import json
import boto3
import os
import uuid
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients
s3_client = boto3.client('s3')
lambda_client = boto3.client('lambda')

# Get environment variables
S3_BUCKET = os.environ['S3_BUCKET']

def handler(event, context):
    """
    GraphQL resolver for processResume mutation
    Triggers processing of a specific resume file in S3
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Extract the S3 key from the event
        arguments = event.get('arguments', {})
        s3_key = arguments.get('s3Key')
        
        if not s3_key:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'message': 'S3 key is required',
                    'attachmentId': None
                })
            }
        
        # Check if the file exists in S3
        try:
            s3_client.head_object(Bucket=S3_BUCKET, Key=s3_key)
        except s3_client.exceptions.NoSuchKey:
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'success': False,
                    'message': f'File {s3_key} not found in S3 bucket {S3_BUCKET}',
                    'attachmentId': None
                })
            }
        
        # Create a mock S3 event to trigger the processor function
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
                            'key': s3_key
                        }
                    }
                }
            ]
        }
        
        # Get the S3 processor function name
        # This should match the function name created in the LambdaConstruct
        processor_function_name = f"resume-ranking-s3-processor"
        
        try:
            # Invoke the S3 processor function asynchronously
            response = lambda_client.invoke(
                FunctionName=processor_function_name,
                InvocationType='Event',  # Asynchronous invocation
                Payload=json.dumps(s3_event)
            )
            
            logger.info(f"Successfully triggered processing for {s3_key}")
            
            return {
                'success': True,
                'message': f'Processing started for {s3_key}',
                'attachmentId': str(uuid.uuid4())  # Generate a temporary ID
            }
            
        except Exception as e:
            logger.error(f"Error invoking processor function: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to start processing: {str(e)}',
                'attachmentId': None
            }
        
    except Exception as e:
        logger.error(f"Error in processResume resolver: {str(e)}")
        return {
            'success': False,
            'message': f'Internal server error: {str(e)}',
            'attachmentId': None
        }
