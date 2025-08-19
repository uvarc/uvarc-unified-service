import requests
import zipfile
import io
import pandas as pd

class QualtricsServiceHandler:
    def __init__(self, app):
        self._connect_host_url, self._api_token = self.__get_qualtrics_host_info(app)

    def __get_qualtrics_host_info(self, app):
        return 'https://{}:{}/API/v3/'.format(
            app.config['QUALTRICS_CONN_INFO']['HOST'],
            app.config['QUALTRICS_CONN_INFO']['PORT']
        ), app.config['QUALTRICS_CONN_INFO']['PASSWORD']

    def get_survey(self, survey_id):
        try:
            base_url = f"{self._connect_host_url}surveys/{survey_id}/export-responses/"
            headers = {
                "X-API-TOKEN": self._api_token,
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            r = requests.post(
                url=base_url,
                headers=headers,
                json={"format": "csv", "useLabels": True, "breakoutSets": False}
            )
            progress_id = r.json()["result"]["progressId"]

            progress_status = "inProgress"
            while progress_status != "complete" and progress_status != "failed":
                response = requests.get(base_url + progress_id, headers=headers)
                res = response.json()["result"]
                progress_status = res["status"]
            
            if progress_status == "failed":
                raise Exception("Export failed. Check your API token and survey ID.")
            
            r = requests.get(f"{base_url}{res['fileId']}/file", headers=headers, stream=True)

            zip_file = zipfile.ZipFile(io.BytesIO(r.content))
            if len(zip_file.namelist()) != 1:
                raise Exception("Expected exactly one file in the zip archive, found: " + str(len(zip_file.namelist())))

            csv_file = zip_file.read(zip_file.namelist()[0]).decode('utf-8')

            df = pd.read_csv(io.StringIO(csv_file))

            return df.iloc[2:], df.iloc[0], df.iloc[1]  # Return data, headers, and metadata
        except Exception as e:
            raise Exception(f"Error retrieving Qualtrics survey data: {str(e)}") from e
