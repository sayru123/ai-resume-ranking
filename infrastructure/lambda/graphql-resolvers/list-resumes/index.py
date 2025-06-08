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
    GraphQL resolver for listResumes query
    Returns all resume attachments from DynamoDB
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Get the attachments table
        table = dynamodb.Table(ATTACHMENTS_TABLE)
        
        # Scan the table to get all attachments
        response = table.scan()
        items = response.get('Items', [])
        
        # Handle pagination if needed
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))
        
        # Process items and add download URLs
        processed_items = []
        for item in items:
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
            
            processed_items.append(item)
        
        # Sort by creation date (newest first)
        processed_items.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
        
        logger.info(f"Retrieved {len(processed_items)} attachments")
        
        return processed_items
        
    except Exception as e:
        logger.error(f"Error in listResumes resolver: {str(e)}")
        raise Exception(f"Error loading resumes: {str(e)}")
