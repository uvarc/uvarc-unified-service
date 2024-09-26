import sys
import boto3
from botocore.config import Config
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def create_bucket(access_key, secret_key, bucket_name):
    session = boto3.session.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )

    # Object Gateway URL
    s3client = session.client(
        's3',
        endpoint_url='https://machi-nas-s.hpc.virginia.edu:7480',
        config=Config(),
        verify=False
    )
    # create [my-new-bucket]
    bucket = s3client.create_bucket(Bucket=bucket_name)
    print(bucket)
    buckets = s3client.list_buckets()
    print(buckets)


def main():
    args = sys.argv[1:]
    print("S3 access_key="+args[0])
    print("S3 secret_key="+args[1])
    print("Create Bucket Name="+args[1])
    create_bucket(args[0], args[1], args[2])


if __name__ == '__main__':
    main()
