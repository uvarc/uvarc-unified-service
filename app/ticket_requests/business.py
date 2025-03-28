from flask import json, jsonify
import pytz
from app import app, jira_service
from common_service_handlers.aws_service_handler import AWSServiceHandler
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

class GeneralSupportRequestManager:
    def process_support_request(self, form_elements_dict, service_host, version):
        jira_service_handler = JiraServiceHandler(app)
        is_rc_project = True
        desc_str = ''
        attrib_to_var = {
              'name': None,
              'email': None,
              'uid': None,
              'category': '',
              'request_title': None,
              'department': '',
              'school': '',
              'discipline': '',
              'discipline-other': '',
              'cost-center': '',
              'components': '',
              'participants': None
        }
        submitted_attribs = list(form_elements_dict)

        for attrib in submitted_attribs:
            if attrib in attrib_to_var:
                attrib_to_var[attrib] = form_elements_dict[attrib]

        desc_str = self.description_with_additional_parameters(desc_str, form_elements_dict)
        project_ticket_route =\
                app.config['JIRA_CATEGORY_PROJECT_ROUTE_DICT'][
                    attrib_to_var['category'].strip().title()]
        if attrib_to_var['request_title'] is not None:
            summary_str = attrib_to_var['request_title']
        else:
            summary_str = '{} Request'.format(attrib_to_var['category'])

        ticket_response = jira_service_handler.create_new_ticket(
            reporter=attrib_to_var['email'] if '@' not in attrib_to_var['email'] else attrib_to_var['email'].split('@')[0],
            participants=attrib_to_var['participants'],
            project_name=project_ticket_route[0],
            request_type=project_ticket_route[1],
            components=attrib_to_var['components'],
            summary=summary_str,
            desc=desc_str,
            department=attrib_to_var['department'],
            school=attrib_to_var['school'],
            discipline=attrib_to_var['discipline'] if attrib_to_var['discipline'] != 'other' else attrib_to_var['discipline-other'],
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

    def update_resource_request_status(self, data):
        aws_service = AWSServiceHandler(app)
        sqs = aws_service.get_resource('sqs')
        queue = sqs.get_queue_by_name(QueueName=app.config['QUEUE_NAME'])
        response = queue.send_message(
         MessageBody=json.dumps(
                        {
                            "ticket_id": data['ticket_id'],
                            "request_type": data['request_type'],
                            "group_name": data['group_name'],
                            "status": data['processing_status']
                        }
                    ))
        return response

    def receive_message(self):
        aws_service = AWSServiceHandler(app)
        sqs = aws_service.get_resource('sqs')
        queue = sqs.get_queue_by_name(QueueName=app.config['QUEUE_NAME'])
        messages = queue.receive_messages(MaxNumberOfMessages=1, WaitTimeSeconds=20, VisibilityTimeout=10)
        if len(messages) > 0:
            for message in messages:
                message_obj = json.loads(message.body)
                print(message_obj)
                # after processing, delete the message from the queue 
                message.delete()
        else:
            message_obj = jsonify({
                'status': 'error',
                'message': 'No messages in the queue.'
            })
        return message_obj
