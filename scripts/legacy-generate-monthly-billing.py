import boto3
import csv
import json
from datetime import date, datetime, timedelta

STANDARD_STORAGE_REQUEST_INFO_TABLE = 'jira_standard_storage_requests_info'
PROJECT_STORAGE_REQUEST_INFO_TABLE = 'jira_project_storage_requests_info'
PAID_SU_REQUESTS_INFO_TABLE = 'jira_paid_su_requests_info'


class DynamoDbTableData:
    def __init__(self, date_str):
        print (date_str)
        self.date_str = date_str
        self.aws_access_key_id = ''
        self.aws_secret_access_key = ''

    def get_items_from_paid_su_requests_info_table(self):
        try:
            dynamodb_session = boto3.Session(
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name='us-east-1'
            )
            tableName = PAID_SU_REQUESTS_INFO_TABLE
            # Initialize DynamoDB resource
            dynamodb = dynamodb_session.resource('dynamodb')
            table = dynamodb.Table(tableName)

            try:
                target_date = datetime.strptime(self.date_str, '%Y-%m')
            except ValueError:
                print(f"Invalid date format: {self.date_str}. Expected format: 'YYYY-MM'.")
                return None

            formatted_date = target_date.strftime('%Y-%m')

            response = table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr('date').begins_with(formatted_date))

            if 'Items' in response and response['Items']:
                items = response['Items']
                items.sort(key=lambda x: x['date'])
                print(f"Items retrieved successfully: {json.dumps(items, indent=4)}")
                return items
                # app.logger.info(json.dumps(items, indent=4))
            else:
                print(f"No items found before the date: {formatted_date}")
                # app.logger.warning(f"No items found before the date: {formatted_date}")
                return []

        except Exception as ex:
            # app.log_exception(ex)
            print(f"An error occurred: {ex}")
            return []

    def get_items_from_project_storage_requests_info_table(self):
        try:
            dynamodb_session = boto3.Session(
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name='us-east-1'
            )
            tableName = PROJECT_STORAGE_REQUEST_INFO_TABLE
            # Initialize DynamoDB resource
            dynamodb = dynamodb_session.resource('dynamodb')
            table = dynamodb.Table(tableName)

            try:
                target_date = datetime.strptime(self.date_str, '%Y-%m')
            except ValueError:
                print(f"Invalid date format: {self.date_str}. Expected format: 'YYYY-MM'.")
                return None

            formatted_date = target_date.strftime('%Y-%m')

            response = table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr('date').begins_with(formatted_date))

            if 'Items' in response and response['Items']:
                items = response['Items']
                items.sort(key=lambda x: x['date'])
                print(f"Items retrieved successfully: {json.dumps(items, indent=4)}")
                return items
                # app.logger.info(json.dumps(items, indent=4))
            else:
                print(f"No items found before the date: {formatted_date}")
                # app.logger.warning(f"No items found before the date: {formatted_date}")
                return []

        except Exception as ex:
            # app.log_exception(ex)
            print(f"An error occurred: {ex}")
            return []

    def get_items_from_standard_storage_requests_info_table(self):
        try:
            dynamodb_session = boto3.Session(
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name='us-east-1'
            )
            tableName = STANDARD_STORAGE_REQUEST_INFO_TABLE
            # Initialize DynamoDB resource
            dynamodb = dynamodb_session.resource('dynamodb')
            table = dynamodb.Table(tableName)

            try:
                target_date = datetime.strptime(self.date_str, '%Y-%m')
            except ValueError:
                print(f"Invalid date format: {self.date_str}. Expected format: 'YYYY-MM'.")
                return None

            formatted_date = target_date.strftime('%Y-%m')

            response = table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr('date').begins_with(formatted_date))

            if 'Items' in response and response['Items']:
                items = response['Items']
                items.sort(key=lambda x: x['date'])
                print(f"Items retrieved successfully: {json.dumps(items, indent=4)}")
                return items
                # app.logger.info(json.dumps(items, indent=4))
            else:
                print(f"No items found before the date: {formatted_date}")
                # app.logger.warning(f"No items found before the date: {formatted_date}")
                return []

        except Exception as ex:
            # app.log_exception(ex)
            print(f"An error occurred: {ex}")
            return []


