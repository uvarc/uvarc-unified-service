import json
import bson
import bson.json_util
from datetime import datetime, timezone

import requests
from app import app, mongo_service
from app.core.business import UVARCUsersDataManager, UVARCGroupsDataManager
from common_service_handlers.workday_service_handler import WorkdayServiceHandler
from common_utils import RESOURCE_REQUESTS_SERVICE_UNITS_TIERS, RESOURCE_REQUESTS_STORAGE_TIERS, RESOURCE_REQUESTS_ADMINS_INFO, RESOURCE_TYPES


class UVARCAdminFormInfoDataManager():
    def __init__(self, group_name):
        self.__group_name = group_name

    def get_group_admin_info(self):
        self.__uvarc_group_data_manager = UVARCGroupsDataManager(self.__group_name, upsert=True, refresh=True)
        group_info_db = self.__uvarc_group_data_manager.get_group_info()
        return {
            "is_owner_set": True if 'pi_uid' in group_info_db and group_info_db['pi_uid'] != None and group_info_db['pi_uid'].strip() != '' else False,
            "owner_uid": group_info_db['pi_uid'] if 'pi_uid' in group_info_db and group_info_db['pi_uid'] is not None and group_info_db['pi_uid'].strip() != '' else ''
        }

    def set_group_admin_info(self, owner_uid):
        self.__uvarc_group_data_manager = UVARCGroupsDataManager(self.__group_name, upsert=True, refresh=True)
        group_info_db = self.__uvarc_group_data_manager.get_group_info()
        if 'pi_uid' in group_info_db and group_info_db['pi_uid'] is not None and group_info_db['pi_uid'].strip() != '':
            raise Exception('Cannot process set group owner request: The group owner has already been claimed')

        if UVARCResourcRequestFormInfoDataManager(owner_uid).get_user_resource_request_info()['is_user_resource_request_elligible'] is False:
            raise Exception('Cannot process set group owner request: The user {} is not elligible to request research resource {}'.format(owner_uid))

        if self.__group_name not in UVARCUsersDataManager(uid=owner_uid, upsert=True, refresh=True).get_user_groups_info():
            raise Exception('Cannot process set group owner request: The {} is not part of grouper/mygrops {}'.format(owner_uid, self.__group_name))

        group_info_db['pi_uid'] = owner_uid
        self.__uvarc_group_data_manager.set_group_info(
            group_info_db
        )


