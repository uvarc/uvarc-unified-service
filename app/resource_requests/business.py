import copy
import json
import bson
import bson.json_util
from datetime import datetime, timezone
from app.resource_requests.tasks import IntervalTasks

import requests
from app import app
from app.core.business import UVARCUserDataManager, UVARCGroupDataManager
from common_service_handlers.workday_service_handler import WorkdayServiceHandler
from common_utils import RESOURCE_REQUEST_FREE_SERVICE_UNITS_SSZ_INSTRUCTIONAL, RESOURCE_REQUEST_FREE_SERVICE_UNITS_SSZ_STANDARD, RESOURCE_REQUEST_FREE_STORAGE_SSZ_STANDARD, RESOURCE_REQUESTS_SERVICE_UNITS_TIERS, RESOURCE_REQUESTS_STORAGE_TIERS, RESOURCE_REQUESTS_ADMINS_INFO, RESOURCE_REQUESTS_DELEGATES_INFO, RESOURCE_TYPES


class UVARCAdminFormInfoDataManager():
    def __init__(self, group_name):
        self.__group_name = group_name

    def get_group_admin_info(self):
        self.__uvarc_group_data_manager = UVARCGroupDataManager(self.__group_name, upsert=True, refresh=True)
        group_info_db = self.__uvarc_group_data_manager.get_group_info()
        return {
            "is_owner_set": True if 'pi_uid' in group_info_db and group_info_db['pi_uid'] != None and group_info_db['pi_uid'].strip() != '' else False,
            "owner_uid": group_info_db['pi_uid'] if 'pi_uid' in group_info_db and group_info_db['pi_uid'] is not None and group_info_db['pi_uid'].strip() != '' else ''
        }

    def get_group_users_info(self):
        return {
            "users": UVARCGroupDataManager(self.__group_name, upsert=True, refresh=True).get_group_info()['group_members']
        }

    def set_group_admin_info(self, owner_uid):
        self.__uvarc_group_data_manager = UVARCGroupDataManager(self.__group_name, upsert=True, refresh=True)
        group_info_db = self.__uvarc_group_data_manager.get_group_info()
        if 'pi_uid' in group_info_db and group_info_db['pi_uid'] is not None and group_info_db['pi_uid'].strip() != '':
            raise Exception('Cannot process set group owner request: The group owner has already been claimed')
        if UVARCResourcRequestFormInfoDataManager(owner_uid).get_user_resource_request_info()['is_user_resource_request_elligible'] is False:
            raise Exception('Cannot process set group owner request: The user {} is not eligible to request research resource {}'.format(owner_uid, self.__group_name))
        if self.__group_name not in UVARCUserDataManager(uid=owner_uid, upsert=True, refresh=True).get_user_groups_info():
            raise Exception('Cannot process set group owner request: The {} is not part of grouper/mygrops {}'.format(owner_uid, self.__group_name))

        group_info_db['pi_uid'] = owner_uid
        self.__uvarc_group_data_manager.set_group_info(
            group_info_db
        )

    def update_resource_request_status(self, ticket_id, resource_request_type, resource_request_id, update_status, update_comment=None):
        uvarc_group_data_manager = UVARCGroupDataManager(self.__group_name, upsert=True, refresh=True)
        group_info_db = uvarc_group_data_manager.get_group_info()
        if 'resources' in group_info_db and resource_request_type in group_info_db['resources'] and resource_request_id in group_info_db['resources'][resource_request_type] and 'request_processing_details' in group_info_db['resources'][resource_request_type][resource_request_id] and 'tickets_info' in group_info_db['resources'][resource_request_type][resource_request_id]['request_processing_details']:
            tickets_info = group_info_db['resources'][resource_request_type][resource_request_id]['request_processing_details']['tickets_info']
            if tickets_info is not None and len(tickets_info) > 0 and ticket_id in tickets_info[len(tickets_info)-1]:
                if group_info_db['resources'][resource_request_type][resource_request_id]['request_status'] in ['processing', 'retiring'] and update_status == 'active':
                    group_info_db['resources'][resource_request_type][resource_request_id]["active_date"] = datetime.now(timezone.utc)
                    group_info_db['resources'][resource_request_type][resource_request_id]["expiry_date"] = None
                    group_info_db['resources'][resource_request_type][resource_request_id]["retire_date"] = None
                    group_info_db['resources'][resource_request_type][resource_request_id]['update_date'] = datetime.now(timezone.utc)
                    group_info_db['resources'][resource_request_type][resource_request_id]['update_comment'] = update_comment
                    group_info_db['resources'][resource_request_type][resource_request_id]['request_status'] = update_status
                elif group_info_db['resources'][resource_request_type][resource_request_id]['request_status'] == 'retiring' and update_status == 'retired':
                    group_info_db['resources'][resource_request_type][resource_request_id]["retire_date"] = datetime.now(timezone.utc)
                    group_info_db['resources'][resource_request_type][resource_request_id]['update_date'] = datetime.now(timezone.utc)
                    group_info_db['resources'][resource_request_type][resource_request_id]['update_comment'] = update_comment
                    group_info_db['resources'][resource_request_type][resource_request_id]['request_status'] = update_status
                elif group_info_db['resources'][resource_request_type][resource_request_id]['request_status'] in ['processing', 'retiring'] and update_status == 'error':
                    resource_request_hist = copy.deepcopy(group_info_db['resources'][resource_request_type][resource_request_id])
                    resource_request_hist['update_date'] = datetime.now(timezone.utc)
                    resource_request_hist['update_comment'] = update_comment
                    resource_request_hist['request_status'] = update_status
                    if tickets_info[len(tickets_info)-1][ticket_id] != None:
                        group_info_db['resources'][resource_request_type][resource_request_id] = tickets_info[len(tickets_info)-1][ticket_id]
                        group_info_db['resources'][resource_request_type][resource_request_id]['request_processing_details']['tickets_info'].append({ticket_id: resource_request_hist})
                    else:
                        group_info_db['resources'][resource_request_type].pop(resource_request_id)

                else:
                    raise Exception("Cannot update request status to {update_status}: Based on ciurrent status of this request, this action is not allowed.".format(update_status=update_status))
                # IntervalTasks.version_groups_info.delay()
                uvarc_group_data_manager.set_group_info(
                    group_info_db
                )
            else:
                if tickets_info is None or len(tickets_info) == 0 or ticket_id not in tickets_info[len(tickets_info)-1]:
                    raise Exception("Cannot process update request: Ticket id {ticket_id} provided did not match/found for this resource request".format(ticket_id=ticket_id))
                else:
                    raise Exception("Cannot process update request: Ticket id {ticket_id} provided is not the latest for this resource request".format(ticket_id=ticket_id))
        else:
            raise Exception("Cannot process update request: Ticket id {ticket_id} did not match/found for this resource request".format(ticket_id=ticket_id))


