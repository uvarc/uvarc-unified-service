import csv
from datetime import datetime, timezone
import pymongo
import requests
import pandas as pd
from deepdiff import DeepDiff
from app import app, mongo_service
from common_service_handlers.ldap_service_handler import PrivateLDAPServiceHandler, PublicLDAPServiceHandler
from common_utils import synchronized


class UVARCUsersDataManager:
    def __init__(self, uid, upsert=True, refresh=False):
        if uid is None:
            raise Exception('User uid provided cannot be {}'.format(uid))
        self.__user = self.__get_user_all_info(uid, upsert, refresh)
        if self.__user is None:
            raise Exception('User with uid {} not found'.format(uid))
        self.__user_resources = self.__get_user_all_resources_info(uid)

    def __refresh_user_all_info(self, uid):
        user = mongo_service.db.uvarc_users.find_one({"uid": uid})
        if user:
            UVARCUsersGroupsSyncManager().sync_user_info(user)
        else:
            raise Exception('User with uid {} not found'.format(uid))

    def __get_user_all_info(self, uid, upsert=True, refresh=False):
        if upsert and mongo_service.db.uvarc_users.count_documents({'uid': uid}) == 0:
            UVARCUsersGroupsSyncManager().create_user_info({'uid': uid})
        elif refresh:
            self.__refresh_user_all_info(uid)
        user = mongo_service.db.uvarc_users.find_one({"uid": uid})
        return user

    def __get_user_all_resources_info(self, uid):
        return mongo_service.db.uvarc_groups.find({"pi_uid": uid})

    def is_user_resource_request_elligible(self):
        if 'member_groups' in self.__user and 'research-infrastructure-users' in self.__user['member_groups']:
            return True
        else:
            return False

    def get_user_info(self):
        return self.__user

    def get_user_groups_info(self):
        member_groups = list(self.__user['member_groups'])
        if 'research-infrastructure-users' in member_groups:
            member_groups.remove('research-infrastructure-users')
        return member_groups

    def get_user_resources_info(self):
        return self.__user_resources


class UVARCGroupsDataManager:
    def __init__(self, group_name, upsert=True, refresh=False):
        if group_name is None:
            raise Exception('Group Name provided cannot be {}'.format(uid))
        self.__group = self.__get_group_all_info(group_name, upsert, refresh)
        if self.__group is None:
            raise Exception('Group with group_name {} not found'.format(group_name))
 
    def __refresh_group_all_info(self, group_name):
        group = mongo_service.db.uvarc_groups.find_one({"group_name": group_name})
        if group:
            UVARCUsersGroupsSyncManager().sync_group_info(group)
        else:
            raise Exception('Group with group_name {} not found'.format(group_name))

    def __get_group_all_info(self, group_name, upsert=True, refresh=False):
        if upsert and mongo_service.db.uvarc_groups.count_documents({'group_name': group_name}) == 0:
            UVARCUsersGroupsSyncManager().create_group_info({'group_name': group_name})
        elif refresh:
            self.__refresh_group_all_info(group_name)
        group = mongo_service.db.uvarc_groups.find_one({"group_name": group_name})
        return group

    def get_group_info(self):
        return self.__group

    def set_grouo_info(self, group_info):
        UVARCUsersGroupsSyncManager().update_group_resource_info(group_info)


