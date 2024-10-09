from app import app,mongo,public_ldap,eservices_ldap
from datetime import datetime, timezone
import pytz
import requests
import pandas as pd
from deepdiff import DeepDiff

class GetDBInfoBusinessLogic:
    def __init__(self):
        self.correlations = {
                                "AS": "CLAS",
                                "BA": "BATT",
                                "BI": "BII",
                                "DA": "DARD",
                                "DS": "SDS",
                                "ED": "SEHD",
                                "EN": "SEAS",
                                "IT": "ITS",
                                "LW": "LAW",
                                "MC": "COMM",
                                "MD": "SOM",
                                "PV": "PROV/VPR",
                                "RC": "ITS/RC",
                                "RS": "RESEARCH",
                            }
        self.combined_ldap_attributes_list = [
                                        "uid", 
                                        "displayName", 
                                        "title", 
                                        "description", 
                                        "uvaDisplayDepartment",
                                        "department",
                                        "school",
                                        "pwdLastSet",
                                        "userAccountControl",
                                        "primaryGroupID",
                                        "Sponsored",
                                        "Rivanna_Status",
                                        "date_of_query",
                                    ]

    def user_db_call(self,id):
        user = mongo.db.users.find_one({"UserID": id})
        response = None
        if user:
            recent_ldap_info = user["recent_ldap_info"]
            recent_ldap_info = self.__format_dates_for_output(recent_ldap_info)
            recent_ldap_info = self.__school_conversion(recent_ldap_info)
            response = {key: recent_ldap_info[key] for key in recent_ldap_info}
        else:
            response  = {key: "" for key in self.combined_ldap_attributes_list}
            response["uid"] = id
        return response
    
    def user_db_call_with_time(self, id, time):
        user = mongo.db.users.find_one({"UserID": id})

        if user:
            recent_record = None
            # First check recent 
            if user["recent_ldap_info"]["date_of_query"] <= time:
                recent_record = user["recent_ldap_info"]
            # Then check historical 
            if len(user["ldap_info_log"]) > 0:
                if not recent_record:
                    recent_record = user["ldap_info_log"][0]
                for record in user["ldap_info_log"]:
                    if record["date_of_query"] <= time:
                        if record["date_of_query"] > recent_record["date_of_query"]:
                            recent_record = record
            if recent_record:   
                recent_record = self.__school_conversion(recent_record)
                recent_record = self.__format_dates_for_output(recent_record)
                return recent_record
            else:
                recent_ldap_info = user["recent_ldap_info"]
                recent_ldap_info = self.__format_dates_for_output(recent_ldap_info)
                recent_ldap_info = self.__school_conversion(recent_ldap_info)
                return recent_ldap_info
        # default entry
        response  = {key: "" for key in self.combined_ldap_attributes_list}
        response["uid"] = id
        return response
    
    def __school_conversion(self, response):
        prev_school = response["school"]
        if prev_school != "": 
            if self.correlations[prev_school]:
                response["school"] = self.correlations[prev_school]
            else:
                response["school"] = "Other"
        else:
            response["school"] = ""
        return response 


    def __format_dates_for_output(self, response):

        response["date_of_query"] = pytz.utc.localize(response["date_of_query"]).astimezone(pytz.timezone('GMT')).strftime('%a, %d %b %Y %H:%M:%S GMT')

        if response["pwdLastSet"] != "":
                response["pwdLastSet"] = pytz.utc.localize(response["pwdLastSet"]).astimezone(pytz.timezone('GMT')).strftime('%a, %d %b %Y %H:%M:%S GMT')

        return response
    

