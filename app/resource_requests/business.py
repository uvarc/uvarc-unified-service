from app import app, mongo_service
from app.account_requests.business import UVARCUsersDataManager


class UVARCResourcRequestFormInfoDataManager():
    def __init__(self, uid):
        self.__uvarc_user_data_manager = UVARCUsersDataManager(uid=uid, upsert=True, refresh=True)

    def get_resource_request_from_info(self, request):
        return {
            'request_base_url': request.headers.get('Origin'),
            'is_user_resource_request_elligible':  self.__uvarc_user_data_manager.is_user_resource_request_elligible(),
            'user_groups': self.__uvarc_user_data_manager.get_user_groups_info()
        }