class UVARCUsersGroupsSyncManager:
    def __init__(self):
        self.__private_ldap_service_handler = None
        self.__public_ldap_service_handler = None
        self.__private_ldap_service_handler = PrivateLDAPServiceHandler(app)
        self.__public_ldap_service_handler = PublicLDAPServiceHandler(app)
        self.hpc_url = f"https://{app.config["HPC_HOST"]}/api"
        self.hpc_key = app.config['HPC_CLIENT_SECRET']
        self.__combined_ldap_attributes_list = [
            "uid",
            "displayName",
            "title",
            "description",
            "uvaDisplayDepartment",
            "department",
            "school",
            "pwdLastSet",
            "userAccountControl",
            "primaryGroupID",
            "uidNumber",
            "Sponsored",
            "Rivanna_Status",
            "date_of_query"
        ]

    def __del__(self):
        self.close()

    def close(self):
        if self.__private_ldap_service_handler:
            self.__private_ldap_service_handler.close()
            self.__private_ldap_service_handler = None
        if self.__public_ldap_service_handler:
            self.__public_ldap_service_handler.close()
            self.__public_ldap_service_handler = None

    def __get_commission(self, uid):
        base_url = f"{self.hpc_url}/commission/?userID={uid}"
        headers = {
            "Authorization": self.hpc_key,
        }

        if not uid:
            return None

        commision_entry = None
        # url = base_url + uid
        try:
            response = requests.get(base_url, headers=headers)
            data = response.json()
        except Exception:
            self.app.logger.warn("Exception occurred while fetching commision info: retrying")
            try:
                response = requests.get(base_url, headers=headers)
                data = response.json()
            except Exception as ex:
                app.logger.error(ex)
                raise ex
        # Valid Commission info
        if len(data) != 0:
            commision_entry = data[0]

        return commision_entry

    def __format_dates_for_input(self, response):

        response["date_of_query"] = datetime.strptime(
            response["date_of_query"], '%Y-%m-%dT%H:%M:%SZ')

        if response["pwdLastSet"] != "":
            response["pwdLastSet"] = datetime.strptime(
                response["pwdLastSet"], '%Y-%m-%dT%H:%M:%SZ')

        return response

    def fetch_user_all_info(self, uid):
        eservices_entry = self.__private_ldap_service_handler.get_private_ldap_info(
            uid)
        public_entry = self.__public_ldap_service_handler.get_public_ldap_info(
            uid)
        commission_entry = self.__get_commission(uid)

        if not eservices_entry:
            return (None, None)

        complete_ldap_entry = eservices_entry

        if public_entry:
            public_entry[public_entry["uid"]] = public_entry
            complete_ldap_entry.update(public_entry)
        else:
            for public_attribute in self.__public_ldap_service_handler.get_public_ldap_query_attribute_list():
                complete_ldap_entry[public_attribute] = ""
            complete_ldap_entry["uid"] = complete_ldap_entry["sAMAccountName"]
        member_groups = []
        if 'memberOf' in complete_ldap_entry:
            for group in  complete_ldap_entry['memberOf']:
                if ('OU=Personal,OU=Groups,DC=eservices,DC=virginia,DC=edu'.lower() in group.lower() or
                    'OU=MyGroups,DC=eservices,DC=virginia,DC=edu'.lower() in group.lower()) and 'OU=IAM'.lower() not in group.lower():
                    member_groups.append(group.split(',')[0][3:])
        del complete_ldap_entry["sAMAccountName"]
        del complete_ldap_entry["memberOf"]
        # del complete_ldap_entry["uvaIsOwnerOf"]

        # current_timestamp = datetime.now(timezone.utc).replace(microsecond=0)
        complete_ldap_entry["date_of_query"] = datetime.now(
            timezone.utc).replace(
                microsecond=0).isoformat().replace(
                    '+00:00', 'Z')

        if commission_entry:
            commission_entry[commission_entry["name"]] = commission_entry
            complete_ldap_entry.update(commission_entry)
            del complete_ldap_entry["name"]
            complete_ldap_entry["Rivanna_Status"] = complete_ldap_entry["commission"]
            del complete_ldap_entry["commission"]
        else:
            complete_ldap_entry["Rivanna_Status"] = ""

        restructured_ldap_entry = {}
        # ordering restructure
        for attr in self.__combined_ldap_attributes_list:
            restructured_ldap_entry[attr] = complete_ldap_entry[attr]

        # print("Final entry: ", restructured_ldap_entry)

        return (restructured_ldap_entry, member_groups)

    def fetch_group_users(self, group_name):
        return self.__private_ldap_service_handler.get_group_users(
            group_name)

    def __build_user_info(self, user_info_dict, user_hist_info_dict, comment):
        user_info_dict["ldap_info_log"] = user_hist_info_dict
        user_info_dict["update_time"] = datetime.now(timezone.utc)
        user_info_dict["comment"] = comment
        return user_info_dict

    @synchronized
    def backfill_users_hist_info(self):
        # Read CSV File
        backfill_users_hist_info = pd.read_csv("data/dropbox/backfill/users_info.csv")

        # Only repopulate the database if there are no documents in there currently
        if mongo_service.db.uvarc_users.count_documents({}) == 0:
            # convert to datatime object
            backfill_users_hist_info["date_of_query"] = pd.to_datetime(
                backfill_users_hist_info["date_of_query"])

            # Convert NaN entries to empty strings
            backfill_users_hist_info = backfill_users_hist_info.fillna('')

            # Insert uid
            backfill_users_hist_info.insert(
                loc=0, column="uid", value=backfill_users_hist_info["UserID"])

            # Replace Lastname and Firstname w/ displayName
            backfill_users_hist_info.insert(loc=1, column="displayName", value=(
                backfill_users_hist_info["Lastname"] + ", " + backfill_users_hist_info["Firstname"] + " (" + backfill_users_hist_info["uid"] + ")"))
            backfill_users_hist_info.drop(
                columns=["Lastname", "Firstname"], inplace=True)

            # Fill out department
            def extract_department(affiliation):
                if ':' in affiliation:
                    return affiliation.split(':')[1]
                return affiliation

            backfill_users_hist_info["department"] = backfill_users_hist_info["affiliation"].apply(
                extract_department)
            # Create uvaDisplayDepartment attribute [in current ldap info -> might be list] and drop affiliation
            backfill_users_hist_info.insert(loc=4, column="uvaDisplayDepartment",
                                            value=(backfill_users_hist_info["affiliation"]))
            backfill_users_hist_info.drop(columns="affiliation", inplace=True)

            # Create a dictionary to hold user data
            user_data = {}
            # Create set of names
            uids = set()

            # Iterate over rows
            for index, backfill_user_hist_info in backfill_users_hist_info.iterrows():
                user_id = backfill_user_hist_info["UserID"]
                uids.add(user_id)
                # Convert the row to a dictionary and drop 'UserID'
                query = backfill_user_hist_info.drop(labels="UserID").to_dict()

                if user_id in user_data:
                    if query["date_of_query"] > user_data[user_id]["recent_ldap_info"]["date_of_query"]:
                        user_data[user_id]["ldap_info_log"].append(
                            user_data[user_id]["recent_ldap_info"])
                        user_data[user_id]["recent_ldap_info"] = query
                    else:
                        user_data[user_id]["ldap_info_log"].append(query)
                else:
                    user_data[user_id] = {
                        "recent_ldap_info": query, "ldap_info_log": []}

            backfill_users_info = []
            # Convert user_data for mongo_service. Insertion
            for user_id, queries in user_data.items():
                backfill_users_info.append(
                    self.__build_user_info(
                        user_info_dict=queries["recent_ldap_info"],
                        user_hist_info_dict=queries["ldap_info_log"],
                        comment="backfilled data"
                    )
                )

            # Insert records into the mongo_service.DB collection
            mongo_service.db.uvarc_users.insert_many(backfill_users_info)

    def backfill_groups_hist_info(self):
        if 'uvarc_groups' not in mongo_service.db.list_collection_names() or mongo_service.db.uvarc_groups.count_documents({}) == 0:
            with open('data/dropbox/backfill/groups_info.csv', mode='r') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                for group_info in csv_reader:
                    self.create_group_info(group_info)

    def create_user_info(self, user):
        app.logger.info('Creating new user with UID: {} '.format(user['uid']))
        user_all_info, user_all_group_info = self.fetch_user_all_info(user['uid'])
        app.logger.info('LDAP Data Fetched USER INFO: {} - Group INFO:  {}'.format(user_all_info, user_all_group_info))
        if user_all_info:
            user_all_info['member_groups'] = sorted(user_all_group_info)
            mongo_service.db.uvarc_users.insert_one(
                self.__build_user_info(
                    user_info_dict=user_all_info,
                    user_hist_info_dict=[],
                    comment="creating mew uvarc user"
                )
            )

    def create_group_info(self, group):
        app.logger.info('Creating new group with group name : {} '.format(group['group_name']))
        if 'uvarc_groups' not in mongo_service.db.list_collection_names() or mongo_service.db.uvarc_groups.count_documents({'group_name': group['group_name']}) == 0:
            group_members_ldap = self.fetch_group_users(group['group_name'])
            if group_members_ldap:
                for uid in group_members_ldap:
                    if mongo_service.db.uvarc_users.count_documents({'uid': uid}) == 0:
                        self.create_user_info({'uid': uid})

                group['group_members'] = group_members_ldap
                group_members_hist = []
                mongo_service.db.uvarc_groups.insert_one(
                    {
                        "group_name": group['group_name'],
                        "group_members": sorted(group_members_ldap),
                        "group_members_hist": group_members_hist,
                        "group_members_update_time": datetime.now(timezone.utc),
                        "group_id": "",
                        "project_name": "",
                        "project_desc": "",
                        "data_agreement_signed": False,
                        "pi_uid":  "",
                        "delegates_uid": [],
                        "resources": {
                            "hpc_service_units": {},
                            "storage": {}
                        }
                    }
                )

    def update_group_resource_info(self, group):
        mongo_service.db.uvarc_groups.update_one(
            {'group_name': group['group_name']},
            {
                "$set": group
            },
            False
        )

    @synchronized
    def sync_users_info(self):
        self.sync_groups_info()
        for user in mongo_service.db.uvarc_users.find({}).sort("uid", pymongo.ASCENDING):
            try:
                app.logger.info('{} sync started'.format(user['uid']))
                self.sync_user_info(user)
                app.logger.info('{} synced'.format(user['uid']))
            except Exception:
                app.logger.error('{} sync failed'.format(user['uid']))

    def sync_user_info(self, user):
        user_all_info, user_all_group_info = self.fetch_user_all_info(user['uid'])

        if user_all_info:
            user_all_info = self.__format_dates_for_input(
                user_all_info)
            if user:
                # if no changes, then no dictionary is sent back
                update_time_current = user["update_time"]
                comment_current = user["comment"]
                del user["update_time"]
                del user["comment"]
                
                if 'member_groups' not in user:
                    user['member_groups'] = []

                changed_fields = DeepDiff(
                    user, user_all_info, exclude_paths="root['date_of_query']")

                user["update_time"] = update_time_current
                user["comment"] = comment_current
                if (changed_fields and 'values_changed' in changed_fields) or (sorted(user['member_groups']) != sorted(user_all_group_info)):
                    app.logger.info('{} user changes detected'.format(user['uid']))
                    change_comment = "User info changes: "+ (str(changed_fields["values_changed"]) if 'values_changed' in changed_fields else "None") + " - "
                    change_comment = change_comment + "Group info changes: " + str(sorted(user_all_group_info)) if sorted(user['member_groups']) != sorted(user_all_group_info) else "None"
                    user_all_info['member_groups'] = sorted(user_all_group_info)
                    user_ldap_info_log = []
                    if 'ldap_info_log' in user:
                        user_ldap_info_log = user["ldap_info_log"]
                        del user["ldap_info_log"]
                    if '_id' in user:
                        del user['_id']
                    user_ldap_info_log.append(user)
                    user = user_all_info

                    mongo_service.db.uvarc_users.update_one(
                        # Filter to find the document
                        {"uid": user['uid']}, {
                            "$set": self.__build_user_info(
                                user_info_dict=user,
                                user_hist_info_dict=user_ldap_info_log,
                                comment=change_comment
                            )
                        }
                    )        

    def sync_groups_info(self):
        for group in mongo_service.db.uvarc_groups.find({}).sort("group_name", pymongo.ASCENDING):
            try:
                app.logger.info('{} group sync started'.format(group['group_name']))
                self.sync_group_info(group)
                app.logger.info('{} synced'.format(group['group_name']))
            except Exception as ex:
                app.logger.error('{} group sync failed: {}'.format(group['group_name'], ex))

    def sync_group_info(self, group):
        group_members_ldap = self.fetch_group_users(group['group_name'])
        if group:
            for uid in group_members_ldap:
                if mongo_service.db.uvarc_users.count_documents({'uid': uid}) == 0:
                    self.create_user_info({'uid': uid})
            if 'group_members' not in group:
                group['group_members'] = []
            if sorted(group_members_ldap) != group['group_members'] or (len(group['group_members']) == 0 and 'group_members_hist' not in group):
                app.logger.info('{} group changes detected'.format(group['group_name']))
                if 'group_members_hist' in group:
                    group_members_hist = group['group_members_hist']
                else:
                    group_members_hist = []
                if len(group['group_members']) > 0:
                    group_members_hist.append(group['group_members'])
                mongo_service.db.uvarc_groups.update_one(
                    {"group_name": group['group_name']},
                    {
                        "$set": {
                            "group_members": sorted(group_members_ldap),
                            "group_members_hist": group_members_hist,
                            "group_members_update_time": datetime.now(timezone.utc)
                        }
                    },
                    False
                )
