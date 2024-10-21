from datetime import datetime, timezone
import pytz
import requests
import pandas as pd
from deepdiff import DeepDiff
from app import app, mongo_service
from common_service_handlers.ldap_service_handler import PrivateLDAPServiceHandler, PublicLDAPServiceHandler

from common_utils import synchronized


class UVARCUsersDataManager:
    def __init__(self):
        self.__correlations = {
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

    def __school_conversion(self, user):
        prev_school = user["school"]
        if prev_school != "":
            if self.__correlations[prev_school]:
                user["school"] = self.__correlations[prev_school]
            else:
                user["school"] = "Other"
        else:
            user["school"] = ""
        return user

    def __format_dates_for_output(self, user):

        user["date_of_query"] = pytz.utc.localize(user["date_of_query"]).astimezone(
            pytz.timezone('GMT')).strftime('%a, %d %b %Y %H:%M:%S GMT')

        if user["pwdLastSet"] != "":
            user["pwdLastSet"] = pytz.utc.localize(user["pwdLastSet"]).astimezone(
                pytz.timezone('GMT')).strftime('%a, %d %b %Y %H:%M:%S GMT')

        return user

    def __format_user_info(self, user):
        return self.__school_conversion(
            self.__format_dates_for_output(user)
        )

    def get_user_info(self, id):
        user = mongo_service.db.uvarc_users.find_one({"UserID": id})
        del user['ldap_info_log']
        response = None
        if user:
            user = self.__format_user_info(user)
            response = {key: user[key] for key in user}
            return response
        else:
            return None

    def get_user_hist_info(self, id, time):
        user = mongo_service.db.uvarc_users.find_one({"UserID": id})

        if user:
            recent_record = None
            # First check recent
            if user["date_of_query"] <= time:
                recent_record = user
            # Then check historical
            if 'ldap_info_log' in user and len(user["ldap_info_log"]) > 0:
                if not recent_record:
                    recent_record = user["ldap_info_log"][0]
                for record in user["ldap_info_log"]:
                    if record["date_of_query"] <= time:
                        if record["date_of_query"] > recent_record["date_of_query"]:
                            recent_record = record
            if recent_record:
                return self.__format_user_info(recent_record)
            else:
                return self.__format_user_info(user)
        else:
            return None


class UVARCUsersSyncManager:
    def __init__(self):
        self.__private_ldap_service_handler = None
        self.__public_ldap_service_handler = None
        self.__private_ldap_service_handler = PrivateLDAPServiceHandler(
            app)
        self.__public_ldap_service_handler = PublicLDAPServiceHandler(app)
        self.hpc_url = f"https://{app.config["HPC_HOST"]}/api"
        self.hpc_key = app.config['HPC_CLIENT_SECRET']
        self.__combined_ldap_attributes_list = [
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

    def __del__(self):
        self.close()

    def close(self):
        if self.__private_ldap_service_handler:
            self.__private_ldap_service_handler.close()
            self.__private_ldap_service_handler = None
        if self.__public_ldap_service_handler:
            self.__public_ldap_service_handler.close()
            self.__public_ldap_service_handler = None

    def __get_commission(self, uid):
        base_url = f"{self.hpc_url}/commission/?userID={uid}"
        headers = {
            "Authorization": self.hpc_key,
        }

        if not uid:
            return None

        commision_entry = None
        # url = base_url + uid
        try:
            response = requests.get(base_url, headers=headers)
            data = response.json()
        except Exception as ex:
            app.logger.error(ex)
            return None
        # Valid Commission info
        if len(data) != 0:
            commision_entry = data[0]

        return commision_entry

    def __format_dates_for_input(self, response):

        response["date_of_query"] = datetime.strptime(
            response["date_of_query"], '%Y-%m-%dT%H:%M:%SZ')

        if response["pwdLastSet"] != "":
            response["pwdLastSet"] = datetime.strptime(
                response["pwdLastSet"], '%Y-%m-%dT%H:%M:%SZ')

        return response

    def fetch_user_all_info(self, uid):
        eservices_entry = self.__private_ldap_service_handler.get_private_ldap_info(
            uid)
        public_entry = self.__public_ldap_service_handler.get_public_ldap_info(
            uid)
        commission_entry = self.__get_commission(uid)

        if not eservices_entry:
            return None

        complete_ldap_entry = eservices_entry

        if public_entry:
            public_entry[public_entry["uid"]] = public_entry
            complete_ldap_entry.update(public_entry)
        else:
            for public_attribute in self.__public_ldap_service_handler.get_public_ldap_query_attribute_list():
                complete_ldap_entry[public_attribute] = ""
            complete_ldap_entry["uid"] = complete_ldap_entry["sAMAccountName"]
        # app.logger.info(complete_ldap_entry["memberOf"])
        # app.logger.info(complete_ldap_entry["uvaIsOwnerOf"])
        del complete_ldap_entry["sAMAccountName"]
        del complete_ldap_entry["memberOf"]
        # del complete_ldap_entry["uvaIsOwnerOf"]

        # current_timestamp = datetime.now(timezone.utc).replace(microsecond=0)
        complete_ldap_entry["date_of_query"] = datetime.now(
            timezone.utc).replace(
                microsecond=0).isoformat().replace(
                    '+00:00', 'Z')

        if commission_entry:
            commission_entry[commission_entry["name"]] = commission_entry
            complete_ldap_entry.update(commission_entry)
            del complete_ldap_entry["name"]
            complete_ldap_entry["Rivanna_Status"] = complete_ldap_entry["commission"]
            del complete_ldap_entry["commission"]
        else:
            complete_ldap_entry["Rivanna_Status"] = ""

        restructured_ldap_entry = {}
        # ordering restructure
        for attr in self.__combined_ldap_attributes_list:
            restructured_ldap_entry[attr] = complete_ldap_entry[attr]

        # print("Final entry: ", restructured_ldap_entry)

        return restructured_ldap_entry

    def __build_user_info(self, user_info_dict, user_hist_info_dict, comment):
        user_info_dict["ldap_info_log"] = user_hist_info_dict
        user_info_dict["date_modified"] = datetime.now(timezone.utc)
        user_info_dict["comment"] = comment
        return user_info_dict

    @synchronized
    def backfill_users_hist_info(self):
        # Read CSV File
        backfill_users_hist_info = pd.read_csv("data/backfill/users_info.csv")

        # Only repopulate the database if there are no documents in there currently
        if mongo_service.db.uvarc_users.count_documents({}) == 0:
            # convert to datatime object
            backfill_users_hist_info["date_of_query"] = pd.to_datetime(
                backfill_users_hist_info["date_of_query"])

            # Convert NaN entries to empty strings
            backfill_users_hist_info = backfill_users_hist_info.fillna('')

            # Insert uid
            backfill_users_hist_info.insert(
                loc=0, column="uid", value=backfill_users_hist_info["UserID"])

            # Replace Lastname and Firstname w/ displayName
            backfill_users_hist_info.insert(loc=1, column="displayName", value=(
                backfill_users_hist_info["Lastname"] + ", " + backfill_users_hist_info["Firstname"] + " (" + backfill_users_hist_info["uid"] + ")"))
            backfill_users_hist_info.drop(
                columns=["Lastname", "Firstname"], inplace=True)

            # Fill out department
            def extract_department(affiliation):
                if ':' in affiliation:
                    return affiliation.split(':')[1]
                return affiliation

            backfill_users_hist_info["department"] = backfill_users_hist_info["affiliation"].apply(
                extract_department)
            # Create uvaDisplayDepartment attribute [in current ldap info -> might be list] and drop affiliation
            backfill_users_hist_info.insert(loc=4, column="uvaDisplayDepartment",
                                            value=(backfill_users_hist_info["affiliation"]))
            backfill_users_hist_info.drop(columns="affiliation", inplace=True)

            # Create a dictionary to hold user data
            user_data = {}
            # Create set of names
            uids = set()

            # Iterate over rows
            for index, backfill_user_hist_info in backfill_users_hist_info.iterrows():
                user_id = backfill_user_hist_info["UserID"]
                uids.add(user_id)
                # Convert the row to a dictionary and drop 'UserID'
                query = backfill_user_hist_info.drop(labels="UserID").to_dict()

                if user_id in user_data:
                    if query["date_of_query"] > user_data[user_id]["recent_ldap_info"]["date_of_query"]:
                        user_data[user_id]["ldap_info_log"].append(
                            user_data[user_id]["recent_ldap_info"])
                        user_data[user_id]["recent_ldap_info"] = query
                    else:
                        user_data[user_id]["ldap_info_log"].append(query)
                else:
                    user_data[user_id] = {
                        "recent_ldap_info": query, "ldap_info_log": []}

            backfill_users_info = []
            # Convert user_data for mongo_service. Insertion
            for user_id, queries in user_data.items():
                backfill_users_info.append(
                    self.__build_user_info(
                        user_info_dict=queries["recent_ldap_info"],
                        user_hist_info_dict=queries["ldap_info_log"],
                        comment="backfilled data"
                    )
                )

            # Insert records into the mongo_service.DB collection
            mongo_service.db.uvarc_users.insert_many(backfill_users_info)

    def create_user_info(self, user):
        pass

    @synchronized
    def sync_users_info(self):

        for user in mongo_service.db.uvarc_users.find({}):
            self.sync_user_info(user)

    def sync_user_info(self, user):
        combined_ldap_entry = self.fetch_user_all_info(user['uid'])

        if combined_ldap_entry:
            combined_ldap_entry = self.__format_dates_for_input(
                combined_ldap_entry)
            if user:
                # if no changes, then no dictionary is sent back
                date_modified_current = user["date_modified"]
                comment_current = user["comment"]
                del user["date_modified"]
                del user["comment"]

                changed_fields = DeepDiff(
                    user, combined_ldap_entry, exclude_paths="root['date_of_query']")

                user["date_modified"] = date_modified_current
                user["comment"] = comment_current
                if changed_fields and 'values_changed' in changed_fields:
                    app.logger.info('User info changes detected: {}'.format(changed_fields))
                    user_ldap_info_log = []
                    if 'ldap_info_log' in user:
                        user_ldap_info_log = user["ldap_info_log"]
                        del user["ldap_info_log"]
                    if '_id' in user:
                        del user['_id']
                    user_ldap_info_log.append(user)
                    user = combined_ldap_entry

                    mongo_service.db.uvarc_users.update_one(
                        # Filter to find the document
                        {"uid": user['uid']}, {
                            "$set": self.__build_user_info(
                                user_info_dict=user,
                                user_hist_info_dict=user_ldap_info_log,
                                comment=changed_fields["values_changed"]
                            )
                        }
                    )
