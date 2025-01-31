import csv
from datetime import datetime, timedelta


class LegacyRCBillingHandler:
    def __init__(self):
        self.__all_fdm_lookup_dict = {}
        self.__all_fdm_lookup_dict['standard_storage_fdm_info'] = self.__fetch_standard_storage_fdm_details()
        self.__all_fdm_lookup_dict['project_storage_fdms_info'] = self.__fetch_project_storage_fdm_details()

    def __fetch_standard_storage_fdm_details(self):
        share_name_fdm_lookup_dict = {}
        with open('/Users/ravichamakuri/UVAProjects/uvarc-unified-service/data/billing/standard-share-name-out.csv', mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for fdm_row in reversed(list(csv_reader)):
                fdm_elements = fdm_row['Expense GLA'].split('>')
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
                # print(share_name_fdm_lookup_dict[share_name])
        return share_name_fdm_lookup_dict

    def __fetch_project_storage_fdm_details(self):
        share_name_fdm_lookup_dict = {}
        with open('/Users/ravichamakuri/UVAProjects/uvarc-unified-service/data/billing/project-share-name-out.csv', mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for fdm_row in reversed(list(csv_reader)):
                fdm_elements = fdm_row['Expense GLA'].split('>')
                for index, raw_fdm_item in enumerate(fdm_elements):
                    fdm_elements[index] = fdm_elements[index].strip()
                share_name = fdm_row['Share Name']
        # return share_name_fdm_lookup_dict
            # csv_reader = csv.DictReader(csv_file)
            # for fdm_row in reversed(list(csv_reader)):
            #     fdm_elements = fdm_row['Expense GLA'].split('>')
            #     for index, raw_fdm_item in enumerate(fdm_elements):
            #         fdm_elements[index] = fdm_elements[index].strip()
            #     share_name = ''
            #     if 'TB ' in fdm_row['Charge Description']:
            #         if 'research project storage' in fdm_row['Charge Description'].split('TB ')[1]:
            #             parse_list = fdm_row['Charge Description'].split('TB ')[1].split('research project storage')[1].strip().split(' ')
            #             share_name = parse_list[len(parse_list)-1]
            #         else:
            #             share_name = fdm_row['Charge Description'].split('TB ')[1].split(' ')[0]
                # print('{} : {}'.format(share_name, fdm_row['Charge Description']))

                share_name_fdm_lookup_dict[share_name.strip().lower()] = fdm_elements
                # print(share_name_fdm_lookup_dict[share_name])
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
                                        description = "{pi}, {size} TB {project_name} /{share_name} research standard storage ({free_space} TB free+{billed_space} TB billed={total_space} TB total)".format(pi=pi_billing_row['PI'], size=orginalsize, project_name=pi_billing_row['Project Name'], share_name=pi_billing_row['Share Name'], free_space=billing_row_disscount_size, billed_space=pi_billing_row['Size'], total_space=int(orginalsize))
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
                                    data_row_not_found =  [''] * len(header_row_not_found)
                                    
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
                    if billing_row['vol name'].strip().lower() in self.__all_fdm_lookup_dict['project_storage_fdms_info'] and  len(self.__all_fdm_lookup_dict['project_storage_fdms_info'][billing_row['vol name'].lower()]) > 3:
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
                        data_row_not_found =  [''] * len(header_row_not_found)
        finally:
            test_reporter_fp.close()
            print('------------------------------------')


def main():
    try:
        legacyRCBillingHandler = LegacyRCBillingHandler()
        legacyRCBillingHandler.generate_rc_standard_storage_billing()
        legacyRCBillingHandler.generate_rc_project_storage_billing()
    except Exception as ex:
        raise ex


if __name__ == "__main__":
    main()