class UVARCResourcRequestFormInfoDataManager():
    def __init__(self, uid):
        self.__uid = uid

    def get_user_resource_request_info(self):
        self.__uvarc_user_data_manager = UVARCUsersDataManager(uid=self.__uid, upsert=True, refresh=True)    

        return {
            'is_user_resource_request_elligible': True if self.__uid in RESOURCE_REQUESTS_ADMINS_INFO else self.__uvarc_user_data_manager.is_user_resource_request_elligible(),
            'user_groups': self.__uvarc_user_data_manager.get_owner_groups_info(),
            'user_resources': self.__transfer_db_data_to_user_resource_request_info(list(self.__uvarc_user_data_manager.get_user_resources_info()))
        }

    def __transfer_db_data_to_user_resource_request_info(self, user_resources_info):
        for user_resource_info in user_resources_info:
            user_resource_info.pop('_id')
            user_resource_info.pop('group_members')
            user_resource_info.pop('group_members_hist')
            user_resource_info.pop('group_members_update_time')
            for resource_type in RESOURCE_TYPES:
                if 'resources' in user_resource_info and resource_type in user_resource_info['resources']:
                    for user_resource_service_units in user_resource_info['resources'][resource_type]:
                        for user_resource_service_unit_attrib in user_resource_info['resources'][resource_type][user_resource_service_units]:
                            if user_resource_service_unit_attrib.find('date') > -1:
                                user_resource_info['resources'][resource_type][user_resource_service_units][user_resource_service_unit_attrib] = user_resource_info['resources'][resource_type][user_resource_service_units][user_resource_service_unit_attrib].strftime('%Y-%m-%dT%H:%M:%SZ')

        # return bson.json_util.dumps(user_resources_info)
        return user_resources_info

    def __generate_fdm_tag_str_from_dict(self, fdm_tag_dict):
        return ' > '.join(
            [
                fdm_tag_dict['company'],
                fdm_tag_dict['cost_center'],
                fdm_tag_dict['business_unit'],
                fdm_tag_dict['fund'],
                fdm_tag_dict['grant'],
                fdm_tag_dict['gift'],
                fdm_tag_dict['project'],
                fdm_tag_dict['designated'],
                fdm_tag_dict['function'],
                fdm_tag_dict['program_code'],
                fdm_tag_dict['activity'],
                fdm_tag_dict['assignee']
            ]
        )

    def __extract_fdm_tags_str_list(self, fdm_tag_list):
        fdm_tags_str_list = []
        for fdm_tag_dict in fdm_tag_list:
            fdm_tags_str_list.append(self.__generate_fdm_tag_str_from_dict(fdm_tag_dict))
        return fdm_tags_str_list

    def __validate_user_resource_request_authorization(self, group_info_db, pi_uid):
        if 'pi_uid' not in group_info_db or group_info_db['pi_uid'] is None or group_info_db['pi_uid'] == '':
            raise Exception('Cannot process the resource request: Please contact research computing user services dept to claim the owneship of the group for furthur processing')
        elif 'pi_uid' in group_info_db and group_info_db['pi_uid'] != '' and group_info_db['pi_uid'] != pi_uid:
            raise Exception('Cannot process the request: The requestor {} does not match the pi uid for the project'.format(self.__uid))
        elif 'pi_uid' in group_info_db and group_info_db['pi_uid'] != '' and group_info_db['pi_uid'] != self.__uid:
            raise Exception('Cannot process the request: The submitter {} does not match the pi uid for the project'.format(self.__uid))
        elif UVARCResourcRequestFormInfoDataManager(pi_uid).get_user_resource_request_info()['is_user_resource_request_elligible'] is False:
            raise Exception('Cannot process the request: The requestor {} is not elligible to submit the resource reuest'.format(self.__uid))
        return True

    def __validate_user_resource_request_info(self, group_info, group_info_db, resource_request_type, request_type):
        self.__validate_user_resource_request_authorization(group_info_db, group_info['pi_uid'])
        if group_info['data_agreement_signed'] is False:
            raise Exception('Cannot process the request: The data agreement was not signed by requestor {}'.format(self.__uid))

        if request_type == 'CREATE':
            if resource_request_type == 'hpc_service_units' and group_info['resources'][resource_request_type][group_info['group_name']]['tier'] not in RESOURCE_REQUESTS_SERVICE_UNITS_TIERS:
                raise Exception('Cannot process the new resource request: Unsupported service unit request tier was provided')
            elif resource_request_type == 'storage' and group_info['resources'][resource_request_type][group_info['group_name']]['tier'] not in RESOURCE_REQUESTS_STORAGE_TIERS:
                raise Exception('Cannot process the new resource request: Unsupported storage request tier was provided')
            elif 'resources' in group_info_db and resource_request_type in group_info_db['resources']:
                resource_request_id = group_info['group_name'] + '-' + group_info['resources'][resource_request_type][group_info['group_name']]['tier']
                if len(group_info_db['resources'][resource_request_type]) > 0 and resource_request_id in group_info_db['resources'][resource_request_type]:
                    raise Exception('Cannot process the new resource request: The resource request with same request name already exists in system')
                else:
                    resource_request_id = group_info['group_name']
                    if 'billing_details' in group_info['resources'][resource_request_type][resource_request_id] and 'fdm_billing_info' in group_info['resources'][resource_request_type][resource_request_id]['billing_details']:
                        for billing_detail in group_info['resources'][resource_request_type][resource_request_id]['billing_details']['fdm_billing_info']:
                            try:
                                uva_billing_info_validator = UVARCBillingInfoValidator(billing_detail)
                                uva_billing_info_validator.legacy_validation_fdm_info()
                            except Exception as ex:
                                raise ex

        elif request_type == 'UPDATE':
            if resource_request_type in group_info_db['resources'] and len(group_info_db['resources'][resource_request_type]) > 0:
                resource_request_id = list(group_info['resources'][resource_request_type].keys())[0]
                if resource_request_id not in group_info_db['resources'][resource_request_type]:
                    raise Exception('Cannot process the update resource request: The resource request with request name does not exists in system to update')
                elif group_info_db['resources'][resource_request_type][resource_request_id]['request_status'] in ['pending', 'processing']:
                    raise Exception('Cannot process the update resource request: The previous resource request caanot be pending/processing')
                else:
                    if 'billing_details' in group_info['resources'][resource_request_type][resource_request_id] and 'fdm_billing_info' in group_info['resources'][resource_request_type][resource_request_id]['billing_details']:
                        fdm_tags_str_db_list = []
                        if 'billing_details' in group_info_db['resources'][resource_request_type][resource_request_id] and 'fdm_billing_info' in group_info_db['resources'][resource_request_type][resource_request_id]['billing_details']:
                            fdm_tags_str_db_list = self.__extract_fdm_tags_str_list(group_info_db['resources'][resource_request_type][resource_request_id]['billing_details']['fdm_billing_info'])
                            
                        for billing_detail in group_info['resources'][resource_request_type][resource_request_id]['billing_details']['fdm_billing_info']:
                            if self.__generate_fdm_tag_str_from_dict(billing_detail) not in fdm_tags_str_db_list:
                                try:
                                    uva_billing_info_validator = UVARCBillingInfoValidator(billing_detail)
                                    uva_billing_info_validator.legacy_validation_fdm_info()
                                except Exception as ex:
                                    raise ex
        return True

    def __transfer_user_resource_request_info_to_db(self, group_info, group_info_db, resource_request_type, request_type):
        if self.__validate_user_resource_request_info(group_info, group_info_db, resource_request_type, request_type):
            if request_type == 'CREATE':
                group_info_db['pi_uid'] = group_info['pi_uid']
                group_info_db['project_name'] = group_info['project_name']
                group_info_db['project_desc'] = group_info['project_desc']
                group_info_db['data_agreement_signed'] = group_info['data_agreement_signed']
                group_info_db['delegates_uid'] = group_info['delegates_uid'] if 'delegates_uid' in group_info else ''
                if 'resources' not in group_info_db:
                    group_info_db['resources'] = {resource_request_type: {}}
                resource_request_id = group_info['group_name'] + '-' + group_info['resources'][resource_request_type][group_info['group_name']]['tier']
                group_info_db['resources'][resource_request_type][resource_request_id] = group_info['resources'][resource_request_type][group_info['group_name']]
                group_info_db['resources'][resource_request_type][resource_request_id]['request_date'] = datetime.now(timezone.utc)
                group_info_db['resources'][resource_request_type][resource_request_id]['update_date'] = datetime.now(timezone.utc)
                group_info_db['resources'][resource_request_type][resource_request_id]['request_status'] = 'pending'
            elif request_type == 'UPDATE':
                group_info_db['pi_uid'] = group_info['pi_uid']
                group_info_db['project_name'] = group_info['project_name']
                group_info_db['project_desc'] = group_info['project_desc']
                group_info_db['data_agreement_signed'] = group_info['data_agreement_signed']
                group_info_db['delegates_uid'] = group_info['delegates_uid'] if 'delegates_uid' in group_info else ''
                resource_request_id = list(group_info['resources'][resource_request_type].keys())[0]
                request_date = group_info_db['resources'][resource_request_type][resource_request_id]['request_date']
                group_info_db['resources'][resource_request_type][resource_request_id] = group_info['resources'][resource_request_type][resource_request_id]
                group_info_db['resources'][resource_request_type][resource_request_id]['request_date'] = request_date
                group_info_db['resources'][resource_request_type][resource_request_id]['update_date'] = datetime.now(timezone.utc)
                group_info_db['resources'][resource_request_type][resource_request_id]['request_status'] = 'pending'

            return group_info_db

    def create_user_resource_su_request_info(self, user_resource_request_info):
        resource_request_type = 'hpc_service_units'
        request_type = 'CREATE'
        self.__uvarc_group_data_manager = UVARCGroupsDataManager(user_resource_request_info['group_name'], upsert=True, refresh=True)
        group_info_db = self.__uvarc_group_data_manager.get_group_info()
        self.__uvarc_group_data_manager.set_group_info(
            self.__transfer_user_resource_request_info_to_db(user_resource_request_info, group_info_db, resource_request_type, request_type)
        )

    def update_user_resource_su_request_info(self, user_resource_request_info):
        resource_request_type = 'hpc_service_units'
        request_type = 'UPDATE'
        self.__uvarc_group_data_manager = UVARCGroupsDataManager(user_resource_request_info['group_name'], upsert=True, refresh=True)
        group_info_db = self.__uvarc_group_data_manager.get_group_info()
        self.__uvarc_group_data_manager.set_group_info(
            self.__transfer_user_resource_request_info_to_db(user_resource_request_info, group_info_db, resource_request_type, request_type)
        )

    def retire_user_resource_su_request_info(self, group_name, resource_request_type, resource_request_id):
        self.__uvarc_group_data_manager = UVARCGroupsDataManager(group_name, upsert=True, refresh=True)
        group_info_db = self.__uvarc_group_data_manager.get_group_info()
        # if self.__uid == group_info_db['pi_uid']: or ('delegates_uid' in group_info_db and self.__uid in group_info_db['delegates_uid']):
        if self.__validate_user_resource_request_authorization(group_info_db, self.__uid) and group_info_db['resources'][resource_request_type][resource_request_id]['request_status'] == 'active':
            if 'resources' in group_info_db and resource_request_type in group_info_db['resources'] and resource_request_id in group_info_db['resources'][resource_request_type]:
                group_info_db['resources'][resource_request_type][resource_request_id]["request_expiry_date"] = datetime.now(timezone.utc)
                group_info_db['resources'][resource_request_type][resource_request_id]['update_date'] = datetime.now(timezone.utc)
                group_info_db['resources'][resource_request_type][resource_request_id]['request_status'] = 'expired'
                self.__uvarc_group_data_manager.set_group_info(
                    group_info_db
                )
            else:
                raise Exception('Cannot process the retire resource request: The requested resource is not found')
        else:
            raise Exception('Cannot process the retire resource request: The requested resource is not active to retire')
        # else:
        #     raise Exception('Cannot process the retire resource request: The requestor UID is not authorized to submit the retire resource request')

    def create_user_resource_storage_request_info(self, user_resource_request_info):
        resource_request_type = 'storage'
        request_type = 'CREATE'
        self.__uvarc_group_data_manager = UVARCGroupsDataManager(user_resource_request_info['group_name'], upsert=True, refresh=True)
        group_info_db = self.__uvarc_group_data_manager.get_group_info()
        self.__uvarc_group_data_manager.set_group_info(
            self.__transfer_user_resource_request_info_to_db(user_resource_request_info, group_info_db, resource_request_type, request_type)
        )

    def update_user_resource_storage_request_info(self, user_resource_request_info):
        resource_request_type = 'storage'
        request_type = 'UPDATE'
        self.__uvarc_group_data_manager = UVARCGroupsDataManager(user_resource_request_info['group_name'], upsert=True, refresh=True)
        group_info_db = self.__uvarc_group_data_manager.get_group_info()
        self.__uvarc_group_data_manager.set_group_info(
            self.__transfer_user_resource_request_info_to_db(user_resource_request_info, group_info_db, resource_request_type, request_type)
        )

    def retire_user_resource_storage_request_info(self, group_name, resource_request_type, resource_request_id):
        self.__uvarc_group_data_manager = UVARCGroupsDataManager(group_name, upsert=True, refresh=True)
        group_info_db = self.__uvarc_group_data_manager.get_group_info()
        # if self.__uid == group_info_db['pi_uid'] or ('delegates_uid' in group_info_db and self.__uid in group_info_db['delegates_uid']):
        if self.__validate_user_resource_request_authorization(group_info_db, self.__uid) and group_info_db['resources'][resource_request_type][resource_request_id]['request_status'] == 'active':
            if 'resources' in group_info_db and resource_request_type in group_info_db['resources'] and resource_request_id in group_info_db['resources'][resource_request_type]:
                group_info_db['resources'][resource_request_type][resource_request_id]["request_expiry_date"] = datetime.now(timezone.utc)
                group_info_db['resources'][resource_request_type][resource_request_id]['update_date'] = datetime.now(timezone.utc)
                group_info_db['resources'][resource_request_type][resource_request_id]['request_status'] = 'expired'
                self.__uvarc_group_data_manager.set_group_info(
                    group_info_db
                )
            else:
                raise Exception('Cannot process the retire resource request: The requested resource is not found')
        else:
            raise Exception('Cannot process the retire resource request: The requested resource is not active to retire')
        # else:
        #     raise Exception('Cannot process the retire resource request: The requestor UID is not authorized to submit the retire resource request')


