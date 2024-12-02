from app import app,jira_service,mongo_service
import pytz
import json


class CreateTicketBusinessLogic:
    def __init__(self):
        # set constant
        self.issue_type_id = "10700"  
        self.project_key = "OH"

    def create_officehour_ticket(self,form_data):

        ldap_helper = UVARCUsersOfficeHoursDataManager()
        ldap_info = ldap_helper.get_user_info(form_data['userID'])
        if not ldap_info:
            return {"error": "LDAP user not found"}, 400
        customer_data = {
            "name": form_data['userID'],
            "email": f"{form_data['userID']}@virginia.edu",
        }

        customer_id = jira_service.get_customer_by_email(customer_data['email'])
        if not customer_id:
            customer_id = jira_service.create_new_customer(customer_data['name'], customer_data['email'])

        reporter = self.__get_reporter_username(customer_id)
        reporter_username = reporter.get("displayName", "")

        return jira_service.create_new_officehour_ticket(reporter_username, form_data, ldap_info)
        #  mapped_details = [{'value': item['value']} for item in form_data['details']]
        # ticket_data = {
        #     "fields": {
        #         "project": {"key": self.project_key},
        #         "reporter": {"name": customer_id},  
        #         "issuetype": {"id": '10700'},  
        #         "description": form_data['comments'],  
        #         "customfield_13184": {"value": form_data['requestType']}, 
        #         "customfield_10972": "Office Hours Request",  
        #         "customfield_13176": ldap_info['department'],  
        #         "customfield_13196": ldap_info['school'],  
        #         "customfield_13175": form_data['date'], 
        #         "customfield_13190": form_data['discipline'],  
        #         "customfield_13194": mapped_details,  
        #         "customfield_13203": {"value": form_data['meetingType']},  
        #         "summary": form_data['summary']  
        #     }
        # }

        # if form_data['staff'][0]['value']:
        #         ticket_data["fields"]["assignee"] = {"name": form_data['staff'][0]['value']}

        # if form_data['computePlatform1'] != "none":
        #         ticket_data["fields"]["customfield_13189"] = {
        #             "value": form_data['computePlatform1'],
        #             "child": {"value": form_data['computePlatform2']}
        #         }

        # if form_data['storagePlatform1'] != "none":
        #     ticket_data["fields"]["customfield_13195"] = {
        #         "value": form_data['storagePlatform1'],
        #         "child": {"value": form_data['storagePlatform2']}
        #     }

    def __get_reporter_username(self, reporter):
        reporter_dict = json.loads(reporter)
        return reporter_dict




class UVARCUsersOfficeHoursDataManager:
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
        user["update_time"] = pytz.utc.localize(user["update_time"]).astimezone(
            pytz.timezone('GMT')).strftime('%a, %d %b %Y %H:%M:%S GMT')
        if user["pwdLastSet"] != "":
            user["pwdLastSet"] = pytz.utc.localize(user["pwdLastSet"]).astimezone(
                pytz.timezone('GMT')).strftime('%a, %d %b %Y %H:%M:%S GMT')

        return user

    def __format_user_info(self, user):
        return self.__school_conversion(
            self.__format_dates_for_output(user)
        )

    def get_user_info(self, uid):
        user = mongo_service.db.uvarc_users.find_one({"uid": uid})
        if user and 'ldap_info_log' in user:
            del user['ldap_info_log']
            del user['_id']
            response = None
            user = self.__format_user_info(user)
            response = {key: user[key] for key in user}
            return response
        else:
            return None

    def get_user_hist_info(self, uid, time):
        user = mongo_service.db.uvarc_users.find_one({"uid": uid})

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
