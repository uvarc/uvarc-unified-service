import bson
import bson.json_util
from datetime import datetime, timezone
from app import app, mongo_service
from app.account_requests.business import UVARCUsersDataManager, UVARCGroupsDataManager
from common_utils import RESOURCE_REQUESTS_SERVICE_UNITS_TIERS


class UVARCResourcRequestFormInfoDataManager():
    def __init__(self, uid):
        self.__uid = uid

    def get_user_resource_request_info(self):
        self.__uvarc_user_data_manager = UVARCUsersDataManager(uid=self.__uid, upsert=True, refresh=True)
        return {
            'is_user_resource_request_elligible':  self.__uvarc_user_data_manager.is_user_resource_request_elligible(),
            'user_groups': self.__uvarc_user_data_manager.get_user_groups_info(),
            'user_resources':  bson.json_util.dumps(list(self.__uvarc_user_data_manager.get_user_resources_info()))
        }

    def __validate_user_resource_request_info(self, group_info, group_info_db, resource_request_type, request_type):
        if 'pi_uid' in group_info_db and group_info_db['pi_uid']!='' and group_info_db['pi_uid'] != group_info['pi_uid']:
            raise Exception('Cannot process the request: The requestor uid does not match the pi uid for the project')
        elif group_info['data_agreement_signed'] is False:
            raise Exception('Cannot process the request: The data agreement is not accepted by usert')
        elif resource_request_type == 'hpc_service_units' and group_info['resources'][resource_request_type][group_info['group_name']]['tier'] not in RESOURCE_REQUESTS_SERVICE_UNITS_TIERS:
            raise Exception('Cannot process the request: Unsupported service unit tier was provided')

        if request_type == 'CREATE':
            resource_request_id = group_info['group_name'] + '-' + group_info['resources'][resource_request_type][group_info['group_name']]['tier']
            if resource_request_type in group_info_db['resources'] and len(group_info_db['resources'][resource_request_type]) > 0 and resource_request_id in group_info_db['resources'][resource_request_type]:
                raise Exception('Cannot process the resource request: The resource request with same request name already exists in system')
  
        return True
    
    def __transfer_user_resource_request_info(self, group_info, group_info_db, resource_request_type, request_type):
        if self.__validate_user_resource_request_info(group_info, group_info_db, resource_request_type, request_type):
            if request_type == 'CREATE':
                group_info_db['pi_uid'] = group_info['pi_uid']
                group_info_db['project_name'] = group_info['project_name']
                group_info_db['project_desc'] = group_info['project_desc']
                group_info_db['data_agreement_signed'] = group_info['data_agreement_signed']
                group_info_db['delegates_uid'] = group_info['delegates_uid'] if 'delegates_uid' in group_info else ''
                resource_request_id = group_info['group_name'] + '-' + group_info['resources'][resource_request_type][group_info['group_name']]['tier']
                group_info_db['resources'][resource_request_type][resource_request_id] = group_info['resources'][resource_request_type][group_info['group_name']]
                group_info_db['resources'][resource_request_type][resource_request_id]['request_date'] = datetime.now(timezone.utc)
                group_info_db['resources'][resource_request_type][resource_request_id]['update_date'] = datetime.now(timezone.utc)
                group_info_db['resources'][resource_request_type][resource_request_id]['request_status'] = 'pending'

            return group_info_db

    def create_user_resource_su_request_info(self, user_resource_request_info):
        resource_request_type = 'hpc_service_units'
        request_type = 'CREATE'
        self.__uvarc_group_data_manager = UVARCGroupsDataManager(user_resource_request_info['group_name'], upsert=True, refresh=True)
        group_info_db = self.__uvarc_group_data_manager.get_group_info()
        self.__uvarc_group_data_manager.set_grouo_info(
            self.__transfer_user_resource_request_info(user_resource_request_info, group_info_db, resource_request_type, request_type)
        )

    def update_user_resource_su_request_info(self, user_resource_request_info):
        self.__uvarc_group_data_manager = UVARCGroupsDataManager(user_resource_request_info['group_name'], upsert=True, refresh=True)
        group_info_db = self.__uvarc_group_data_manager.get_group_info()
        if self.__validate_user_resource_request_info(user_resource_request_info, group_info_db, 'hpc_service_units'):
            pass

    def create_user_resource_storage_request_info(self, user_resource_request_info):
        resource_request_type = 'storage'
        request_type = 'CREATE'
        self.__uvarc_group_data_manager = UVARCGroupsDataManager(user_resource_request_info['group_name'], upsert=True, refresh=True)
        group_info_db = self.__uvarc_group_data_manager.get_group_info()
        self.__uvarc_group_data_manager.set_grouo_info(
            self.__transfer_user_resource_request_info(user_resource_request_info, group_info_db, resource_request_type, request_type)
        )

    def update_user_resource_storage_request_info(self, user_resource_request_info):
        self.__uvarc_group_data_manager = UVARCGroupsDataManager(user_resource_request_info['group_name'], upsert=True, refresh=True)
        group_info_db = self.__uvarc_group_data_manager.get_group_info()
        if self.__validate_user_resource_request_info(user_resource_request_info, group_info_db, 'storage'):
            pass
