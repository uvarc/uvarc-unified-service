from app import app,jira_service
import json
from common_utils.business import UVARCUserInfoManager


class UVARCUsersOfficeHoursDataManager:
    def __init__(self):
        # set constant
        self.project_name = "CONSULTATIONS & OUTREACH" 
        self.request_type = "IT_HELP" 

    def create_officehour_ticket(self,form_data):

        ldap_helper = UVARCUserInfoManager()
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

        return jira_service.create_new_ticket(reporter=reporter_username, project_name=self.project_name, request_type=self.request_type, department=ldap_info["department"], school=ldap_info["school"], additional_data = form_data)
        
    def __get_reporter_username(self, reporter):
        reporter_dict = json.loads(reporter)
        return reporter_dict




