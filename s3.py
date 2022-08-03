import os, logging, boto3, awscli
from botocore.exceptions import ClientError

AWS_REGION = str(os.getenv('AWS_REGION'))
AWS_ACCESS_KEY_ID = str(os.getenv('AWS_ACCESS_KEY_ID'))
AWS_SECRET_ACCESS_KEY = str(os.getenv('AWS_SECRET_ACCESS_KEY'))

def list_all_files(bucket):

    s3_resource = boto3.resource(
                    's3', 
                    aws_access_key_id = AWS_ACCESS_KEY_ID,
                    aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
                    region_name=AWS_REGION)
    s3_bucket = s3_resource.Bucket(bucket)

    filenames = []
    for obj in s3_bucket.objects.all():
        filenames.append(obj.key)
    return filenames

def download_file(file_name, bucket, object_name):

    s3_client = boto3.client(
                    's3', 
                    aws_access_key_id = AWS_ACCESS_KEY_ID,
                    aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
                    region_name=AWS_REGION)
    try:
        s3_client.download_file(bucket, object_name, file_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def upload_file(file_name, bucket, object_name=None):

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    s3_client = boto3.client(
                    's3', 
                    aws_access_key_id = AWS_ACCESS_KEY_ID,
                    aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
                    region_name=AWS_REGION)

    # Search if the file already exists and eventually delete it
    s3_client.delete_object(Bucket=bucket, Key=file_name)

    # Upload the file
    try:
        s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True
