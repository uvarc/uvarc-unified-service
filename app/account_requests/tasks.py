from app import app, celery
from .business import UVARCUsersSyncManager


class IntervalTasks:
    @celery.task(name="ldap_requests_sync_ldap_data_task")
    def sync_ldap_data():
        try:
            # Read, download files (if for preprocessing) and mark for scheduled preprocessing or processing in mongodb
            app.logger.info("ldap_requests_sync_ldap_data_task: Started")
            uvarc_user_sync_manager = UVARCUsersSyncManager()
            uvarc_user_sync_manager.backfill_users_hist_info()
            uvarc_user_sync_manager.sync_users_info()
            app.logger.info("ldap_requests_sync_ldap_data_task: Ended")
        except Exception as ex:
            app.logger.info("ldap_requests_sync_ldap_data_task: Failed")
            print(ex)
            app.logger.exception(ex)