class UVARCResourcRequestFormInfoDataManager():
    def __init__(self, uid):
        self.__uid = uid

    def get_user_resource_request_info(self):
        self.__uvarc_user_data_manager = UVARCUserDataManager(uid=self.__uid, upsert=True, refresh=True)

        # print(self.__uvarc_user_data_manager.get_user_groups_info())
        owner_groups = self.__uvarc_user_data_manager.get_owner_groups_info()
        user_resources = list(self.__uvarc_user_data_manager.get_user_resources_info())
        for group_name in RESOURCE_REQUESTS_DELEGATES_INFO:
            if self.__uid in RESOURCE_REQUESTS_DELEGATES_INFO[group_name] and group_name not in owner_groups:
                group_info = UVARCGroupDataManager(group_name, upsert=True, refresh=True).get_group_info()
                if 'group_members' in group_info and group_info['group_members'] is not None and group_info['group_members'] != '' and self.__uid in group_info['group_members'] and 'resources' in group_info and 'pi_uid' in group_info and group_info['pi_uid'] is not None and group_info['pi_uid'].strip() != '':
                    user_resources.append(group_info)
                    owner_groups.append(group_name)

        return {
            'is_user_admin':  True if self.__uid in RESOURCE_REQUESTS_ADMINS_INFO else False,
            'is_user_resource_request_elligible': True if self.__uid in RESOURCE_REQUESTS_ADMINS_INFO else self.__uvarc_user_data_manager.is_user_resource_request_elligible(),
            'owner_groups': owner_groups,
            'user_resources': self.__transfer_db_data_to_user_resource_request_info(user_resources)
        }

    def get_user_groups_info(self):
        self.__uvarc_user_data_manager = UVARCUserDataManager(uid=self.__uid, upsert=True, refresh=True)
        return self.__uvarc_user_data_manager.get_user_groups_info()

    def __transfer_db_data_to_user_resource_request_info(self, user_resources_info):
        for user_resource_info in user_resources_info:
            user_resource_info.pop('_id')
            user_resource_info.pop('group_members')
            user_resource_info.pop('group_members_hist')
            user_resource_info.pop('group_members_update_time')
            for resource_type in RESOURCE_TYPES:
                if 'resources' in user_resource_info and resource_type in user_resource_info['resources']:
                    for user_resource_name in user_resource_info['resources'][resource_type]:
                        for user_resource_attrib in user_resource_info['resources'][resource_type][user_resource_name]:
                            if user_resource_attrib.endswith('date'):
                                user_resource_info['resources'][resource_type][user_resource_name][user_resource_attrib] = user_resource_info['resources'][resource_type][user_resource_name][user_resource_attrib].strftime('%Y-%m-%dT%H:%M:%SZ') if user_resource_info['resources'][resource_type][user_resource_name][user_resource_attrib] is not None else ''

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

    def __validate_user_resource_request_authorization(self, group_info_db, pi_uid, request_type):
        if 'group_members' not in group_info_db or group_info_db['group_members'] is None or group_info_db['group_members'] == '' or self.__uid not in group_info_db['group_members']:
            raise Exception('Cannot process the resource request: Requestor is not part of the group ({group_name}) to allow this change'.format(group_name=group_info_db['group_name']))
        if 'pi_uid' not in group_info_db or group_info_db['pi_uid'] is None or group_info_db['pi_uid'] == '':
            raise Exception('Cannot process the resource request: Please contact research computing user services dept to claim the owneship of the group for furthur processing')
        elif 'pi_uid' in group_info_db and group_info_db['pi_uid'] != '' and group_info_db['pi_uid'] != pi_uid and (request_type != 'UPDATE' or group_info_db['group_name'] not in RESOURCE_REQUESTS_DELEGATES_INFO or self.__uid not in RESOURCE_REQUESTS_DELEGATES_INFO[group_info_db['group_name']]):
            raise Exception('Cannot process the request: The requestor {} does not match the pi/delegate uid for the group {} to authorize this request'.format(self.__uid, group_info_db['group_name']))
        elif 'pi_uid' in group_info_db and group_info_db['pi_uid'] != '' and group_info_db['pi_uid'] != self.__uid and (request_type != 'UPDATE' or group_info_db['group_name'] not in RESOURCE_REQUESTS_DELEGATES_INFO or self.__uid not in RESOURCE_REQUESTS_DELEGATES_INFO[group_info_db['group_name']]):
            raise Exception('Cannot process the request: The submitter {} does not match the pi/delegate uid for the group {}'.format(self.__uid, group_info_db['group_name']))
        elif UVARCResourcRequestFormInfoDataManager(pi_uid).get_user_resource_request_info()['is_user_resource_request_elligible'] is False:
            raise Exception('Cannot process the request: The requestor {} is not eligible to submit the resource request'.format(self.__uid))
        return True

    def __get_pi_total_free_resource_distribution(self, resource_request_type, tier, pi_uid):
        user_resource_request_info = UVARCResourcRequestFormInfoDataManager(pi_uid).get_user_resource_request_info()
        free_resource_distribution_specified_count = 0
        for group_info in user_resource_request_info['user_resources']:
            if pi_uid == group_info['pi_uid']:
                if 'resources' in group_info and resource_request_type in group_info['resources'] and group_info['resources'][resource_request_type] is not None and len(group_info['resources'][resource_request_type]) > 0:
                    for resource_name in group_info['resources'][resource_request_type]:
                        if 'tier' in group_info['resources'][resource_request_type][resource_name] and tier == group_info['resources'][resource_request_type][resource_name]['tier'] and 'billing_details' in group_info['resources'][resource_request_type][resource_name] and 'free_resource_distribution_info' in group_info['resources'][resource_request_type][resource_name]['billing_details'] and pi_uid in group_info['resources'][resource_request_type][resource_name]['billing_details']['free_resource_distribution_info']:
                            if group_info['resources'][resource_request_type][resource_name]['status'] == 'active':
                                free_resource_distribution_specified_count = free_resource_distribution_specified_count + int(group_info['resources'][resource_request_type][resource_name]['billing_details']['free_resource_distribution_info'][pi_uid])
                            elif group_info['resources'][resource_request_type][resource_name]['status'] != 'retired':
                                raise Exception('Please contact UVARC admin: Cannot validate free resource distribution info for PI ({pi_uid}) when resource ({resource_name}) request is in "{status}" state'.format(pi_uid=pi_uid, resource_name=resource_name, status=group_info['resources'][resource_request_type][resource_name]['status']))
        return free_resource_distribution_specified_count

    def __validate_user_resource_request_info(self, group_info, group_info_db, resource_request_type, request_type):
        self.__validate_user_resource_request_authorization(group_info_db, group_info['pi_uid'], request_type)
        if group_info['data_agreement_signed'] is False:
            raise Exception('Cannot process the request: The data agreement was not signed by requestor {}'.format(self.__uid))

        if request_type == 'CREATE':
            if group_info['group_name'] not in group_info['resources'][resource_request_type]:
                raise Exception('Cannot process the new resource request: Resource name ({resource_name}) provided is not same as group name ({group_name})'.format(resource_name=list(group_info['resources'][resource_request_type].keys())[0], group_name=group_info['group_name']))
            if resource_request_type == 'hpc_service_units':
                if group_info['resources'][resource_request_type][group_info['group_name']]['tier'] not in RESOURCE_REQUESTS_SERVICE_UNITS_TIERS:
                    raise Exception('Cannot process the new resource request: Unsupported service unit request tier was provided')
                elif 'request_count' not in group_info['resources'][resource_request_type][group_info['group_name']]:
                    raise Exception('Cannot process the new resource request: request_count is missing')
                elif group_info['resources'][resource_request_type][group_info['group_name']]['tier'] == 'ssz_paid' and ('billing_details' not in group_info['resources'][resource_request_type][group_info['group_name']] or 'fdm_billing_info' not in group_info['resources'][resource_request_type][group_info['group_name']]['billing_details'] or len(group_info['resources'][resource_request_type][group_info['group_name']]['billing_details']['fdm_billing_info']) == 0):
                    raise Exception('Cannot process the new resource request: FDM billing details are required but missing for the paid tier resource request')
            elif resource_request_type == 'storage':
                if group_info['resources'][resource_request_type][group_info['group_name']]['tier'] not in RESOURCE_REQUESTS_STORAGE_TIERS:
                    raise Exception('Cannot process the new resource request: Unsupported storage request tier was provided')
                elif 'billing_details' not in group_info['resources'][resource_request_type][group_info['group_name']] or 'fdm_billing_info' not in group_info['resources'][resource_request_type][group_info['group_name']]['billing_details'] or len(group_info['resources'][resource_request_type][group_info['group_name']]['billing_details']['fdm_billing_info']) == 0:
                    raise Exception('Cannot process the new resource request: FDM billing details are required but missing for the paid tier resource request')
                elif 'request_size' not in group_info['resources'][resource_request_type][group_info['group_name']]:
                    raise Exception('Cannot process the new resource request: request_size is missing')
                elif group_info['resources'][resource_request_type][group_info['group_name']]['tier'] == 'ssz_standard' and 'billing_details' in group_info['resources'][resource_request_type][group_info['group_name']] and 'free_resource_distribution_info' in group_info['resources'][resource_request_type][group_info['group_name']]['billing_details'] and group_info['resources'][resource_request_type][group_info['group_name']]['billing_details']['free_resource_distribution_info'] is not None and len(group_info['resources'][resource_request_type][group_info['group_name']]['billing_details']['free_resource_distribution_info']) > 0:
                    for pi_uid in group_info['resources'][resource_request_type][group_info['group_name']]['billing_details']['free_resource_distribution_info']:
                        if pi_uid == group_info_db['pi_uid']:
                            pi_total_free_resource_distribution = self.__get_pi_total_free_resource_distribution(resource_request_type, group_info['resources'][resource_request_type][group_info['group_name']]['tier'], pi_uid)
                            increase_ammt = int(group_info['resources'][resource_request_type][group_info['group_name']]['billing_details']['free_resource_distribution_info'][pi_uid])
                            if (int(pi_total_free_resource_distribution) + increase_ammt) > RESOURCE_REQUEST_FREE_STORAGE_SSZ_STANDARD:
                                raise Exception('Cannot process the new resource request: Requested free storage exceeds maximum free storage available ({balance_free_storage} TB) for the PI ({pi_uid}) for this resource'.format(balance_free_storage=(RESOURCE_REQUEST_FREE_STORAGE_SSZ_STANDARD-pi_total_free_resource_distribution), pi_uid=pi_uid))
                        else:
                            raise Exception('Cannot process the new resource request: You are not not PI on this project to set free resource distribution for this resource')
            if 'resources' in group_info_db and resource_request_type in group_info_db['resources']:
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
                elif group_info_db['resources'][resource_request_type][resource_request_id]['request_status'] in ['processing', 'retiring', 'retired']:
                    raise Exception('Cannot process the update resource request: The previous resource request caanot be in {status} state'.format(status=group_info_db['resources'][resource_request_type][resource_request_id]['request_status']))
                else:
                    if resource_request_type == 'hpc_service_units':
                        if group_info['resources'][resource_request_type][resource_request_id]['tier'] not in RESOURCE_REQUESTS_SERVICE_UNITS_TIERS:
                            raise Exception('Cannot process the update resource request: Unsupported service unit request tier was provided')
                        elif 'request_count' not in group_info['resources'][resource_request_type][resource_request_id]:
                            raise Exception('Cannot process the update resource request: request_count is missing')
                        elif group_info['resources'][resource_request_type][resource_request_id]['tier'] == 'ssz_paid' and ('billing_details' not in group_info['resources'][resource_request_type][resource_request_id] or 'fdm_billing_info' not in group_info['resources'][resource_request_type][resource_request_id]['billing_details'] or len(group_info['resources'][resource_request_type][resource_request_id]['billing_details']['fdm_billing_info']) == 0):
                            raise Exception('Cannot process the update resource request: FDM billing details are required but missing for the paid tier resource request')
                    elif resource_request_type == 'storage':
                        if group_info['resources'][resource_request_type][resource_request_id]['tier'] not in RESOURCE_REQUESTS_STORAGE_TIERS:
                            raise Exception('Cannot process the new resource request: Unsupported storage request tier was provided')
                        elif 'billing_details' not in group_info['resources'][resource_request_type][resource_request_id] or 'fdm_billing_info' not in group_info['resources'][resource_request_type][resource_request_id]['billing_details'] or len(group_info['resources'][resource_request_type][resource_request_id]['billing_details']['fdm_billing_info']) == 0:
                            raise Exception('Cannot process the update resource request: FDM billing details are required but missing for the paid tier resource request')
                        elif 'request_size' not in group_info['resources'][resource_request_type][resource_request_id]:
                            raise Exception('Cannot process the new resource request: request_size is missing')
                        elif group_info['resources'][resource_request_type][resource_request_id]['tier'] == 'ssz_standard' and 'billing_details' in group_info['resources'][resource_request_type][resource_request_id] and 'free_resource_distribution_info' in group_info['resources'][resource_request_type][resource_request_id]['billing_details'] and group_info['resources'][resource_request_type][resource_request_id]['billing_details']['free_resource_distribution_info'] is not None and len(group_info['resources'][resource_request_type][resource_request_id]['billing_details']['free_resource_distribution_info']) > 0:
                            for pi_uid in group_info['resources'][resource_request_type][resource_request_id]['billing_details']['free_resource_distribution_info']:
                                if pi_uid == group_info_db['pi_uid']:
                                    pi_total_free_resource_distribution_current_usage = 0
                                    pi_total_free_resource_distribution = self.__get_pi_total_free_resource_distribution(resource_request_type, group_info['resources'][resource_request_type][resource_request_id]['tier'],pi_uid)
                                    increase_ammt = int(group_info['resources'][resource_request_type][resource_request_id]['billing_details']['free_resource_distribution_info'][pi_uid])
                                    if group_info_db['resources'][resource_request_type][resource_request_id]['tier'] == 'ssz_standard' and 'billing_details' in group_info_db['resources'][resource_request_type][resource_request_id] and 'free_resource_distribution_info' in group_info_db['resources'][resource_request_type][resource_request_id]['billing_details'] and group_info_db['resources'][resource_request_type][resource_request_id]['billing_details']['free_resource_distribution_info'] is not None and len(group_info_db['resources'][resource_request_type][resource_request_id]['billing_details']['free_resource_distribution_info']) > 0 and pi_uid in group_info_db['resources'][resource_request_type][resource_request_id]['billing_details']['free_resource_distribution_info']:
                                        pi_total_free_resource_distribution_current_usage = pi_total_free_resource_distribution - int(group_info_db['resources'][resource_request_type][resource_request_id]['billing_details']['free_resource_distribution_info'][pi_uid])
                                    if (int(pi_total_free_resource_distribution_current_usage) + increase_ammt) > RESOURCE_REQUEST_FREE_STORAGE_SSZ_STANDARD:
                                        raise Exception('Cannot process the update resource request: Requested free storage exceeds maximum free storage available ({balance_free_storage} TB) for the PI ({pi_uid}) for this resource'.format(balance_free_storage=(RESOURCE_REQUEST_FREE_STORAGE_SSZ_STANDARD-pi_total_free_resource_distribution_current_usage), pi_uid=pi_uid))
                                else:
                                    raise Exception('Cannot process the update resource request: You are not not PI on this project to set free resource distribution for this resource')
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
                elif resource_request_type not in group_info_db['resources']:
                    group_info_db['resources'][resource_request_type] = {}
                    
                resource_request_id = group_info['group_name'] + '-' + group_info['resources'][resource_request_type][group_info['group_name']]['tier']
                if resource_request_type == 'hpc_service_units':
                    if group_info['resources'][resource_request_type][group_info['group_name']]['tier'] == 'ssz_paid':
                        group_info['resources'][resource_request_type][group_info['group_name']]['request_count'] = int(group_info['resources'][resource_request_type][group_info['group_name']]['request_count'])
                        group_info['resources'][resource_request_type][group_info['group_name']]['billing_details']['pending_bill_count'] = int(group_info['resources'][resource_request_type][group_info['group_name']]['request_count'])
                    elif group_info['resources'][resource_request_type][group_info['group_name']]['tier'] == 'ssz_standard':
                        group_info['resources'][resource_request_type][group_info['group_name']]['request_count'] = RESOURCE_REQUEST_FREE_SERVICE_UNITS_SSZ_STANDARD
                    elif group_info['resources'][resource_request_type][group_info['group_name']]['tier'] == 'ssz_instructional':
                        group_info['resources'][resource_request_type][group_info['group_name']]['request_count'] = RESOURCE_REQUEST_FREE_SERVICE_UNITS_SSZ_INSTRUCTIONAL
              
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
                if resource_request_type == 'hpc_service_units':
                    if group_info['resources'][resource_request_type][resource_request_id]['tier'] == 'ssz_paid':
                        request_count = int(group_info['resources'][resource_request_type][resource_request_id]['request_count'])
                        group_info['resources'][resource_request_type][resource_request_id]['request_count'] = group_info_db['resources'][resource_request_type][resource_request_id]['request_count'] + request_count
                        group_info['resources'][resource_request_type][resource_request_id]['billing_details']['pending_bill_count'] = group_info_db['resources'][resource_request_type][resource_request_id]['billing_details']['pending_bill_count'] + request_count
                    elif group_info['resources'][resource_request_type][resource_request_id]['tier'] == 'ssz_standard':
                        group_info['resources'][resource_request_type][resource_request_id]['request_count'] = RESOURCE_REQUEST_FREE_SERVICE_UNITS_SSZ_STANDARD
                    elif group_info['resources'][resource_request_type][resource_request_id]['tier'] == 'ssz_instructional':
                        group_info['resources'][resource_request_type][resource_request_id]['request_count'] = RESOURCE_REQUEST_FREE_SERVICE_UNITS_SSZ_INSTRUCTIONAL
                if 'request_processing_details' in group_info_db['resources'][resource_request_type][resource_request_id]:
                    group_info['resources'][resource_request_type][resource_request_id]['request_processing_details'] = group_info_db['resources'][resource_request_type][resource_request_id]['request_processing_details']
                group_info_db['resources'][resource_request_type][resource_request_id] = group_info['resources'][resource_request_type][resource_request_id]
                group_info_db['resources'][resource_request_type][resource_request_id]['request_date'] = request_date
                group_info_db['resources'][resource_request_type][resource_request_id]['update_date'] = datetime.now(timezone.utc)
                group_info_db['resources'][resource_request_type][resource_request_id]['request_status'] = 'pending'

            return group_info_db, resource_request_id

    def create_user_resource_su_request_info(self, user_resource_request_info):
        resource_request_type = 'hpc_service_units'
        request_type = 'CREATE'
        self.__uvarc_group_data_manager = UVARCGroupDataManager(user_resource_request_info['group_name'], upsert=True, refresh=True)
        group_info_db = self.__uvarc_group_data_manager.get_group_info()
        resource_request_hist = copy.deepcopy(group_info_db)
        group_info_db, resource_request_id = self.__transfer_user_resource_request_info_to_db(user_resource_request_info, group_info_db, resource_request_type, request_type)
        # IntervalTasks.version_groups_info.delay()
        self.__uvarc_group_data_manager.set_group_info(
            group_info_db
        )
        IntervalTasks.process_pending_resource_request.delay(
            user_resource_request_info['group_name'],
            request_type, 
            resource_request_type,
            'Rivanna',
            resource_request_hist['resources'][resource_request_type][resource_request_id] if resource_request_id in resource_request_hist['resources'][resource_request_type] else None,
            self.__uid
        )

    def update_user_resource_su_request_info(self, user_resource_request_info):
        resource_request_type = 'hpc_service_units'
        request_type = 'UPDATE'
        self.__uvarc_group_data_manager = UVARCGroupDataManager(user_resource_request_info['group_name'], upsert=True, refresh=True)
        group_info_db = self.__uvarc_group_data_manager.get_group_info()
        resource_request_hist = copy.deepcopy(group_info_db)
        group_info_db, resource_request_id =  self.__transfer_user_resource_request_info_to_db(user_resource_request_info, group_info_db, resource_request_type, request_type)
        # IntervalTasks.version_groups_info.delay()
        self.__uvarc_group_data_manager.set_group_info(
            group_info_db
        )
        IntervalTasks.process_pending_resource_request.delay(
            user_resource_request_info['group_name'],
            request_type, 
            resource_request_type, 
            'Rivanna',
            resource_request_hist['resources'][resource_request_type][resource_request_id] if resource_request_id in resource_request_hist['resources'][resource_request_type] else None,
            self.__uid
        )

    def retire_user_resource_su_request_info(self, group_name, resource_request_type, resource_request_id):
        self.__uvarc_group_data_manager = UVARCGroupDataManager(group_name, upsert=True, refresh=True)
        group_info_db = self.__uvarc_group_data_manager.get_group_info()
        resource_request_hist = copy.deepcopy(group_info_db)
        # if self.__uid == group_info_db['pi_uid']: or ('delegates_uid' in group_info_db and self.__uid in group_info_db['delegates_uid']):
        if self.__validate_user_resource_request_authorization(group_info_db, self.__uid) and group_info_db['resources'][resource_request_type][resource_request_id]['request_status'] == 'active':
            if 'resources' in group_info_db and resource_request_type in group_info_db['resources'] and resource_request_id in group_info_db['resources'][resource_request_type]:
                group_info_db['resources'][resource_request_type][resource_request_id]['expiry_date'] = datetime.now(timezone.utc)
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
        IntervalTasks.process_pending_resource_request.delay(
            group_name,
            'DELETE',
            resource_request_type,
            'Rivanna',
            resource_request_hist['resources'][resource_request_type][resource_request_id] if resource_request_id in resource_request_hist['resources'][resource_request_type] else None,
            self.__uid
        )

    def create_user_resource_storage_request_info(self, user_resource_request_info):
        # IntervalTasks.process_pending_resource_request.delay('uvarc_core')
        resource_request_type = 'storage'
        request_type = 'CREATE'
        self.__uvarc_group_data_manager = UVARCGroupDataManager(user_resource_request_info['group_name'], upsert=True, refresh=True)
        group_info_db = self.__uvarc_group_data_manager.get_group_info()
        resource_request_hist = copy.deepcopy(group_info_db)
        group_info_db, resource_request_id = self.__transfer_user_resource_request_info_to_db(user_resource_request_info, group_info_db, resource_request_type, request_type)
        self.__uvarc_group_data_manager.set_group_info(
            group_info_db
        )
        IntervalTasks.process_pending_resource_request.delay(
            user_resource_request_info['group_name'],
            request_type,
            resource_request_type,
            'Storage',
            resource_request_hist['resources'][resource_request_type][resource_request_id] if resource_request_id in resource_request_hist['resources'][resource_request_type] else None,
            self.__uid
        )

    def update_user_resource_storage_request_info(self, user_resource_request_info):
        resource_request_type = 'storage'
        request_type = 'UPDATE'
        self.__uvarc_group_data_manager = UVARCGroupDataManager(user_resource_request_info['group_name'], upsert=True, refresh=True)
        group_info_db = self.__uvarc_group_data_manager.get_group_info()
        resource_request_hist = copy.deepcopy(group_info_db)
        group_info_db, resource_request_id = self.__transfer_user_resource_request_info_to_db(user_resource_request_info, group_info_db, resource_request_type, request_type)
        self.__uvarc_group_data_manager.set_group_info(
            group_info_db
        )
        IntervalTasks.process_pending_resource_request.delay(
            user_resource_request_info['group_name'],
            request_type,
            resource_request_type,
            'Storage',
            resource_request_hist['resources'][resource_request_type][resource_request_id] if resource_request_id in resource_request_hist['resources'][resource_request_type] else None,
            self.__uid
        )

    def retire_user_resource_storage_request_info(self, group_name, resource_request_type, resource_request_id):
        self.__uvarc_group_data_manager = UVARCGroupDataManager(group_name, upsert=True, refresh=True)
        group_info_db = self.__uvarc_group_data_manager.get_group_info()
        resource_request_hist = copy.deepcopy(group_info_db)
        # if self.__uid == group_info_db['pi_uid'] or ('delegates_uid' in group_info_db and self.__uid in group_info_db['delegates_uid']):
        if self.__validate_user_resource_request_authorization(group_info_db, self.__uid) and group_info_db['resources'][resource_request_type][resource_request_id]['request_status'] == 'active':
            if 'resources' in group_info_db and resource_request_type in group_info_db['resources'] and resource_request_id in group_info_db['resources'][resource_request_type]:
                group_info_db['resources'][resource_request_type][resource_request_id]["expiry_date"] = datetime.now(timezone.utc)
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
        IntervalTasks.process_pending_resource_request.delay(
            group_name,
            'DELETE',
            resource_request_type,
            'Storage',
            resource_request_hist['resources'][resource_request_type][resource_request_id] if resource_request_id in resource_request_hist['resources'][resource_request_type] else None,
            self.__uid
        )


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


class UVARCResourceRequestsFlowManager():
    def __init__(self):
        pass
