from app import app, celery

class IntervalTasks:
    @celery.task(name="sync_ldap_data_task")
    def sync_ldap_data():
        try:
            # Read, download files (if for preprocessing) and mark for scheduled preprocessing or processing in mongodb
            app.logger.info("sync_ldap_data_task: Started")
            
            app.logger.info("sync_ldap_data_task: Ended")
        except Exception as ex:
            app.logger.info("sync_ldap_data_task: Failed")
            print(ex)
            app.logger.exception(ex)
