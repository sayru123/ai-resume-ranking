"""
GraphQL resolver for listing all parsed resumes
"""
import json
import boto3
import logging
import os
from decimal import Decimal

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients
dynamodb = boto3.resource('dynamodb')

# Get environment variables
PARSED_RESUMES_TABLE = os.environ['PARSED_RESUMES_TABLE']

def decimal_to_number(obj):
    """Convert Decimal objects to regular numbers for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj) if obj % 1 else int(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_number(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_number(v) for v in obj]
    return obj

def handler(event, context):
    """
    GraphQL resolver for listParsedResumes query
    Returns all parsed resume records
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Get table
        table = dynamodb.Table(PARSED_RESUMES_TABLE)
        
        # Scan all items
        response = table.scan()
        items = response.get('Items', [])
        
        # Process items
        processed_items = []
        for item in items:
            # Convert Decimal objects to regular numbers
            item = decimal_to_number(item)
            
            # Ensure both camelCase and snake_case fields for compatibility
            processed_item = dict(item)
            
            # Add camelCase versions
            if 'attachment_id' in item:
                processed_item['attachmentId'] = item['attachment_id']
            if 'parsing_status' in item:
                processed_item['parsingStatus'] = item['parsing_status']
            if 'created_at' in item:
                processed_item['createdAt'] = item['created_at']
            
            # Add snake_case versions (in case they're missing)
            if 'attachmentId' in item and 'attachment_id' not in processed_item:
                processed_item['attachment_id'] = item['attachmentId']
            if 'parsingStatus' in item and 'parsing_status' not in processed_item:
                processed_item['parsing_status'] = item['parsingStatus']
            if 'createdAt' in item and 'created_at' not in processed_item:
                processed_item['created_at'] = item['createdAt']
            
            processed_items.append(processed_item)
        
        logger.info(f"Returning {len(processed_items)} parsed resumes")
        return processed_items
        
    except Exception as e:
        logger.error(f"Error in listParsedResumes: {str(e)}")
        raise e
