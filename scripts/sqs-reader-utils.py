import os
import boto3


class SQSOperations:
    def __init__(self, aws_region, queue_url):
        self.aws_region = aws_region
        self.sqs = boto3.client('sqs', region_name=self.aws_region)
        self.queue_url = queue_url

    def receive_message(self):
        response = self.sqs.receive_message(
            QueueUrl=self.queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=2
        )
        messages = response.get("Messages", [])
        return messages[0] if messages else None

    def delete_message(self, message):
        self.sqs.delete_message(
            QueueUrl=self.queue_url,
            ReceiptHandle=message["ReceiptHandle"]
        )


if __name__ == '__main__':
    aws_region = os.environ.get('AWS_REGION')
    queue_url = os.environ.get('QUEUE_URL')
    sqs = SQSOperations(aws_region, queue_url)

    while True:
        message = sqs.receive_message()
        if not message:
            print(f"Queue is empty: {queue_url}")
            break
        print(f"Message Body: {message['Body']}")
        sqs.delete_message(message)
