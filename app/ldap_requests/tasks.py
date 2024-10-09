from app import app, celery
from .business import LDAPSyncJobBusinessLogic

class IntervalTasks:
    @celery.task(name="ldap_requests_sync_ldap_data_task")
    def sync_ldap_data():
        try:
            # Read, download files (if for preprocessing) and mark for scheduled preprocessing or processing in mongodb
            app.logger.info("ldap_requests_sync_ldap_data_task: Started")
            ldap_sync = LDAPSyncJobBusinessLogic(app)
            ldap_sync.init_db()
            app.logger.info("ldap_requests_sync_ldap_data_task: Ended")
        except Exception as ex:
            app.logger.info("ldap_requests_sync_ldap_data_task: Failed")
            print(ex)
            app.logger.exception(ex)
