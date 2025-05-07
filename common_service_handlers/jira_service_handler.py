import json
import requests
from flask import jsonify, make_response


class JiraServiceHandler:
    def __init__(self, app):
        self._connect_host_url, self._auth = self.__get_jira_host_info(
            app)
        self._default_reporter = app.config['JIRA_CONN_INFO']['CLIENT_ID']
        self._project_info_lookup_dict = app.config['JIRA_PROJECT_INFO_LOOKUP']
        self._project_request_type_lookup_dict =\
            app.config['JIRA_PROJECT_REQUEST_TYPE_LOOKUP']
        self._customfield = app.config['CUSTOMFIELD_VALUES']
        self._project_custom_fields_dict = app.config['JIRA_CUSTOM_FIELDS']

    def __get_jira_host_info(self, app):
        return [
            'https://{}:{}/rest/'.format(app.config['JIRA_CONN_INFO']['HOST'],
                                            app.config['JIRA_CONN_INFO']['PORT']),
            (app.config['JIRA_CONN_INFO']['CLIENT_ID'],
                app.config['JIRA_CONN_INFO']['PASSWORD'])
        ]

    def __get_jira_ticket_route_ids(self, project_name, request_type):
        try:
            if(project_name.upper() in self._project_info_lookup_dict
               and request_type.upper() in self._project_request_type_lookup_dict):
                return (
                    self._project_info_lookup_dict[project_name.upper(
                    )],
                    self._project_request_type_lookup_dict[request_type.upper(
                    )]
                )

            headers = {
                "Content-Type": "application/json"}
            r = requests.get(
                ''.join([self._connect_host_url,
                         'servicedeskapi/servicedesk']),
                headers=headers,
                auth=self._auth
            )
            project_meta_info = json.loads((r.content).decode("utf-8"))

            for i in range(0, project_meta_info['size']):
                if(project_meta_info['values'][i]['projectName'].upper() == project_name.upper()):
                    headers = {
                        "Content-Type": "application/json"}
                    r = requests.get(
                        ''.join([self._connect_host_url,
                                 'servicedeskapi/servicedesk/{}/requesttype'.format(project_meta_info['values'][i]['id'])]),
                        headers=headers,
                        auth=self._auth
                    )
                    request_typ_meta_info = json.loads(
                        (r.content).decode("utf-8"))

                    for ri in range(0, request_typ_meta_info['size']):
                        if(request_typ_meta_info['values'][ri]['name'].upper() == request_type.upper()):
                            return (project_meta_info['values'][i]['id'], request_typ_meta_info['values'][ri]['id'])

            raise Exception(
                'Cannot find JIRA route to create ticket for project/request type {}/{}'.format(project_name, request_type))
        except Exception as ex:
            print(str(ex))
            raise ex

    def create_new_customer(self, name, email):
        try:
            headers = {
                "Content-Type": "application/json",
                "X-ExperimentalApi": "opt-in"
            }
            payload = json.dumps(
                {
                    "email": email,
                    "fullName": name
                }
            )
            r = requests.post(
                ''.join([self._connect_host_url, 'servicedeskapi/customer']),
                headers=headers,
                data=payload,
                auth=self._auth
            )
            return r.text
        except Exception as ex:
            print("Couldn't create customer {} in JIRA: {}".format(name, str(ex)))

    def get_customer(self, account_id):
        try:
            headers = {
                "Content-Type": "application/json",
                "X-ExperimentalApi": "opt-in"
            }

            r = requests.get(
                ''.join([self._connect_host_url, 'api/2/user?accountId='+account_id]),
                headers=headers,
                auth=self._auth
            )
            return r.text
        except Exception as ex:
            print("Couldn't get customer {} in JIRA: {}".format(account_id, str(ex)))

    def get_customer_by_email(self,email):
        try:
            headers={
                "Content-Type": "application/json",
                "X-ExperimentalApi": "opt-in"

            }
            r = requests.get(
                ''.join([self._connect_host_url, 'api/2/user?username='+email]),
                headers=headers,
                auth=self._auth
            )

            # Check if the response status code indicates an error
            if r.status_code != 200:
                print(f"Error fetching customer {email}: {r.status_code} - {r.text}")
                return None
            return r.text
        except Exception as ex:
            print("Couldn't get customer {} in JIRA: {}".format(email, str(ex)))

    def create_new_ticket(
        self,
        reporter=None,
        participants=None,
        project_name='GENERAL_SUPPORT',
        request_type='GENERAL_SUPPORT_GET_IT_HELP',
        components=None,
        summary=None,
        desc=None,
        department='',
        school='',
        discipline='',
        is_rc_project=False,
        additional_data = None
    ):
        is_office_hours = False

        if project_name == "CONSULTATIONS & OUTREACH":
            is_office_hours = True

        custom_fields_dict = self._project_custom_fields_dict
        
        if reporter is None:
            reporter = self._default_reporter
        # if(participants is None):
        #     participants = [reporter]
        headers = {'content-type': 'application/json'}
        jira_ticket_route_info = self.__get_jira_ticket_route_ids(
            project_name, request_type)
        payload = {
            "serviceDeskId": jira_ticket_route_info[0],
            "requestTypeId": jira_ticket_route_info[1],
            "requestFieldValues": {
                "summary": summary,
                "description": desc
            },
            "requestParticipants": participants,
            "raiseOnBehalfOf": reporter,
        }

        if is_rc_project and (department != '' or school != ''):
            payload["requestFieldValues"][self._customfield[0]] = department
            payload["requestFieldValues"][self._customfield[1]] = school
        if is_rc_project and discipline != '':
            payload["requestFieldValues"][self._customfield[2]] = discipline

        if is_office_hours and (department!='' or school!=''):
            payload["requestFieldValues"][custom_fields_dict["custom_field_department"]] = department
            payload["requestFieldValues"][custom_fields_dict["custom_field_school"]] = school
        if (is_rc_project or is_office_hours) and discipline != '':
            payload["requestFieldValues"][custom_fields_dict["custom_field_discipline"]] = discipline

        # Required changes from office hours once I get right Request Type
        if is_office_hours and additional_data:
            mapped_details = [{'value': item['value']} for item in additional_data['details']]
            payload["requestFieldValues"]["description"] = (
                f"Requested by: {additional_data['userID']}\n{additional_data['comments']}"
            )   
            payload["requestFieldValues"]["summary"] = additional_data["summary"]
            payload["requestFieldValues"][custom_fields_dict["custom_field_request_type"]] = {"value": additional_data['requestType']}
            payload["requestFieldValues"][custom_fields_dict["custom_field_date"]] = additional_data["date"]
            payload["requestFieldValues"][custom_fields_dict["custom_field_details"]] = mapped_details
            payload["requestFieldValues"][custom_fields_dict["custom_field_meeting_type"]] = {"value": additional_data['meetingType']}

            if additional_data['staff'][0]['value']:
                payload["requestFieldValues"]["assignee"] = {"name": additional_data['staff'][0]['value']}

            if additional_data['computePlatform1'] != "none":
                payload["requestFieldValues"][custom_fields_dict["custom_field_compute_platform"]]= {
                    "value": additional_data['computePlatform1'],
                    "child": {"value": additional_data['computePlatform2']}
                }

            if additional_data['storagePlatform1'] != "none":
                payload["requestFieldValues"][custom_fields_dict["custom_field_storage_platform"]] = {
                    "value": additional_data['storagePlatform1'],
                    "child": {"value": additional_data['storagePlatform2']}
                }


        if components:
            payload["requestFieldValues"]["components"] = []
            for component in components.split(";"):
                if component.lstrip() != '':
                    payload["requestFieldValues"]["components"].append(
                        {"name": component})
        response = requests.post(
            ''.join([self._connect_host_url, 'servicedeskapi/request']),
            headers=headers,
            data=json.dumps(payload),
            auth=self._auth
        )

        return response.text

    def add_ticket_comment(self, ticket_id, comment):
        headers = {
            "Content-Type": "application/json",
        }

        payload = json.dumps(
            {
                "body": comment,
                "public": False
            }
        )
        response = requests.post(
            ''.join([self._connect_host_url,
                     'servicedeskapi/request/{issueIdOrKey}/comment'.replace('{issueIdOrKey}', ticket_id)]),
            headers=headers,
            data=payload,
            auth=self._auth
        )
        return response.text

    def get_all_tickets_by_customer(self, reporter):
        try:
            headers = {
                "Content-Type": "application/json",
                "X-ExperimentalApi": "opt-in"
            }
            r = requests.get(
                ''.join([self._connect_host_url,
                         "api/3/search?jql=reporter%20%3D%20\"{}\"+order+by+created"]).format(reporter),
                headers=headers,
                auth=self._auth
            )
            requests_info = json.loads((r.content).decode("utf-8"))
            response_data = ()
            for request in requests_info['issues']:
                try:
                    description = ''
                    if request['fields'].get('description'):
                        for content in request['fields'].get('description')['content'][0]['content']:
                            if content['type'] == 'text' and content['text'].startswith('Description: '):
                                description = content['text']
                except Exception as ex:
                    pass
                try:
                    request_type = ''
                    request_type_icon_link = ''
                    request_link = ''

                    if 'customfield_10001' in request['fields']:
                        if 'requestType' in request['fields']['customfield_10001']:
                            request_type = request['fields']['customfield_10001']['requestType']['name']
                            request_type_icon_link = request['fields']['customfield_10001'][
                                'requestType']['icon']['_links']['iconUrls']['24x24']
                        if '_links' in request['fields']['customfield_10001']:
                            request_link = request['fields']['customfield_10001']['_links']['web']
                except Exception as ex:
                    pass
                try:
                    response_data = response_data + (
                        {
                            'reference_id': request['key'],
                            'status': request['fields']['status']['name'],
                            'project_name': request['fields']['project']['name'],
                            'request_type': request_type,
                            'summary': request['fields']['summary'],
                            'create_date': request['fields']['created'],
                            'description': description,
                            'request_link': request_link,
                            'request_type_icon_link': request_type_icon_link
                        },
                    )
                except Exception as ex:
                    pass
            return response_data
        except Exception as ex:
            print("Couldn't fetch tickets for customer {} from JIRA: {}".format(
                reporter, str(ex)))
