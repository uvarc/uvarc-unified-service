import csv
from datetime import datetime


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
                share_name_fdm_lookup_dict[fdm_row['Share Name']] = fdm_elements
                print(share_name_fdm_lookup_dict[fdm_row['Share Name']])
        return share_name_fdm_lookup_dict

    def __fetch_project_storage_fdm_details(self):
        share_name_fdm_lookup_dict = {}
        with open('/Users/ravichamakuri/UVAProjects/uvarc-unified-service/data/billing/project-share-name-out.csv', mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for fdm_row in reversed(list(csv_reader)):
                fdm_elements = fdm_row['Expense GLA'].split('>')
                for index, raw_fdm_item in enumerate(fdm_elements):
                    fdm_elements[index] = fdm_elements[index].strip()
                share_name_fdm_lookup_dict[fdm_row['Share Name']] = fdm_elements
                print(share_name_fdm_lookup_dict[fdm_row['Share Name']])

        return share_name_fdm_lookup_dict

    def generate_rc_standard_storage_billing(self):
        header_row = ('Date', 'Company', 'Business Unit', 'Cost Center', 'Fund', 'Gift', 'rant', 'Designated', 'Project', 'Program', 'Function', 'Activity', 'Assignee', 'Internal Reference', 'Location', 'Loan', 'Region', 'Override Amt', 'Owner', 'Description')
        data_row = [''] * len(header_row)
        test_reporter_fp = open(
            '/Users/ravichamakuri/UVAProjects/uvarc-unified-service/data/rc-standard-storage-billing-'+datetime.now().strftime("%Y%m%d%H%M%S")+'.csv', 'w', newline='')
        try: 
            report_writer = csv.writer(test_reporter_fp, delimiter=',',
                                    quotechar='"')
            report_writer.writerow(list(header_row))
            free_space = 10
            pi_share_list = []
            with open('/Users/ravichamakuri/UVAProjects/uvarc-unified-service/data/billing/rc-standard-storage-billing.csv', mode='r') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                for billing_row in csv_reader:
                    # print(billing_row)
                    if billing_row['Share Name'] != 'total':
                        if billing_row['Share Name'] in self.__all_fdm_lookup_dict['standard_storage_fdm_info']:
                            if free_space > 0 and int(billing_row['Size']) > free_space:
                                description = "{pi}, {size} TB {project_name} /{share_name} research standard storage ({free_space} TB free+{billed_space} TB billed={total_space} TB total)".format(pi=billing_row['PI'], size=billing_row['Size'], project_name=billing_row['Project Name'], share_name=billing_row['Share Name'], free_space=free_space, billed_space=int(billing_row['Size']) - free_space, total_space=int(billing_row['Size']))
                                billing_row['Size'] = int(billing_row['Size']) - free_space
                                free_space = 0
                            else:
                                description = "{pi}, {size} TB {project_name} /{share_name} research standard storage".format(pi=billing_row['PI'], size=billing_row['Size'], project_name=billing_row['Project Name'], share_name=billing_row['Share Name'])
                            pi_share_list.append([datetime.now().strftime("%Y%m%d")] + self.__all_fdm_lookup_dict['standard_storage_fdm_info'][billing_row['Share Name']] + [(int(billing_row['Size']) * 4500)/12] + [' > '.join(self.__all_fdm_lookup_dict['standard_storage_fdm_info'][billing_row['Share Name']])] + [description])
                        else:
                            print('{pi} FDM TAGS NOT FOUND FOR SHARE: {share_name}'.format(pi=billing_row['PI'], share_name=billing_row['Share Name']))
                    else:
                        if free_space is not 0:
                            print('{pi} FAILED TO APPLY DISSCOUNT'.format(pi=billing_row['PI']))
                        for bill_row in pi_share_list:
                            report_writer.writerow(bill_row)
                        free_space = 10
                        pi_share_list = []
        finally:
            test_reporter_fp.close()


def main():
    try:
        legacyRCBillingHandler = LegacyRCBillingHandler()
        legacyRCBillingHandler.generate_rc_standard_storage_billing()
    except Exception as ex:
        raise ex


if __name__ == "__main__":
    main()