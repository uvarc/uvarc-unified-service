from app import app, celery


class IntervalTasks:
    @celery.task(name="process_pending_resource_request_task")
    def process_pending_resource_request(group_name, resource_request_type, resource_request_id):
        try:
            # Read, download files (if for preprocessing) and mark for scheduled preprocessing or processing in mongodb
            app.logger.info("process_pending_resource_request_task: Started")

            app.logger.info("process_pending_resource_request_task: Ended")
        except Exception as ex:
            app.logger.info("process_pending_resource_request_task: Failed")
            print(ex)
            app.logger.exception(ex)
