from datetime import datetime
from flask import json, jsonify
import pytz
from app import app, mongo_service
from common_service_handlers.aws_service_handler import AWSServiceHandler
from common_service_handlers.jira_service_handler import JiraServiceHandler


class UVARCUsersOfficeHoursDataManager:
    def __init__(self, uid):
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
                            "status": data['status'],
                            "resource_request_id": data['resource_request_id'],
                            'creation_timestamp': datetime.now().strftime("%A, %B %d, %Y - %H:%M:%S")
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
        
