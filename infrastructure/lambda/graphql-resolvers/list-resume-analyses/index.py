"""
GraphQL resolver for listing all resume analyses with legacy field mapping
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

def decimal_to_number(obj):
    """Convert Decimal objects to regular numbers for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj) if obj % 1 else int(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_number(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_number(v) for v in obj]
    return obj

def map_legacy_fields(item):
    """Map new optimized fields to legacy field names for backward compatibility"""
    # Create a copy to avoid modifying the original
    mapped_item = dict(item)
    
    # Map new fields to legacy field names that the frontend expects
    if 'top_strengths' in item:
        mapped_item['strengths'] = item['top_strengths']
    else:
        mapped_item['strengths'] = []
    
    if 'top_recommendations' in item:
        mapped_item['recommendations'] = item['top_recommendations']
    else:
        mapped_item['recommendations'] = []
    
    if 'key_skills' in item:
        mapped_item['skills'] = item['key_skills']
        mapped_item['keySkills'] = item['key_skills']
    else:
        mapped_item['skills'] = []
        mapped_item['keySkills'] = []
    
    # Map summary to detailed_summary for legacy compatibility
    if 'summary' in item:
        mapped_item['detailed_summary'] = item['summary']
    else:
        mapped_item['detailed_summary'] = ""
    
    if 'experience_years' in item:
        mapped_item['yearsOfExperience'] = item['experience_years']
        mapped_item['experienceYears'] = item['experience_years']
    
    # Map snake_case to camelCase for backward compatibility
    field_mappings = {
        'candidate_name': 'candidateName',
        'experience_level': 'experienceLevel', 
        'total_skills': 'totalSkills',
        'overall_score': 'overallScore',
        'skill_diversity': 'skillDiversity',
        'fit_assessment': 'fitAssessment',
        'extraction_confidence': 'extractionConfidence',
        'parsed_resume_id': 'parsedResumeId',
        'created_at': 'createdAt'
    }
    
    for snake_case, camel_case in field_mappings.items():
        if snake_case in item:
            mapped_item[camel_case] = item[snake_case]
    
    # Add default values for missing legacy fields
    if 'contactInfo' not in mapped_item:
        mapped_item['contactInfo'] = None
    
    # Ensure all required fields exist with defaults
    defaults = {
        'strengths': [],
        'recommendations': [],
        'skills': [],
        'keySkills': [],
        'detailed_summary': "",
        'key_achievements': [],
        'education': [],
        'certifications': [],
        'skill_breakdown': {},
        'yearsOfExperience': 0,
        'experienceYears': 0
    }
    
    for field, default_value in defaults.items():
        if field not in mapped_item:
            mapped_item[field] = default_value
    
    return mapped_item

def handler(event, context):
    """
    GraphQL resolver for listResumeAnalyses query
    Returns all AI analysis data with legacy field mapping
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Get all resume analyses from DynamoDB
        resume_info_table = dynamodb.Table(RESUME_INFORMATION_TABLE)
        
        response = resume_info_table.scan()
        items = response.get('Items', [])
        
        # Process items and map legacy fields
        analyses = []
        for item in items:
            # Convert Decimal objects to regular numbers
            item = decimal_to_number(item)
            
            # Map new fields to legacy field names
            mapped_item = map_legacy_fields(item)
            
            analyses.append(mapped_item)
        
        logger.info(f"Retrieved {len(analyses)} resume analyses")
        
        return analyses
        
    except Exception as e:
        logger.error(f"Error in listResumeAnalyses resolver: {str(e)}")
        raise Exception(f"Error loading resume analyses: {str(e)}")
