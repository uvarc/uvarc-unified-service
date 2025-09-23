from app import mongo_service
import pytz
from datetime import datetime

class UVARCUserInfoManager:
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
        if "date_of_query" in user and isinstance(user["date_of_query"], str):
            user["date_of_query"] = datetime.strptime(user["date_of_query"], '%Y-%m-%dT%H:%M:%SZ')
        if "update_time" in user and isinstance(user["update_time"], str):
            user["update_time"] = datetime.strptime(user["update_time"], '%Y-%m-%dT%H:%M:%SZ')
        if "pwdLastSet" in user and isinstance(user["pwdLastSet"], str):
            user["pwdLastSet"] = datetime.strptime(user["pwdLastSet"], '%Y-%m-%dT%H:%M:%SZ')
        
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
