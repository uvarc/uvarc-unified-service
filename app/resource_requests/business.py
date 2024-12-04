from app import app, mongo_service
from app.account_requests.business import UVARCUsersDataManager, UVARCGroupsDataManager


class UVARCResourcRequestFormInfoDataManager():
    def __init__(self, uid):
        self.__uid = uid

    def get_user_resource_request_info(self):
        self.__uvarc_user_data_manager = UVARCUsersDataManager(uid=uid, upsert=True, refresh=True)
        return {
            'is_user_resource_request_elligible':  self.__uvarc_user_data_manager.is_user_resource_request_elligible(),
            'user_groups': self.__uvarc_user_data_manager.get_user_groups_info()
        }

    def __validate_user_resource_request_info(self, group_info, group_info_db):
        if 'pi_uid' in group_info_db and group_info_db['pi_uid'] !=  group_info('pi_uid'):
            raise Exception('Cannot process the request: The requestor uid does not match the pi uid for the project')
        if group_info['data_agreement_signed'] is False:
            raise Exception('Cannot process the request: The data agreement is not accepted by usert')
        return True

    def create_user_resource_request_info(self, user_resource_request_info):
        self.__uvarc_group_data_manager = UVARCGroupsDataManager(group_info['group_name'], upsert=True, refresh=True)
        group_info_db = self.__uvarc_group_data_manager.get_group_info()
        if self.__validate_user_resource_request_info(group_info, group_info_db):
            pass

    def update_user_resource_request_info(self, user_resource_request_info):
        self.__uvarc_group_data_manager = UVARCGroupsDataManager(group_info['group_name'], upsert=True, refresh=True)
        group_info_db = self.__uvarc_group_data_manager.get_group_info()
        if self.__validate_user_resource_request_info(group_info, group_info_db):
            pass
         
