import json
import boto3
import os
from datetime import datetime
import logging
from decimal import Decimal
from collections import Counter

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients
dynamodb = boto3.resource('dynamodb')
bedrock_client = boto3.client('bedrock')  # Fixed: use bedrock client for list_foundation_models

# Get environment variables
ATTACHMENTS_TABLE = os.environ['ATTACHMENTS_TABLE']
PARSED_RESUMES_TABLE = os.environ['PARSED_RESUMES_TABLE']
RESUME_INFO_TABLE = os.environ['RESUME_INFORMATION_TABLE']  # Fixed: use the correct env var name

def decimal_default(obj):
    """JSON serializer for Decimal objects"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def handler(event, context):
    """
    Enhanced GraphQL resolver for getSystemHealth query
    Returns comprehensive system analytics
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Get tables
        attachments_table = dynamodb.Table(ATTACHMENTS_TABLE)
        parsed_resumes_table = dynamodb.Table(PARSED_RESUMES_TABLE)
        resume_info_table = dynamodb.Table(RESUME_INFO_TABLE)
        
        # Get basic statistics
        stats = get_basic_statistics(attachments_table, parsed_resumes_table, resume_info_table)
        
        # Get advanced analytics
        analytics = get_advanced_analytics(resume_info_table)
        
        # Check system health
        overall_status = "HEALTHY"
        bedrock_status = "HEALTHY"
        database_status = "HEALTHY"
        
        try:
            # Test Bedrock connectivity
            bedrock_client.list_foundation_models()
            bedrock_status = "HEALTHY"
        except Exception as e:
            logger.warning(f"Bedrock health check failed: {str(e)}")
            bedrock_status = "DEGRADED"
            overall_status = "DEGRADED"
        
        # Determine overall health
        if stats['success_rate'] < 50:
            overall_status = "DEGRADED"
        elif stats['total_resumes'] == 0:
            overall_status = "IDLE"
        
        health_data = {
            'status': overall_status,
            'totalResumes': stats['total_resumes'],
            'processedResumes': stats['processed_resumes'],
            'successRate': stats['success_rate'],
            'lastProcessedAt': stats['last_processed_at'],
            'bedrockStatus': bedrock_status,
            'databaseStatus': database_status,
            
            # Enhanced Analytics
            'averageScore': analytics['average_score'],
            'topSkills': analytics['top_skills'],
            'experienceLevels': analytics['experience_levels']
        }
        
        logger.info(f"System health: {overall_status}, Total: {stats['total_resumes']}, Processed: {stats['processed_resumes']}")
        
        return health_data
        
    except Exception as e:
        logger.error(f"Error in getSystemHealth resolver: {str(e)}")
        raise Exception(f"Error loading system health: {str(e)}")

def get_basic_statistics(attachments_table, parsed_resumes_table, resume_info_table):
    """Get basic system statistics"""
    try:
        # Count total attachments
        attachments_response = attachments_table.scan(Select='COUNT')
        total_resumes = attachments_response.get('Count', 0)
        
        # Count processed resumes (with AI analysis)
        resume_info_response = resume_info_table.scan(Select='COUNT')
        processed_resumes = resume_info_response.get('Count', 0)
        
        # Calculate success rate
        success_rate = (processed_resumes / total_resumes * 100) if total_resumes > 0 else 0
        
        # Get last processed timestamp
        last_processed_at = None
        if processed_resumes > 0:
            try:
                recent_response = resume_info_table.scan(
                    Limit=1,
                    ScanFilter={
                        'created_at': {
                            'AttributeValueList': [datetime.utcnow().isoformat()],
                            'ComparisonOperator': 'LT'
                        }
                    }
                )
                if recent_response.get('Items'):
                    last_processed_at = recent_response['Items'][0].get('created_at')
            except Exception as e:
                logger.warning(f"Could not get last processed time: {str(e)}")
                last_processed_at = datetime.utcnow().isoformat()
        
        return {
            'total_resumes': total_resumes,
            'processed_resumes': processed_resumes,
            'success_rate': success_rate,
            'last_processed_at': last_processed_at
        }
        
    except Exception as e:
        logger.error(f"Error getting basic statistics: {str(e)}")
        return {
            'total_resumes': 0,
            'processed_resumes': 0,
            'success_rate': 0,
            'last_processed_at': None
        }

def get_advanced_analytics(resume_info_table):
    """Get advanced analytics from AI analysis data"""
    try:
        # Get all resume information
        response = resume_info_table.scan()
        resume_infos = response.get('Items', [])
        
        if not resume_infos:
            return {
                'average_score': 0.0,
                'top_skills': [],
                'experience_levels': {
                    'Junior': 0,
                    'Mid': 0,
                    'Senior': 0,
                    'Lead': 0,
                    'Executive': 0
                }
            }
        
        # Calculate average score
        scores = []
        all_skills = []
        experience_levels = Counter()
        
        for resume_info in resume_infos:
            # Overall score
            score = resume_info.get('overall_score', 0)
            if isinstance(score, (int, float, Decimal)):
                scores.append(float(score))
            
            # Skills
            key_skills = resume_info.get('key_skills', [])
            if isinstance(key_skills, list):
                all_skills.extend([skill.lower() for skill in key_skills if isinstance(skill, str)])
            
            # Experience levels
            exp_level = resume_info.get('experience_level', '').lower()
            if 'senior' in exp_level:
                experience_levels['Senior'] += 1
            elif 'lead' in exp_level or 'principal' in exp_level:
                experience_levels['Lead'] += 1
            elif 'executive' in exp_level or 'director' in exp_level or 'vp' in exp_level:
                experience_levels['Executive'] += 1
            elif 'mid' in exp_level:
                experience_levels['Mid'] += 1
            else:
                experience_levels['Junior'] += 1
        
        # Calculate average score
        average_score = sum(scores) / len(scores) if scores else 0.0
        
        # Get top skills
        skill_counts = Counter(all_skills)
        top_skills = [skill.title() for skill, count in skill_counts.most_common(10)]
        
        return {
            'average_score': round(average_score, 1),
            'top_skills': top_skills,
            'experience_levels': {
                'Junior': experience_levels.get('Junior', 0),
                'Mid': experience_levels.get('Mid', 0),
                'Senior': experience_levels.get('Senior', 0),
                'Lead': experience_levels.get('Lead', 0),
                'Executive': experience_levels.get('Executive', 0)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting advanced analytics: {str(e)}")
        return {
            'average_score': 0.0,
            'top_skills': [],
            'experience_levels': {
                'Junior': 0,
                'Mid': 0,
                'Senior': 0,
                'Lead': 0,
                'Executive': 0
            }
        }
