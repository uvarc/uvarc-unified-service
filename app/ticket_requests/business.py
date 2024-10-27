#from app import jira_service
from app.ldap_requests.business import GetDBInfoBusinessLogic
from common_service_handlers.jira_service_handler import JiraServiceHandler
from datetime import datetime

class CreateTicketBussinessLogic:
    def __init__(self):
        # set constant
        self.issue_type_id = "10700"  
        self.project_key = "OH"

    def create_officehour_ticket(self,form_data):

        ldap_helper = GetDBInfoBusinessLogic()
        ldap_info = ldap_helper.user_db_call(form_data['userID'])
        if not ldap_info:
            return {"error": "LDAP user not found"}, 400
        #print(ldap_info)

        jira_handler = JiraServiceHandler()
        customer_data = {
            "name": form_data['userID'],
            "email": f"{form_data['userID']}@virginia.edu",
        }

        customer_id = jira_handler.get_customer_by_email(customer_data['email'])

        if not customer_id:
            customer_id = jira_handler.create_new_customer(customer_data['name'], customer_data['email'])



        mapped_details = [{'value': item['value']} for item in form_data['details']]

        ticket_data = {
            "fields": {
                "project": {"key": self.project_key},
                "reporter": {"name": customer_id},  
                "issuetype": {"id": '10700'},  
                "description": form_data['comments'],  
                "customfield_13184": {"value": form_data['requestType']}, 
                "customfield_10972": "Office Hours Request",  
                "customfield_13176": ldap_info['department'],  
                "customfield_13196": ldap_info['school'],  
                "customfield_13175": form_data['date'], 
                "customfield_13190": form_data['discipline'],  
                "customfield_13194": mapped_details,  
                "customfield_13203": {"value": form_data['meetingType']},  
                "summary": form_data['summary']  
            }
        }

        if form_data['staff'][0]['value']:
                ticket_data["fields"]["assignee"] = {"name": form_data['staff'][0]['value']}

        if form_data['computePlatform1'] != "none":
                ticket_data["fields"]["customfield_13189"] = {
                    "value": form_data['computePlatform1'],
                    "child": {"value": form_data['computePlatform2']}
                }

        if form_data['storagePlatform1'] != "none":
            ticket_data["fields"]["customfield_13195"] = {
                "value": form_data['storagePlatform1'],
                "child": {"value": form_data['storagePlatform2']}
            }

        

        ## New method
        # jira_response=jira_handler.create_new_officehour_ticket(customer_id,form_data,ldap_info):
        #     return jira_response, 200
