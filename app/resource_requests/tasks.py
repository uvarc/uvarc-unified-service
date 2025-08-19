import json
from app import app, celery
from app.core.business import UVARCGroupDataManager, UVARCGroupsDataManager
from app.ticket_requests.business import UVARCSupportRequestsManager


class IntervalTasks:
    @celery.task(name="process_pending_resource_request_task", autoretry_for=(Exception,), retry_backoff=60, retry_jitter=True, retry_kwargs={'max_retries': 5, 'countdown': 5})
    def process_pending_resource_request(group_name, request_type, resource_request_type, support_request_type, resource_request_hist, resource_requestor_uid):
        try:
            # Read, download files (if for preprocessing) and mark for scheduled preprocessing or processing in mongodb
            ticket_request_type = ''
            app.logger.info("process_pending_resource_request_task: Started")
            if request_type == 'CREATE':
                ticket_request_type = 'Create New Resource'
            elif request_type == 'UPDATE':
                ticket_request_type = 'Update/Renew Resource'
            elif request_type == 'DELETE':
                ticket_request_type = 'Retire Resource'
            uvarc_group_data_manager = UVARCGroupDataManager(group_name, upsert=True, refresh=True)
            group_info_db = uvarc_group_data_manager.get_group_info()
            for resource_name in sorted(group_info_db['resources'][resource_request_type]):
                if group_info_db['resources'][resource_request_type][resource_name]['request_status'] in ['pending', 'expired']:
                    uvarc_support_requests_manager = UVARCSupportRequestsManager()
                    ticket_request_payload = {
                        'uid': group_info_db['pi_uid'],
                        'grpup_name': group_info_db['group_name'],
                        'data_agreement_signed': group_info_db['data_agreement_signed'],
                        'project_name': group_info_db['project_name'],
                        'project_description': group_info_db['project_desc'],
                        'resource_type': resource_request_type,
                        'resource_name': resource_name,
                        'request_type': ticket_request_type,
                        'resource_requestor_uid': resource_requestor_uid
                    }
                    if resource_request_type == 'hpc_service_units':
                        ticket_request_payload['request_count'] = group_info_db['resources'][resource_request_type][resource_name]['request_count']
                        ticket_request_payload['allocation_name'] = resource_name
                    elif resource_request_type == 'storage':
                        ticket_request_payload['request_size'] = group_info_db['resources'][resource_request_type][resource_name]['request_size']
                        ticket_request_payload['share_name'] = resource_name
                    ticket_response = uvarc_support_requests_manager.create_support_request(
                        support_request_type,
                        ticket_request_payload
                    )
                    print(ticket_response)
                    app.logger.info(ticket_response)
                    group_info_db['resources'][resource_request_type][resource_name]['request_status'] = 'processing' if group_info_db['resources'][resource_request_type][resource_name]['request_status'] == 'pending' else 'retiring'
                    if 'request_processing_details' not in group_info_db['resources'][resource_request_type][resource_name]:
                        group_info_db['resources'][resource_request_type][resource_name]['request_processing_details'] = {'tickets_info': []}
                    if 'tickets_info' not in group_info_db['resources'][resource_request_type][resource_name]['request_processing_details']:
                        group_info_db['resources'][resource_request_type][resource_name]['request_processing_details']['tickets_info'] = []
                    group_info_db['resources'][resource_request_type][resource_name]['request_processing_details']['tickets_info'].append({str(json.loads(ticket_response)['issueKey']): resource_request_hist})

            uvarc_group_data_manager.set_group_info(
                group_info_db
            )

            app.logger.info("process_pending_resource_request_task: Ended")
            return "completed"
        except Exception as ex:
            app.logger.info("process_pending_resource_request_task: Failed ({group_name}, {request_type}, {resource_request_type}, {support_request_type})".format(group_name=group_name, request_type=request_type, resource_request_type=resource_request_type, support_request_type=support_request_type))
            print(ex)
            app.logger.exception(ex)
            raise Exception(ex)

    @celery.task(name="version_groups_info_task")
    def version_groups_info():
        try:
            app.logger.info("version_groups_info_task: Started")
            UVARCGroupsDataManager().version_groups()
            app.logger.info("version_groups_info_task: Ended")
        except Exception as ex:
            app.logger.info("version_groups_info_task: Failed")
            print(ex)
            app.logger.exception(ex)

    @celery.task(name="generate_and_transfer_resource_requests_billing_task")
    def generate_and_transfer_resource_requests_billing():
        try:
            # Read, download files (if for preprocessing) and mark for scheduled preprocessing or processing in mongodb
            app.logger.info("generate_and_transfer_resource_requests_billing_task: Started")

            app.logger.info("generate_and_transfer_resource_requests_billing_task: Ended")
        except Exception as ex:
            app.logger.info("generate_and_transfer_resource_requests_billing_task: Failed")
            print(ex)
            app.logger.exception(ex)

    @celery.task(name="send_resource_requests_emails_task")
    def send_resource_requests_emails():
        try:
            # Read, download files (if for preprocessing) and mark for scheduled preprocessing or processing in mongodb
            app.logger.info("send_resource_requests_emails_task: Started")

            app.logger.info("send_resource_requests_emails_task: Ended")
        except Exception as ex:
            app.logger.info("send_resource_requests_emails_task: Failed")
            print(ex)
            app.logger.exception(ex)   