class LDAPSyncJobBusinessLogic:
    def __init__(self, app):
        self.hpc_url = f"https://{app.config["HPC_HOST"]}/api"
        self.hpc_key = app.config['HPC_CLIENT_SECRET']
        self.combined_ldap_attributes_list = [
                                        "uid", 
                                        "displayName", 
                                        "title", 
                                        "description", 
                                        "uvaDisplayDepartment",
                                        "department",
                                        "school",
                                        "pwdLastSet",
                                        "userAccountControl",
                                        "primaryGroupID",
                                        "Sponsored",
                                        "Rivanna_Status",
                                        "date_of_query",
                                    ]
        

    def get_combined_ldap_info(self, uid):
    
        eservices_entry = eservices_ldap.get_eservices_ldap_info(uid, eservices_ldap.eservices_ldap_conn)
        public_entry = public_ldap.get_public_ldap_info(uid, public_ldap.public_ldap_conn)
        commission_entry =  self.__get_commission(uid)

        if not eservices_entry:
            return None

        complete_ldap_entry = eservices_entry

        if public_entry:
            public_entry[public_entry["uid"]] = public_entry
            complete_ldap_entry.update(public_entry)
        else:
            for public_attribute in public_ldap.public_ldap_attribute_list:
                complete_ldap_entry[public_attribute] = ""
            complete_ldap_entry["uid"] = complete_ldap_entry["sAMAccountName"]


        del complete_ldap_entry["sAMAccountName"]
        del complete_ldap_entry["memberOf"]

        current_timestamp = datetime.now(timezone.utc).replace(microsecond=0)
        complete_ldap_entry["date_of_query"] = current_timestamp.isoformat().replace('+00:00', 'Z')

        if commission_entry:
            commission_entry[commission_entry["name"]] = commission_entry
            complete_ldap_entry.update(commission_entry)
            del complete_ldap_entry["name"]
            complete_ldap_entry["Rivanna_Status"] = complete_ldap_entry["commission"]
            del complete_ldap_entry["commission"]
        else:
            complete_ldap_entry["Rivanna_Status"] =  ""

        restructured_ldap_entry = {}
        # ordering restructure 
        for attr in self.combined_ldap_attributes_list:
            restructured_ldap_entry[attr] = complete_ldap_entry[attr]

        # print("Final entry: ", restructured_ldap_entry)
        return restructured_ldap_entry
    

    def init_db(self):

        # Read CSV File
        df = pd.read_csv("data/ldap_files/all_users_formatted_to_ldap.csv")

        # Only repopulate the database if there are no documents in there currently 
        if mongo.db.users.count_documents({}) == 0:
            # convert to datatime object
            df["date_of_query"] = pd.to_datetime(df["date_of_query"])

            # Convert NaN entries to empty strings
            df = df.fillna('')

            #Insert uid 
            df.insert(loc=0, column="uid", value=df["UserID"])

            # Replace Lastname and Firstname w/ displayName
            df.insert(loc=1, column="displayName", value=(df["Lastname"] + ", " + df["Firstname"] + " (" + df["uid"] + ")"))
            df.drop(columns=["Lastname","Firstname"], inplace=True)

            # Fill out department 
            def extract_department(affiliation):
                if ':' in affiliation:
                    return affiliation.split(':')[1]
                return affiliation
            
            df["department"] = df["affiliation"].apply(extract_department)
            # Create uvaDisplayDepartment attribute [in current ldap info -> might be list] and drop affiliation
            df.insert(loc=4, column="uvaDisplayDepartment", value=(df["affiliation"]))
            df.drop(columns="affiliation", inplace=True)

            

            # Create a dictionary to hold user data
            user_data = {}
            # Create set of names
            uids = set()

            # Iterate over rows
            for index, row in df.iterrows():
                user_id = row["UserID"]
                uids.add(user_id)
                query = row.drop(labels="UserID").to_dict()  # Convert the row to a dictionary and drop 'UserID'
                
                if user_id in user_data:
                    if query["date_of_query"] > user_data[user_id]["recent_ldap_info"]["date_of_query"]:
                        user_data[user_id]["ldap_info_log"].append(user_data[user_id]["recent_ldap_info"])
                        user_data[user_id]["recent_ldap_info"] = query
                    else:
                        user_data[user_id]["ldap_info_log"].append(query)
                else:
                    user_data[user_id] = {"recent_ldap_info": query, "ldap_info_log": []}
            
            # UTC data w/ timestamp
            current_timestamp = datetime.now(timezone.utc)

            # Convert user_data for Mongo Insertion
            records = [{"UserID": user_id, "recent_ldap_info" : queries["recent_ldap_info"], "ldap_info_log": queries["ldap_info_log"],"date_modified": current_timestamp, "comments_on_changes": "Initial Entry"} for user_id, queries in user_data.items()]

            # Insert records into the MongoDB collection
            mongo.db.users.insert_many(records)

            print("Database initialization complete")

            for uid in uids:
                print(uid)
                combined_ldap_entry = self.get_combined_ldap_info(uid)

                user = mongo.db.users.find_one({"UserID": uid})

                if combined_ldap_entry:
                    combined_ldap_entry = self.__format_dates_for_input(combined_ldap_entry)
                    if user:
                        print(combined_ldap_entry)
                        # if no changes, then no dictionary is sent back 
                        changed_fields =  DeepDiff(user["recent_ldap_info"], combined_ldap_entry, exclude_paths="root['date_of_query']")

                        if changed_fields:
                            user["ldap_info_log"].append(user["recent_ldap_info"])
                            user["recent_ldap_info"] = combined_ldap_entry
                            
                            mongo.db.users.update_one(
                                {"UserID": user["UserID"]},  # Filter to find the document
                                {"$set": {
                                    "ldap_info_log": user["ldap_info_log"],
                                    "recent_ldap_info": user["recent_ldap_info"],
                                    "date_modified": user["recent_ldap_info"]["date_of_query"],
                                    "comments_on_changes": changed_fields["values_changed"]
                                }
                                }
                            ) 
                    else:
                        # Should never reach here, but just included as a safety net
                        mongo.db.users.insert_one(
                                    {"UserID": combined_ldap_entry["uid"],
                                        "recent_ldap_info": combined_ldap_entry,
                                        "ldap_info_log": [],
                                        "date_modified": combined_ldap_entry["date_of_query"],
                                        "comments_on_changes": "Initial Entry"
                                    }     
                                )

        else:
            csv_user_id_set = set()

            for index, row in df.iterrows():
                user_id = row["UserID"]
                csv_user_id_set.add(user_id)

            for uid in csv_user_id_set:
                print(uid)
                combined_ldap_entry = self.get_combined_ldap_info(uid)
                user = mongo.db.users.find_one({"UserID": uid})

                if combined_ldap_entry:
                    combined_ldap_entry = self.__format_dates_for_input(combined_ldap_entry)
                    if user:
                        # if no changes, then no dictionary is sent back 
                        changed_fields =  DeepDiff(user["recent_ldap_info"], combined_ldap_entry, exclude_paths="root['date_of_query']", significant_digits=6)

                        if changed_fields:
                            user["ldap_info_log"].append(user["recent_ldap_info"])
                            user["recent_ldap_info"] = combined_ldap_entry
                            
                            mongo.db.users.update_one(
                                {"UserID": user["UserID"]},  # Filter to find the document
                                {"$set": {
                                    "ldap_info_log": user["ldap_info_log"],
                                    "recent_ldap_info": user["recent_ldap_info"],
                                    "date_modified": user["recent_ldap_info"]["date_of_query"],
                                    "comments_on_changes": changed_fields["values_changed"]
                                }
                                }
                            ) 
                    else:
                        # Should never reach here, but just included as a safety net
                        mongo.db.users.insert_one(
                                    {"UserID": combined_ldap_entry["uid"],
                                        "recent_ldap_info": combined_ldap_entry,
                                        "ldap_info_log": [],
                                        "date_modified": combined_ldap_entry["date_of_query"],
                                        "comments_on_changes": "Initial Entry"
                                    }     
                                )
                        

    def __get_commission(self, uid):
        base_url = f"{self.hpc_url}/commission/?userID="
        headers = {
            "Authorization": self.hpc_key,
        }

        if not uid:
            return None 

        commision_entry = None
        url = base_url + uid
        response = requests.get(url, headers=headers)
        data = response.json()

        # Valid Commission info
        if len(data) != 0:
            commision_entry = data[0]

        return commision_entry

    def __format_dates_for_input(self, response):

            response["date_of_query"] = datetime.strptime(response["date_of_query"], '%Y-%m-%dT%H:%M:%SZ')

            if response["pwdLastSet"] != "":
                    response["pwdLastSet"] = datetime.strptime(response["pwdLastSet"], '%Y-%m-%dT%H:%M:%SZ')

            return response

        