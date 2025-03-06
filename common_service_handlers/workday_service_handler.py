import json
import requests


class WorkdayServiceHandler:
    def __init__(self, app):
        self._connect_host_url, self._auth = self.__get_workday_host_info(
            app)

    def __get_workday_host_info(self, app):
        return [
            'https://{}:{}/ws/rest/'.format(app.config['WORKDAY_CONN_INFO']['HOST'],
                                            app.config['WORKDAY_CONN_INFO']['PORT']),
            app.config['WORKDAY_CONN_INFO']['PASSWORD']
        ]

    def validate_fdm(self, fdm_dict):
        try:
            headers = {
                "x-api-key": self._auth,
            }
            payload = json.dumps(
                {
                    "P_Taggable_Type": "ACCOUNTING_JOURNAL",
                    "P_Company_ID": fdm_dict['company'],
                    "P_CostCenter": fdm_dict['cost_center'],
                    "P_Business_Unit": fdm_dict['business_unit'],
                    "P_Fund": fdm_dict['fund'],
                    "P_Grant": fdm_dict['grant'],
                    "P_Gift": fdm_dict['gift'],
                    "P_Internal_Reference": '',
                    "P_Program": fdm_dict['program'],
                    "P_Project": fdm_dict['project'],
                    "P_Revenue_Category": '',
                    "P_Spend_Category": '',
                    "P_Loan": '',
                    "P_Location": '',
                    "P_Designated": fdm_dict['designated'],
                    "P_Function": fdm_dict['function'],
                    "P_Activity": fdm_dict['activity'],
                    "P_Assignee": fdm_dict['assignee'],
                    "P_Transaction_Date": ''
                }
            )
            r = requests.post(
                ''.join([self._connect_host_url, 'workdayfdm/FDMValidator']),
                headers=headers,
                data=payload,
            )
            return r.text
        except Exception as ex:
            print("Couldn't validate FDM {} info provided: {}".format(fdm_dict, str(ex)))
            raise ex
