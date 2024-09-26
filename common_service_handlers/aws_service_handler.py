import boto3
import json
from app.api import DecimalEncoder


class AWSServiceHandler:
    def __init__(self, app):
        self.app = app
        self.aws_access_key_id = app.config['AWS_CONN_INFO']['CLIENT_ID']
        self.aws_secret_access_key = app.config['AWS_CONN_INFO']['CLIENT_SECRET']

    def get_dynamodb_resource(self):
        try:
            return boto3.Session(
                aws_access_key_id=self.aws_access_key_id, 
                aws_secret_access_key=self.aws_secret_access_key, 
                region_name='us-east-1'
            ).resource('dynamodb')
        except Exception as ex:
            self.app.log_exception(ex)
            print(str(ex))
            raise ex
        
    def update_dynamodb_jira_tracking(self, jira_issue_key, create_date, username, email, desc):
        try:
            dynamodb_session = boto3.Session(
                aws_access_key_id=self.aws_access_key_id, 
                aws_secret_access_key=self.aws_secret_access_key, 
                region_name='us-east-1'
            )
            dynamodb = dynamodb_session.resource('dynamodb')
            table = dynamodb.Table('jira-tracking')

            response = table.put_item(
                Item={
                    'key': jira_issue_key,
                    'submitted': create_date,
                    'uid': username,
                    'email': email,
                    'type': desc
                }
            )
            self.app.logger.info(json.dumps(response, indent=4, cls=DecimalEncoder))
            print(json.dumps(response, indent=4, cls=DecimalEncoder))
        except Exception as ex:
            self.app.log_exception(ex)
            print(str(ex))