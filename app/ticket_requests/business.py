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
          
        response_text = jira_service.create_new_ticket(reporter=reporter_username, project_name=self.project_name, request_type=self.request_type, department=department, school=school, additional_data = form_data)
        if "errorMessage" in response_text:
            # if failed to create ticket, then retry with not valid 
            response_text = jira_service.create_new_ticket(reporter=None, project_name=self.project_name, request_type=self.request_type, department=department, school=school, additional_data = form_data)


        # headers for requests
        headers = {'content-type': 'application/json'}

        # convert into json to read necessary info
        json_response = json.loads(response_text)
    
        if "errorMessage" not in response_text:
                jira_issue_key = json_response.get('issueKey')
                staff_ids = [obj['value'] for obj in form_data['staff'][1:]]  
                if staff_ids:
                    servicedesk_res = jira_service.add_participants(jira_issue_key=jira_issue_key, id_list=staff_ids)
                    if "errorMessage" in servicedesk_res:
                        return False, servicedesk_res
                
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

        ticket_response = jira_service_handler.create_new_ticket(
            reporter=request_info_dict['uid'],
            participants=attrib_to_var['participants'],
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


    # def set_queue_message(self, data):
    #     aws_service = AWSServiceHandler(app)
    #     sqs = aws_service.get_resource('sqs')
    #     queue = sqs.get_queue_by_name(QueueName=app.config['QUEUE_NAME'])
    #     response = queue.send_message(
    #             MessageBody=json.dumps(
    #                     {
    #                       'group_name': data['group_name'],
    #                       'resource_request_type': data['resource_request_type'],
    #                       'resource_request_id': data['resource_request_id'],
    #                       'status': data['status']
    #                     }
    #                 ))
    #     print(response)
    #     return response

    # def receive_message(self):
    #     try:
    #         aws_service = AWSServiceHandler(app)
    #         sqs = aws_service.get_resource('sqs')
    #         queue = sqs.get_queue_by_name(QueueName=app.config['QUEUE_NAME'])
    #         messages = queue.receive_messages(MaxNumberOfMessages=1, WaitTimeSeconds=20, VisibilityTimeout=10)
    #         if len(messages) > 0:
    #             for message in messages:
    #                 message_obj = json.loads(message.body)
    #                 if message_obj.get('status') == 'pending':
    #                     #mocking data
    #                     form_data = {'email': 'cyj7aj@virginia.edu', 'name': 'raji', 'uid': 'cyj7aj', 'category': 'Storage',
    #                            'department': '', 'cost-center': 'CC1260', 'company_id': 'UVA_207', 'business_unit': 'BU01',
    #                            'fund': 'FD068', 'grant': '', 'gift': '', 'program': '', 'project': 'PJ02322', 'designated': '',
    #                            'function': 'FN009', 'activity': '', 'assignee':'988443044', 'components': '', 'participants': None}
    #                     message_obj.update(form_data)
    #                     response = json.loads(self.process_support_request(message_obj))
    #                     if response['issueKey']:
    #                          # after creating ticket, delete the message from the queue 
    #                         message.delete()
    #                         return make_response(jsonify({"ticket_id": response['issueKey']}), 201)
    #                     else:
    #                         return make_response(jsonify({"error": "Failed to create Jira ticket."}), 500)
    #                 else:
    #                     print(message)
    #         else:
    #             message_obj = {
    #                 'status': 'error',
    #                 'message': 'No messages available in the queue.'
    #              }
    #             return message_obj
             
    #     except Exception as e:
    #         print(f"Unexpected error: {str(e)}")
    #         return make_response(jsonify({"error": "An unexpected error occurred."}), 500)