class LegacyRCBillingHandler:
    def __init__(self):
        self.__all_fdm_lookup_dict = {}
        self.__all_standard_multi_fdm_dict = {}
        self.__all_project_multi_fdm_dict = {}
        self.__all_fdm_lookup_dict['standard_storage_fdm_info'] = self.__fetch_standard_storage_fdm_details()
        self.__all_fdm_lookup_dict['project_storage_fdms_info'] = self.__fetch_project_storage_fdm_details()

    def __fetch_standard_storage_fdm_details(self):
        share_name_fdm_lookup_dict = {}
        with open('/Users/ravichamakuri/UVAProjects/uvarc-unified-service/data/billing/standard-share-name-out.csv', mode='r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for fdm_row in reversed(list(csv_reader)):
                fdm_elements = fdm_row['Expense GLA'].split('>')
                # print(fdm_row)
                for index, raw_fdm_item in enumerate(fdm_elements):
                    fdm_elements[index] = fdm_elements[index].strip()
                share_name = ''
                if 'TB ' in fdm_row['Charge Description']:
                    if '/RC Storage Contract' in fdm_row['Charge Description'].split('TB ')[1]:
                        share_name = fdm_row['Charge Description'].split('TB ')[1].split('/RC Storage Contract')[0]
                    elif '/RC STORAGE CONTRACT' in  fdm_row['Charge Description'].split('TB ')[1]:
                        share_name = fdm_row['Charge Description'].split('TB ')[1].split('/RC STORAGE CONTRACT')[0]
                    elif '/ RC STORAGE CONTRACT' in  fdm_row['Charge Description'].split('TB ')[1]:
                        share_name = fdm_row['Charge Description'].split('TB ')[1].split('/ RC STORAGE CONTRACT')[0]
                    elif '/' in fdm_row['Charge Description'].split('TB ')[1]:
                        if 'research standard storage' in fdm_row['Charge Description'].split('TB ')[1].split('/')[1].strip():
                            share_name = fdm_row['Charge Description'].split('TB ')[1].split('/')[1].strip().split('research standard storage')[0].strip()
                        else:
                            share_name = fdm_row['Charge Description'].split('TB ')[1].split('/')[1].strip().split(' ')[0]
                    else:
                        if 'research standard storage' in fdm_row['Charge Description'].split('TB ')[1]:
                            share_name = fdm_row['Charge Description'].split('TB ')[1].split('research standard storage')[0].strip()
                            if ' ' in share_name:
                                share_name = share_name.split(' ')[0]
                        else:
                            share_name = fdm_row['Charge Description'].split('TB ')[1].split(' ')[0]
                elif '/' in fdm_row['Charge Description']:
                    if '/RC STORAGE CONTRACT' in fdm_row['Charge Description']:
                        share_name = fdm_row['Charge Description'].split('/RC STORAGE CONTRACT')[0]
                    elif 'RC STORAGE CONTRACT' in fdm_row['Charge Description']:
                        share_name = fdm_row['Charge Description'].split('/')[1].strip().split('RC STORAGE CONTRACT')[0].strip()
                    elif '/ RC STORAGE CONTRACT' in fdm_row['Charge Description']:
                        share_name = fdm_row['Charge Description'].split('/ RC STORAGE CONTRACT')[0].strip()
                    else:
                        share_name = fdm_row['Charge Description'].split('/')[1].split(' ')[0]
                else:
                    share_name = fdm_row['Charge Description'].split(' ')[0]

                if ',' in share_name:
                    share_name = share_name.split(',')[0]
                # print('{} : {}'.format(share_name, fdm_row['Charge Description']))

                share_name_fdm_lookup_dict[share_name.strip().lower()] = fdm_elements
                # print(share_name_fdm_lookup_dict[share_name]

        with open('/Users/ravichamakuri/UVAProjects/uvarc-unified-service/data/billing/rc-standard-storage-billing-not-found.csv', mode='r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for fdm_row in list(csv_reader):
                if fdm_row['Cost Center'] != '':
                    share_name_fdm_lookup_dict[fdm_row['Share Name'].strip().lower()] = [fdm_row['Company'], fdm_row['Business Unit'], fdm_row['Cost Center'], fdm_row['Fund'], fdm_row['Gift'], fdm_row['Grant'], fdm_row['Designated'], fdm_row['Project'], fdm_row['Program'], fdm_row['Function'], fdm_row['Activity'], fdm_row['Assignee'], '', '', '', '']

        with open('/Users/ravichamakuri/UVAProjects/uvarc-unified-service/data/billing/standard-share-name-out-new.csv', mode='r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for fdm_row in list(csv_reader):
                if fdm_row['Cost Center'] != '':
                    if ' - ' in fdm_row['Share Name'] and ' of ' in fdm_row['Share Name'].split(' - ')[1]:
                        share_name = fdm_row['Share Name'].split(' - ')[0].strip().lower()
                        fdm_index = fdm_row['Share Name'].split(' - ')[1].split(' of ')[0]
                        fdm_list_size = fdm_row['Share Name'].split(' - ')[1].split(' of ')[1].split(' ')[0]
                        if share_name not in self.__all_project_multi_fdm_dict:
                            self.__all_standard_multi_fdm_dict[share_name] = [[] for _ in range(int(fdm_list_size))]
                        self.__all_standard_multi_fdm_dict[share_name][int(fdm_index)-1] = [fdm_row['Company'], fdm_row['Business Unit'], fdm_row['Cost Center'], fdm_row['Fund'], fdm_row['Gift'], fdm_row['Grant'], fdm_row['Designated'], fdm_row['Project'], fdm_row['Program'], fdm_row['Function'], fdm_row['Activity'], fdm_row['Assignee'], '', '', '', '']
                    else:
                        share_name_fdm_lookup_dict[fdm_row['Share Name'].strip().lower()] = [fdm_row['Company'], fdm_row['Business Unit'], fdm_row['Cost Center'], fdm_row['Fund'], fdm_row['Gift'], fdm_row['Grant'], fdm_row['Designated'], fdm_row['Project'], fdm_row['Program'], fdm_row['Function'], fdm_row['Activity'], fdm_row['Assignee'], '', '', '', '']
        new_standard_storage_fdm_records = DynamoDbTableData((date.today().replace(day=1) - timedelta(days=1)).replace(day=1).strftime('%Y-%m'))
        for fdm_row in new_standard_storage_fdm_records.get_items_from_project_storage_requests_info_table():
            fdm_elements = [
                fdm_row['company'], 
                fdm_row['business_unit'], 
                fdm_row['cost_center'],
                fdm_row['fund'],
                fdm_row['gift'], 
                fdm_row['grant'],
                fdm_row['designated'],
                fdm_row['project'],
                fdm_row['program'],
                fdm_row['function'],
                fdm_row['activity'],
                fdm_row['assignee'],
                '',
                '',
                '',
                ''
            ]

            share_name_fdm_lookup_dict[fdm_row['share_name'].strip().lower()] = fdm_elements
            print('{} : {}'.format(fdm_row['share_name'].strip().lower(), fdm_row))

        return share_name_fdm_lookup_dict

    def __fetch_project_storage_fdm_details(self):
        share_name_fdm_lookup_dict = {}
        with open('/Users/ravichamakuri/UVAProjects/uvarc-unified-service/data/billing/project-share-name-out.csv', mode='r', encoding='utf-8') as csv_file:
            # csv_reader = csv.DictReader(csv_file)
            # for fdm_row in reversed(list(csv_reader)):
            #     fdm_elements = fdm_row['Expense GLA'].split('>')
            #     for index, raw_fdm_item in enumerate(fdm_elements):
            #         fdm_elements[index] = fdm_elements[index].strip()
            #     share_name = fdm_row['Share Name']
        # return share_name_fdm_lookup_dict
            csv_reader = csv.DictReader(csv_file)
            for fdm_row in reversed(list(csv_reader)):
                fdm_elements = fdm_row['Expense GLA'].split('>')
                for index, raw_fdm_item in enumerate(fdm_elements):
                    fdm_elements[index] = fdm_elements[index].strip()
                share_name = ''
                if 'TB ' in fdm_row['Charge Description']:
                    if 'research project storage' in fdm_row['Charge Description'].split('TB ')[1]:
                        parse_list = fdm_row['Charge Description'].split('TB ')[1].split('research project storage')[1].strip().split(' ')
                        share_name = parse_list[len(parse_list)-1] if 'TB' not in parse_list[len(parse_list)-1] else fdm_row['Charge Description'].split('research project storage ')[1].split(' ')[0]
                    else:
                        share_name = fdm_row['Charge Description'].split('TB ')[1].split(' ')[0]
                if share_name.strip().lower() == '':
                    print('{} : {}'.format(share_name, fdm_row['Charge Description']))
                else:
                    share_name_fdm_lookup_dict[share_name.strip().lower()] = fdm_elements
                # print(share_name_fdm_lookup_dict[share_name])

        with open('/Users/ravichamakuri/UVAProjects/uvarc-unified-service/data/billing/rc-project-storage-billing-not-found.csv', mode='r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for fdm_row in list(csv_reader):
                if fdm_row['Cost Center'] != '':
                    share_name_fdm_lookup_dict[fdm_row['Share Name'].strip().lower()] = [fdm_row['Company'], fdm_row['Business Unit'], fdm_row['Cost Center'], fdm_row['Fund'], fdm_row['Gift'], fdm_row['Grant'], fdm_row['Designated'], fdm_row['Project'], fdm_row['Program'], fdm_row['Function'], fdm_row['Activity'], fdm_row['Assignee'], '', '', '', '']

        with open('/Users/ravichamakuri/UVAProjects/uvarc-unified-service/data/billing/project-share-name-out-new.csv', mode='r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for fdm_row in list(csv_reader):
                if fdm_row['Cost Center'] != '':
                    if ' - ' in fdm_row['Share Name'] and ' of ' in fdm_row['Share Name'].split(' - ')[1]:
                        share_name = fdm_row['Share Name'].split(' - ')[0].strip().lower()
                        fdm_index = fdm_row['Share Name'].split(' - ')[1].split(' of ')[0]
                        fdm_list_size = fdm_row['Share Name'].split(' - ')[1].split(' of ')[1].split(' ')[0]
                        if share_name not in self.__all_project_multi_fdm_dict:
                            self.__all_project_multi_fdm_dict[share_name] = [[] for _ in range(int(fdm_list_size))]
                        self.__all_project_multi_fdm_dict[share_name][int(fdm_index)-1] = [fdm_row['Company'], fdm_row['Business Unit'], fdm_row['Cost Center'], fdm_row['Fund'], fdm_row['Gift'], fdm_row['Grant'], fdm_row['Designated'], fdm_row['Project'], fdm_row['Program'], fdm_row['Function'], fdm_row['Activity'], fdm_row['Assignee'], '', '', '', '']
                    else:
                        share_name_fdm_lookup_dict[fdm_row['Share Name'].strip().lower()] = [fdm_row['Company'], fdm_row['Business Unit'], fdm_row['Cost Center'], fdm_row['Fund'], fdm_row['Gift'], fdm_row['Grant'], fdm_row['Designated'], fdm_row['Project'], fdm_row['Program'], fdm_row['Function'], fdm_row['Activity'], fdm_row['Assignee'], '', '', '', '']

        new_project_storage_fdm_records = DynamoDbTableData((date.today().replace(day=1) - timedelta(days=1)).replace(day=1).strftime('%Y-%m'))
        for fdm_row in new_project_storage_fdm_records.get_items_from_project_storage_requests_info_table():
            fdm_elements = [
                fdm_row['company'], 
                fdm_row['business_unit'], 
                fdm_row['cost_center'],
                fdm_row['fund'],
                fdm_row['gift'], 
                fdm_row['grant'],
                fdm_row['designated'],
                fdm_row['project'],
                fdm_row['program'],
                fdm_row['function'],
                fdm_row['activity'],
                fdm_row['assignee'],
                '',
                '',
                '',
                ''
            ]

            share_name_fdm_lookup_dict[fdm_row['share_name'].strip().lower()] = fdm_elements
            print('{} : {}'.format(fdm_row['share_name'].strip().lower(), fdm_row))

        return share_name_fdm_lookup_dict

    def __percent_share_ratio(self, part, whole):
        return (part / whole)
    
    def generate_rc_standard_storage_billing(self):
        print('------------------------------------')
        print('Generating Standard Storage Billing: CEPH')
        print('------------------------------------')
        header_row = ('Date', 'Company', 'Business Unit', 'Cost Center', 'Fund', 'Gift', 'Grant', 'Designated', 'Project', 'Program', 'Function', 'Activity', 'Assignee', 'Internal Reference', 'Location', 'Loan', 'Region', 'Override Amt', 'Owner', 'Description')
        header_row_not_found = ('PI', 'Share Name', 'Company', 'Business Unit', 'Cost Center', 'Fund', 'Gift', 'Grant', 'Designated', 'Project', 'Program', 'Function', 'Activity', 'Assignee')
        data_row = [''] * len(header_row)
        data_row_not_found =  [''] * len(header_row_not_found)
        test_reporter_fp = open(
            '/Users/ravichamakuri/UVAProjects/uvarc-unified-service/data/rc-standard-storage-billing-'+datetime.now().strftime("%Y%m%d%H%M%S")+'.csv', 'w', newline='')
        test_reporter_fp_not_found = open(
            '/Users/ravichamakuri/UVAProjects/uvarc-unified-service/data/rc-standard-storage-billing-not-found'+datetime.now().strftime("%Y%m%d%H%M%S")+'.csv', 'w', newline='')
        try:
            report_writer = csv.writer(test_reporter_fp, delimiter=',', quotechar='"')
            report_writer.writerow(list(header_row))
            report_writer_not_found = csv.writer(test_reporter_fp_not_found, delimiter=',', quotechar='"')
            report_writer_not_found.writerow(list(header_row_not_found))
            free_space_max =10
            free_space = free_space_max
            pi_share_list = []
            pi_billing_row_list = []
            with open('/Users/ravichamakuri/UVAProjects/uvarc-unified-service/data/billing/rc-standard-storage-billing.csv', mode='r') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                for billing_row in csv_reader:
                    # print(billing_row)
                    if billing_row['Share Name'] != 'total':
                        pi_billing_row_list.append(billing_row)
                        # if billing_row['Share Name'] in self.__all_fdm_lookup_dict['standard_storage_fdm_info']:
                        #     if free_space > 0 and int(billing_row['Size']) > free_space:
                        #         description = "{pi}, {size} TB {project_name} /{share_name} research standard storage ({free_space} TB free+{billed_space} TB billed={total_space} TB total)".format(pi=billing_row['PI'], size=billing_row['Size'], project_name=billing_row['Project Name'], share_name=billing_row['Share Name'], free_space=free_space, billed_space=int(billing_row['Size']) - free_space, total_space=int(billing_row['Size']))
                        #         billing_row['Size'] = int(billing_row['Size']) - free_space
                        #         free_space = 0
                        #     else:
                        #         description = "{pi}, {size} TB {project_name} /{share_name} research standard storage".format(pi=billing_row['PI'], size=billing_row['Size'], project_name=billing_row['Project Name'], share_name=billing_row['Share Name'])
                        #     pi_share_list.append([datetime.now().strftime("%Y%m%d")] + self.__all_fdm_lookup_dict['standard_storage_fdm_info'][billing_row['Share Name']] + [int((float(billing_row['Size']) * 4500)/12)] + [' > '.join(self.__all_fdm_lookup_dict['standard_storage_fdm_info'][billing_row['Share Name']])] + [description])
                        # else:
                        #     print('{pi} FDM TAGS NOT FOUND FOR SHARE: {share_name}'.format(pi=billing_row['PI'], share_name=billing_row['Share Name']))
                    else:
                        if free_space != 0:
                            pi_share_list = []
                            for pi_billing_row in pi_billing_row_list:
                                # print(pi_billing_row)
                                billing_row_disscount_size = free_space_max * self.__percent_share_ratio(int(pi_billing_row['Size']), int(billing_row['Project Name']))
                                if pi_billing_row['Share Name'].strip().lower() in self.__all_fdm_lookup_dict['standard_storage_fdm_info'] and len(self.__all_fdm_lookup_dict['standard_storage_fdm_info'][pi_billing_row['Share Name'].lower()]) > 3:
                                    if free_space > 0:
                                        orginalsize = int(pi_billing_row['Size'])
                                        pi_billing_row['Size'] = int(pi_billing_row['Size']) - billing_row_disscount_size
                                        free_space = free_space - billing_row_disscount_size
                                        description = "{pi}, {size} TB {project_name} /{share_name} research standard storage ({free_space} TB free+{billed_space} TB billed={total_space} TB total)".format(pi=pi_billing_row['PI'], size=orginalsize, project_name=pi_billing_row['Project Name'], share_name=pi_billing_row['Share Name'], free_space=str(round(billing_row_disscount_size, 2)), billed_space=str(round(pi_billing_row['Size'], 2)), total_space=int(orginalsize))
                                        # print(description)
                                        # print('{orginalsize} : {disscount} : {billed_size} : {billed_ammt}'.format(orginalsize=orginalsize, disscount=billing_row_disscount_size, billed_size=pi_billing_row['Size'], billed_ammt=int((float(pi_billing_row['Size']) * 4500)/12)))
                                    else:
                                        description = "{pi}, {size} TB {project_name} /{share_name} research standard storage".format(pi=pi_billing_row['PI'], size=pi_billing_row['Size'], project_name=pi_billing_row['Project Name'], share_name=pi_billing_row['Share Name'])
                                    today = datetime.now()
                                    bill_date = (today - timedelta(days=today.day)).replace(day=1)
                                    # print(self.__all_fdm_lookup_dict['standard_storage_fdm_info'][pi_billing_row['Share Name'].lower()][2])
                                    pi_share_list.append([bill_date.strftime("%d-%b-%y")] + self.__all_fdm_lookup_dict['standard_storage_fdm_info'][pi_billing_row['Share Name'].lower()] + [int((float(pi_billing_row['Size']) * 4500)/12)] + [self.__all_fdm_lookup_dict['standard_storage_fdm_info'][pi_billing_row['Share Name'].lower()][2]] + [description])
                                else:
                                    print('{pi} FDM TAGS NOT FOUND FOR SHARE: {share_name}'.format(pi=pi_billing_row['PI'], share_name=pi_billing_row['Share Name']))
                                    data_row_not_found[0] = pi_billing_row['PI']
                                    data_row_not_found[1] = pi_billing_row['Share Name']
                                    report_writer_not_found.writerow(data_row_not_found)
                                    data_row_not_found = [''] * len(header_row_not_found)
                                    
                            # print(pi_share_list)

                            # print('{pi} FAILED TO APPLY DISSCOUNT'.format(pi=billing_row['PI']))

                        for bill_row in pi_share_list:
                            report_writer.writerow(bill_row)
                        free_space = free_space_max
                        pi_billing_row_list = []
                        pi_share_list = []
        finally:
            test_reporter_fp.close()
            print('------------------------------------')

    def generate_rc_project_storage_billing(self):
        print('------------------------------------')
        print('Generating Project Storage Billing: GPFS')
        print('------------------------------------')
        header_row = ('Date', 'Company', 'Business Unit', 'Cost Center', 'Fund', 'Gift', 'Grant', 'Designated', 'Project', 'Program', 'Function', 'Activity', 'Assignee', 'Internal Reference', 'Location', 'Loan', 'Region', 'Override Amt', 'Owner', 'Description')
        header_row_not_found = ('PI', 'Share Name', 'Company', 'Business Unit', 'Cost Center', 'Fund', 'Gift', 'Grant', 'Designated', 'Project', 'Program', 'Function', 'Activity', 'Assignee')
        data_row = [''] * len(header_row)
        data_row_not_found =  [''] * len(header_row_not_found)
        test_reporter_fp = open(
            '/Users/ravichamakuri/UVAProjects/uvarc-unified-service/data/rc-project-storage-billing-'+datetime.now().strftime("%Y%m%d%H%M%S")+'.csv', 'w', newline='')
        test_reporter_fp_not_found = open(
            '/Users/ravichamakuri/UVAProjects/uvarc-unified-service/data/rc-project-storage-billing-not-found'+datetime.now().strftime("%Y%m%d%H%M%S")+'.csv', 'w', newline='')
        try:
            report_writer = csv.writer(test_reporter_fp, delimiter=',', quotechar='"')
            report_writer.writerow(list(header_row))
            report_writer_not_found = csv.writer(test_reporter_fp_not_found, delimiter=',', quotechar='"')
            report_writer_not_found.writerow(list(header_row_not_found))
            with open('/Users/ravichamakuri/UVAProjects/uvarc-unified-service/data/billing/rc-project-storage-billing.csv', mode='r') as csv_file:
                csv_reader = csv.DictReader(f=csv_file, delimiter=':')
                for billing_row in csv_reader:
                    # print(billing_row)
                    if billing_row['vol name'].strip().lower() in self.__all_project_multi_fdm_dict:
                        multi_fdm_list = self.__all_project_multi_fdm_dict[billing_row['vol name'].strip().lower()]
                        total_size = billing_row['size'].split('TB')[0].strip()
                        size = int(float(total_size)/len(multi_fdm_list))
                        index = 1
                        for fdm_list in multi_fdm_list:
                            description = "{pi}, {size} TB {project_name} /{share_name} research project storage - {index} of {fdm_list_len} partial pymt for {total_size}TB".format(pi=billing_row['owner'], size=str(size), project_name=billing_row['group'], share_name=billing_row['vol name'], index=index, fdm_list_len=len(multi_fdm_list), total_size=total_size)
                            today = datetime.now()
                            bill_date = (today - timedelta(days=today.day)).replace(day=1)
                            report_writer.writerow([bill_date.strftime("%d-%b-%y")] + fdm_list + [int((float(size) * 7000)/12)] + [fdm_list[2]] + [description])
                            index = index + 1
                    elif billing_row['vol name'].strip().lower() in self.__all_fdm_lookup_dict['project_storage_fdms_info'] and  len(self.__all_fdm_lookup_dict['project_storage_fdms_info'][billing_row['vol name'].lower()]) > 3:
                        size = billing_row['size'].split('TB')[0].strip()
                        description = "{pi}, {size} TB {project_name} /{share_name} research project storage".format(pi=billing_row['owner'], size=size, project_name=billing_row['group'], share_name=billing_row['vol name'])
                        today = datetime.now()
                        bill_date = (today - timedelta(days=today.day)).replace(day=1)
                        report_writer.writerow([bill_date.strftime("%d-%b-%y")] + self.__all_fdm_lookup_dict['project_storage_fdms_info'][billing_row['vol name'].lower()] + [int((float(size) * 7000)/12)] + [self.__all_fdm_lookup_dict['project_storage_fdms_info'][billing_row['vol name'].lower()][2]] + [description])
                        # print('found')
                    else:
                        print('{pi} FDM TAGS NOT FOUND FOR SHARE: {share_name}'.format(pi=billing_row['owner'], share_name=billing_row['vol name']))
                        data_row_not_found[0] = billing_row['owner']
                        data_row_not_found[1] = billing_row['vol name']
                        report_writer_not_found.writerow(data_row_not_found)
                        data_row_not_found = [''] * len(header_row_not_found)
        finally:
            test_reporter_fp.close()
            print('------------------------------------')

    def generate_rc_paid_su_ssz_billing(self):
        print('------------------------------------')
        print('Generating Paid SU SSZ Billing:')
        print('------------------------------------')
        header_row = ('Date', 'Company', 'Business Unit', 'Cost Center', 'Fund', 'Gift', 'Grant', 'Designated', 'Project', 'Program', 'Function', 'Activity', 'Assignee', 'Internal Reference', 'Location', 'Loan', 'Region', 'Override Amt', 'Owner', 'Description')
        test_reporter_fp = open(
            '/Users/ravichamakuri/UVAProjects/uvarc-unified-service/data/rc-ssz-paid-su-billing-'+datetime.now().strftime("%Y%m%d%H%M%S")+'.csv', 'w', newline='')
        try:
            report_writer = csv.writer(test_reporter_fp, delimiter=',', quotechar='"')
            report_writer.writerow(list(header_row))
            today = datetime.now()
            bill_date = (today - timedelta(days=today.day)).replace(day=1)
            new_paid_su_fdm_records = DynamoDbTableData((date.today().replace(day=1) - timedelta(days=1)).replace(day=1).strftime('%Y-%m'))
            for fdm_row in new_paid_su_fdm_records.get_items_from_paid_su_requests_info_table():
                print(fdm_row)
                report_writer.writerow( 
                    [
                        bill_date.strftime("%d-%b-%y"),
                        fdm_row['company'], 
                        fdm_row['business_unit'], 
                        fdm_row['cost_center'],
                        fdm_row['fund'],
                        fdm_row['gift'], 
                        fdm_row['grant'],
                        fdm_row['designated'],
                        fdm_row['project'],
                        fdm_row['program'],
                        fdm_row['function'],
                        fdm_row['activity'],
                        fdm_row['assignee'],
                        '',
                        '',
                        '',
                        '',
                        int(fdm_row['bill_amount'])*100,
                        fdm_row['cost_center'],
                        '{} RC Rivanna SUs {}'.format(fdm_row['owner_uid'], fdm_row['allocation_name'])
                    ]
                )

                # share_name_fdm_lookup_dict[fdm_row['share_name'].strip().lower()] = fdm_elements
                # print('{} : {}'.format(fdm_row['share_name'].strip().lower(), fdm_row))
                # RC Rivanna SUs collabrobogroup_paid
        
        finally:
            test_reporter_fp.close()
            print('------------------------------------')

def main():
    try:
        legacyRCBillingHandler = LegacyRCBillingHandler()
        legacyRCBillingHandler.generate_rc_standard_storage_billing()
        legacyRCBillingHandler.generate_rc_project_storage_billing()
        legacyRCBillingHandler.generate_rc_paid_su_ssz_billing()
    except Exception as ex:
        raise ex


if __name__ == "__main__":
    main()
