from pymongo import MongoClient
from datetime import datetime, timedelta
from pathlib import Path
import csv

MONGO_URI = "mongodb://uvarc_unified_db_user_local:uvarc_unified_db_pass@localhost:27017/uvarc_unified_data_local"
DB_NAME = "uvarc_unified_data_local"
COLLECTION_NAME = "uvarc_groups"


class MongoDbTableDta:
    def __init__(self):
        try:
            self.client = MongoClient(MONGO_URI)
            self.db = self.client[DB_NAME]
            self.collection = self.db[COLLECTION_NAME]

            # Pull all groups once at init (cache in memory)
            self.all_groups = list(self.collection.find({}, {"_id": 0}))
            print(f"Loaded {len(self.all_groups)} groups at init")

            # Precompute active resources
            self.active_resources = self._get_all_active_resources()
            print(f"Cached {len(self.active_resources)} active resources")

        except Exception as ex:
            print(f"DB connection failed: {ex}")
            self.all_groups = []
            self.active_resources = []

    def _get_all_active_resources(self):
        active_resources = []
        for group in self.all_groups:
            resources = group.get("resources", {})
            
            for resource_type, resource_items in resources.items():
                for res_name, details in resource_items.items():
                    if details.get("request_status") == "active":
                        active_resources.append({
                            "group_name": group.get("group_name"),
                            "project_name": group.get("project_name"),
                            "pi_uid": group.get("pi_uid"),
                            "resource_type": resource_type,
                            "resource_name": res_name,
                            "details": details
                        })

        print(f"Found {len(active_resources)} active resources")
        return active_resources

    def get_resource_requests_for_billing(self, resource_type: str, request_name: str):
        try:
            results = [
               res for res in self.active_resources
               if res["resource_type"] == resource_type
               and res["details"].get("tier") == request_name
             ]
            print(f"Found {len(results)} active {resource_type} resources of type '{request_name}'")
            return results

        except Exception as ex:
            print(f"Error filtering resources: {ex}")
            return []


class BillingHandler:
    # Common billing CSV header for all reports
    BILLING_HEADER = (
        'Date', 'Company', 'Business Unit', 'Cost Center', 'Fund', 'Gift', 'Grant',
        'Designated', 'Project', 'Program', 'Function', 'Activity', 'Assignee',
        'Internal Reference', 'Location', 'Loan', 'Region', 'Override Amt',
        'Owner', 'Description'
    )

    def __init__(self, output_dir):
        try:
            self.output_dir = Path(output_dir)
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.data_fetcher = MongoDbTableDta()
        except Exception as e:
            print(f"[ERROR] Failed to initialize BillingHandler: {e}")

    @staticmethod
    def _write_csv(file_path, header, rows):
        try:
            with open(file_path, "w", newline="") as fp:
                writer = csv.writer(fp)
                writer.writerow(header)
                for row in rows:
                    writer.writerow(row)
            print(f"[INFO] Billing CSV generated at: {file_path}")
        except Exception as e:
            print(f"[ERROR] Failed to write CSV {file_path}: {e}")

    def _build_billing_rows(self, docs, bill_date, billing_type, yearly_rate=None):
        rows = []
        for doc in docs:
            try:
                pi_uid = doc.get('pi_uid', '')
                project_name = doc.get('project_name', '')
                resource_name = doc.get('resource_name', '')
                details = doc.get('details', {}) or {}
                billing_info = details.get('billing_details', {}).get('fdm_billing_info', []) or []
                if not billing_info:
                    continue

                # compute type-specific values
                if billing_type == "storage":
                    size_tb = float(details.get('request_size', 0) or 0)
                    override_amt = int((size_tb * yearly_rate) / 12)
                    description = f"{project_name}, {size_tb} TB / {resource_name.lower()}"

                elif billing_type == "paid_allocations":
                    su_count = float(details.get('request_count', 0) or 0)
                    override_amt = int(su_count * 100)
                    description = f"{project_name}, RC Rivanna SUs-{su_count}/{resource_name}"

                else:
                    raise ValueError(f"Unknown billing_type: {billing_type}")

                for fdm in billing_info:
                    row = [
                        bill_date.strftime("%d-%b-%y"),
                        fdm.get('company', ''),
                        fdm.get('business_unit', ''),
                        fdm.get('cost_center', ''),
                        fdm.get('fund', ''),
                        fdm.get('gift', ''),
                        fdm.get('grant', ''),
                        fdm.get('designated', ''),
                        fdm.get('project', ''),
                        fdm.get('program_code', ''),
                        fdm.get('function', ''),
                        fdm.get('activity', ''),
                        fdm.get('assignee', ''),
                        '', '', '', '',
                        override_amt,
                        pi_uid,
                        description
                    ]
                    rows.append(row)
            except Exception as inner:
                print(f"[WARN] Skipped a document: {inner}")
        return rows

    def generate_storage_billing(self, resource_type, request_name, yearly_rate):
        try:
            docs = self.data_fetcher.get_resource_requests_for_billing(resource_type, request_name)
            bill_date = datetime.now().replace(day=1)

            rows = self._build_billing_rows(docs, bill_date, billing_type="storage", yearly_rate=yearly_rate)

            file_path = self.output_dir / f"rc-{resource_type}-{request_name}-billing-{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
            self._write_csv(file_path, self.BILLING_HEADER, rows)

        except Exception as e:
            print(f"[ERROR] Failed to generate storage billing: {e}")

    def generate_paid_allocations_billing(self, resource_type, request_name):
        try:
            docs = self.data_fetcher.get_resource_requests_for_billing(resource_type, request_name)
            bill_date = datetime.now().replace(day=1)

            rows = self._build_billing_rows(docs, bill_date, billing_type="paid_allocations")

            file_path = self.output_dir / f"rc-paid-allocations-billing-{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
            self._write_csv(file_path, self.BILLING_HEADER, rows)

        except Exception as e:
            print(f"[ERROR] Failed to generate paid allocations billing: {e}")


if __name__ == "__main__":
    billing = BillingHandler("/Users/rajyalakshmivedhere/billing_data")
    billing.generate_storage_billing("storage", "ssz_project", 7000)
    billing.generate_storage_billing("storage", "hsz_standard", 4500)
    billing.generate_paid_allocations_billing("hpc_service_units", "ssz_paid")