class UVARCBillingInfoValidator():
    def __init__(self, fdm_dict):
        self.__fdm_dict = fdm_dict

    def validate_fdm_info(self):
        workday_service_handler = WorkdayServiceHandler(app)
        return workday_service_handler.validate_fdm(self.__fdm_dict)

    def legacy_validation_fdm_info(self):
        billing_data = {
            'company': self.__fdm_dict['company'],
            'cost_center': self.__fdm_dict['cost_center'],
            'business_unit': self.__fdm_dict['business_unit'],
            'fund': self.__fdm_dict['fund'],
            'grant': self.__fdm_dict['grant'],
            'gift': self.__fdm_dict['gift'],
            'project': self.__fdm_dict['project'],
            'designated': self.__fdm_dict['designated'],
            'function': self.__fdm_dict['function'],
            'program': self.__fdm_dict['program_code'],
            'activity': self.__fdm_dict['activity'],
            'assignee': self.__fdm_dict['assignee']
        }
        api_url = "https://uvarc-unified-service.hpc.virginia.edu/uvarc/api/resource/rcwebform/fdm/verify"
        headers = {"Content-Type": "application/json", 'Origin': 'https://uvarc-api.pods.uvarc.io'}
        try:
            app.logger.info("starting to validation API")
            payload = json.dumps(billing_data)
            app.logger.info(payload)
            response = requests.post(api_url, headers=headers, data=payload)
            # app.logger.info("response:", response)
            response_dict = eval(json.loads(response.text)[0])
            if response_dict.get("Valid") == "true":
                return True
                print("Billing validation successful.")
            else:
                error_message = response_dict.get("ErrorText")
                raise ValueError(f"Billing validation failed: {error_message}")
        except Exception as ex:
            app.log_exception(ex)
            print(ex)
            raise ex
