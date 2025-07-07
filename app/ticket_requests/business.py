from flask import json
from app import app, jira_service
import requests

# from common_service_handlers.aws_service_handler import AWSServiceHandler
from common_service_handlers.jira_service_handler import JiraServiceHandler
from common_utils.business import UVARCUserInfoManager


class UVARCUsersOfficeHoursDataManager:
    def __init__(self):
        # set constant
        self.project_name = "CONSULTATIONS & OUTREACH" 
        self.request_type = "IT_HELP" 

    def create_officehour_ticket(self,form_data):

        ldap_helper = UVARCUserInfoManager()
        ldap_info = ldap_helper.get_user_info(form_data['userID'])
        # if not ldap_info:
        #     return {"error": "LDAP user not found"}, 400
        customer_data = {
            "name": form_data['userID'],
            "email": f"{form_data['userID']}@virginia.edu",
        }

        customer_id = jira_service.get_customer_by_email(customer_data['email'])
        if not customer_id:
            customer_id = jira_service.create_new_customer(customer_data['name'], customer_data['email'])

        reporter = self.__get_reporter_username(customer_id)
        reporter_email = reporter.get("emailAddress", "")
        reporter_username = reporter_email if '@' not in reporter_email else reporter_email.split('@')[0] 
        department = ''
        school = ''
        
        # only set department and school if we received a valid user ID
        # otherwise set reporter to None since that means we don't have a valid userID input
        if ldap_info and ldap_info["department"] and ldap_info["school"]:
            department = ldap_info["department"]
            school = ldap_info["school"]
        else:
            reporter_username = None

        participants = None

        staff_ids = [obj['value'] for obj in form_data['staff'][1:]]  
        if staff_ids:
            participants = staff_ids
          
        response_text = jira_service.create_new_ticket(reporter=reporter_username, project_name=self.project_name, participants=participants, request_type=self.request_type, department=department, school=school, additional_data = form_data)
        if "errorMessage" in response_text:
            # if failed to create ticket, then retry with not valid 
            response_text = jira_service.create_new_ticket(reporter=None, project_name=self.project_name, participants=participants, request_type=self.request_type, department=department, school=school, additional_data = form_data)

        # convert into json to read necessary info
        json_response = json.loads(response_text)
    
        if "errorMessage" not in response_text:
            return True, json_response
        # unable to create ticket, so return false w/ the error message
        return False, json_response
        
    def __get_reporter_username(self, reporter):
        reporter_dict = json.loads(reporter)
        return reporter_dict


class UVARCSupportRequestsManager:
    def create_support_request(self,  request_type, request_info_dict):
        jira_service_handler = JiraServiceHandler(app)
        is_rc_project = True
        desc_str = ''
        attrib_to_var = {
              'name': None,
              'email': None,
              'uid': None,
              'request_title': None,
              'department': '',
              'school': '',
              'discipline': '',
              'discipline-other': '',
              'cost-center': '',
              'components': '',
              'participants': None
        }
        submitted_attribs = list(request_info_dict)

        for attrib in submitted_attribs:
            if attrib in attrib_to_var:
                attrib_to_var[attrib] = request_info_dict[attrib]

        desc_str = self.description_with_additional_parameters(desc_str, request_info_dict)
        project_ticket_route =\
                app.config['JIRA_CATEGORY_PROJECT_ROUTE_DICT'][
                    request_type]
        if attrib_to_var['request_title'] is not None:
            summary_str = attrib_to_var['request_title']
        else:
            summary_str = '{} Request'.format(request_type)

        try:
            jira_service_handler.create_new_customer(
                name=request_info_dict['uid'],
                email='{}@virginia.edu'.format(request_info_dict['uid'])
            )
        except Exception as ex:
            app.log_exception(ex)
            print(ex)
        if 'resource_requestor_uid' in request_info_dict and request_info_dict['resource_requestor_uid'] is not None and request_info_dict['resource_requestor_uid'] != '':
            try:
                jira_service_handler.create_new_customer(
                    name=request_info_dict['resource_requestor_uid'],
                    email='{}@virginia.edu'.format(request_info_dict['resource_requestor_uid'])
                )
            except Exception as ex:
                app.log_exception(ex)
                print(ex)

        ticket_response = jira_service_handler.create_new_ticket(
            reporter=request_info_dict['uid'],
            participants=request_info_dict['resource_requestor_uid'] if 'resource_requestor_uid' in request_info_dict and request_info_dict['resource_requestor_uid'] is not None and request_info_dict['resource_requestor_uid'] != '' and request_info_dict['uid'] != request_info_dict['resource_requestor_uid'] else None,
            project_name=project_ticket_route[0],
            request_type=project_ticket_route[1],
            components=attrib_to_var['components'],
            summary=summary_str,
            desc=desc_str,
            department=attrib_to_var['department'],
            school=attrib_to_var['school'],
            discipline=attrib_to_var['discipline'],
            is_rc_project=is_rc_project
        )

        app.logger.info(ticket_response)
        print('Ticket Response: ' + str(ticket_response))
        return ticket_response

    def description_with_additional_parameters(self, desc_str, form_elements_dict):
        excluded_keys = {'department', 'school', 'discipline', 'discipline-other'}
        for key, value in form_elements_dict.items():
            if key not in excluded_keys:
                desc_str = ''.join([desc_str, '{}: {}\n'.format(
                    key, value)])
        return desc_str
