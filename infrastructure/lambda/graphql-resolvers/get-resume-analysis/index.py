"""
GraphQL resolver for getting resume analysis data
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
RESUME_INFORMATION_TABLE = os.environ['RESUME_INFORMATION_TABLE']

def decimal_default(obj):
    """JSON serializer for Decimal objects"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def handler(event, context):
    """
    GraphQL resolver for getResumeAnalysis query
    Returns AI analysis data for a specific resume
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Get the resume ID from arguments
        resume_id = event.get('arguments', {}).get('resumeId')
        
        if not resume_id:
            raise Exception("Resume ID is required")
        
        # Get resume analysis from DynamoDB
        resume_info_table = dynamodb.Table(RESUME_INFORMATION_TABLE)
        
        # Query by parsed_resume_id (which links to attachment ID)
        response = resume_info_table.scan(
            FilterExpression='parsed_resume_id = :resume_id',
            ExpressionAttributeValues={':resume_id': resume_id}
        )
        
        items = response.get('Items', [])
        
        if not items:
            logger.warning(f"No analysis found for resume ID: {resume_id}")
            return None
        
        # Return the first matching analysis
        analysis = items[0]
        
        # Convert Decimal types to float for JSON serialization
        analysis_json = json.loads(json.dumps(analysis, default=decimal_default))
        
        logger.info(f"Retrieved analysis for resume: {resume_id}")
        
        return analysis_json
        
    except Exception as e:
        logger.error(f"Error in getResumeAnalysis resolver: {str(e)}")
        raise Exception(f"Error loading resume analysis: {str(e)}")
