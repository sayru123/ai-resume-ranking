import json
import boto3
import os
from decimal import Decimal
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')

# Get table names from environment variables
ATTACHMENTS_TABLE = os.environ['ATTACHMENTS_TABLE']
S3_BUCKET = os.environ['S3_BUCKET']

def decimal_default(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def generate_presigned_url(s3_key):
    """Generate presigned URL for S3 object"""
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': s3_key},
            ExpiresIn=3600  # 1 hour
        )
        return url
    except Exception as e:
        logger.error(f"Error generating presigned URL: {str(e)}")
        return None

def handler(event, context):
    """
    GraphQL resolver for getResume query
    Returns a specific resume attachment by ID
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Extract the resume ID from the event
        arguments = event.get('arguments', {})
        resume_id = arguments.get('id')
        
        if not resume_id:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Bad Request',
                    'message': 'Resume ID is required'
                })
            }
        
        # Get the attachments table
        table = dynamodb.Table(ATTACHMENTS_TABLE)
        
        # Get the specific attachment
        response = table.get_item(Key={'id': resume_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'error': 'Not Found',
                    'message': f'Resume with ID {resume_id} not found'
                })
            }
        
        item = response['Item']
        
        # Generate presigned URL for download
        if 'filename' in item:
            download_url = generate_presigned_url(item['filename'])
            item['downloadUrl'] = download_url
        
        # Ensure processingStatus has a default value
        if 'processingStatus' not in item:
            item['processingStatus'] = 'UPLOADED'
        
        # Convert datetime strings to ISO format if needed
        if 'createdAt' in item and isinstance(item['createdAt'], str):
            try:
                # If it's already in ISO format, keep it
                datetime.fromisoformat(item['createdAt'].replace('Z', '+00:00'))
            except:
                # Convert to ISO format
                item['createdAt'] = datetime.now().isoformat() + 'Z'
        elif 'createdAt' not in item:
            item['createdAt'] = datetime.now().isoformat() + 'Z'
        
        logger.info(f"Retrieved attachment: {item['id']}")
        
        return item
        
    except Exception as e:
        logger.error(f"Error in getResume resolver: {str(e)}")
        raise Exception(f"Error loading resume: {str(e)}")
