import json
import boto3
import os
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients
s3_client = boto3.client('s3')
lambda_client = boto3.client('lambda')
dynamodb = boto3.resource('dynamodb')

# Get environment variables
S3_BUCKET = os.environ['S3_BUCKET']
ATTACHMENTS_TABLE = os.environ['ATTACHMENTS_TABLE']

def handler(event, context):
    """
    GraphQL resolver for triggerS3Monitor mutation
    Scans S3 bucket for new files and triggers processing
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Get the attachments table
        table = dynamodb.Table(ATTACHMENTS_TABLE)
        
        # Get existing files from DynamoDB
        response = table.scan(ProjectionExpression='filename')
        existing_files = set()
        for item in response.get('Items', []):
            if 'filename' in item:
                existing_files.add(item['filename'])
        
        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                ProjectionExpression='filename',
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            for item in response.get('Items', []):
                if 'filename' in item:
                    existing_files.add(item['filename'])
        
        logger.info(f"Found {len(existing_files)} existing files in database")
        
        # List all PDF files in S3 bucket
        s3_response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix='',  # No prefix to get all files
        )
        
        s3_files = []
        if 'Contents' in s3_response:
            for obj in s3_response['Contents']:
                key = obj['Key']
                # Only process PDF files
                if key.lower().endswith('.pdf'):
                    s3_files.append(key)
        
        # Handle pagination for S3 listing
        while s3_response.get('IsTruncated', False):
            s3_response = s3_client.list_objects_v2(
                Bucket=S3_BUCKET,
                ContinuationToken=s3_response['NextContinuationToken']
            )
            if 'Contents' in s3_response:
                for obj in s3_response['Contents']:
                    key = obj['Key']
                    if key.lower().endswith('.pdf'):
                        s3_files.append(key)
        
        logger.info(f"Found {len(s3_files)} PDF files in S3 bucket")
        logger.info(f"S3 files: {s3_files}")
        logger.info(f"Existing files: {list(existing_files)}")
        
        # Find new files (in S3 but not in database)
        new_files = []
        for s3_file in s3_files:
            if s3_file not in existing_files:
                new_files.append(s3_file)
                logger.info(f"New file detected: {s3_file}")
            else:
                logger.info(f"File already exists: {s3_file}")
        
        logger.info(f"Found {len(new_files)} new files to process")
        
        # Process new files
        processed_files = []
        processor_function_name = f"resume-ranking-s3-processor"
        
        for file_key in new_files:
            try:
                # Create S3 event for the processor
                s3_event = {
                    'Records': [
                        {
                            'eventVersion': '2.1',
                            'eventSource': 'aws:s3',
                            'eventTime': datetime.now().isoformat() + 'Z',
                            'eventName': 'ObjectCreated:Put',
                            's3': {
                                'bucket': {
                                    'name': S3_BUCKET
                                },
                                'object': {
                                    'key': file_key
                                }
                            }
                        }
                    ]
                }
                
                # Invoke the processor function asynchronously
                lambda_client.invoke(
                    FunctionName=processor_function_name,
                    InvocationType='Event',  # Asynchronous invocation
                    Payload=json.dumps(s3_event)
                )
                
                processed_files.append(file_key)
                logger.info(f"Triggered processing for: {file_key}")
                
            except Exception as e:
                logger.error(f"Error processing file {file_key}: {str(e)}")
                continue
        
        # Return results
        result = {
            'success': True,
            'message': f'S3 monitoring completed. Found {len(new_files)} new files, triggered processing for {len(processed_files)} files.',
            'newFilesFound': len(new_files),
            'processedFiles': processed_files
        }
        
        logger.info(f"S3 monitoring result: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in triggerS3Monitor resolver: {str(e)}")
        return {
            'success': False,
            'message': f'Internal server error: {str(e)}',
            'newFilesFound': 0,
            'processedFiles': []
        }
