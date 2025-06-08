import json
import boto3
import os
from datetime import datetime
import logging
from decimal import Decimal

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')

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
    GraphQL resolver for listRankedResumes query
    Returns resumes with AI analysis and ranking
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Get query arguments
        arguments = event.get('arguments', {})
        sort_by = arguments.get('sortBy', 'overallScore')  # Default sort by score
        filter_by = arguments.get('filterBy', 'all')
        
        # Get tables
        attachments_table = dynamodb.Table(ATTACHMENTS_TABLE)
        parsed_resumes_table = dynamodb.Table(PARSED_RESUMES_TABLE)
        resume_info_table = dynamodb.Table(RESUME_INFO_TABLE)
        
        # Get all attachments
        attachments_response = attachments_table.scan()
        attachments = attachments_response.get('Items', [])
        
        # Get all resume information with AI analysis
        resume_info_response = resume_info_table.scan()
        resume_infos = {item['parsed_resume_id']: item for item in resume_info_response.get('Items', [])}
        
        # Get all parsed resumes
        parsed_resumes_response = parsed_resumes_table.scan()
        parsed_resumes = {item['id']: item for item in parsed_resumes_response.get('Items', [])}
        
        ranked_resumes = []
        
        for attachment in attachments:
            # Find corresponding parsed resume
            parsed_resume = None
            for pr_id, pr in parsed_resumes.items():
                if pr.get('attachment_id') == attachment['id']:
                    parsed_resume = pr
                    break
            
            if not parsed_resume:
                # Create basic entry for unprocessed resume
                ranked_resumes.append({
                    'id': attachment['id'],
                    'filename': attachment.get('filename', 'Unknown'),
                    'candidateName': extract_name_from_filename(attachment.get('filename', '')),
                    'overallScore': 0,
                    'experienceLevel': 'ENTRY',
                    'experienceYears': 0,
                    'totalSkills': 0,
                    'fitAssessment': 'LOW',
                    'keySkills': [],
                    'createdAt': attachment.get('created_at', datetime.utcnow().isoformat()),
                    'processingStatus': 'UPLOADED',
                    'downloadUrl': f"https://{os.environ.get('S3_BUCKET', 'bucket')}.s3.amazonaws.com/{attachment.get('filename', '')}",
                    'rank': 999
                })
                continue
            
            # Get AI analysis
            resume_info = resume_infos.get(parsed_resume['id'])
            
            if resume_info:
                # Full AI analysis available
                ranked_resume = {
                    'id': attachment['id'],
                    'filename': attachment.get('filename', 'Unknown'),
                    'candidateName': resume_info.get('candidate_name', extract_name_from_filename(attachment.get('filename', ''))),
                    'overallScore': int(resume_info.get('overall_score', 0)),
                    'experienceLevel': map_experience_level(resume_info.get('experience_level', 'Entry')),
                    'experienceYears': int(resume_info.get('experience_years', 0)),
                    'totalSkills': int(resume_info.get('total_skills', 0)),
                    'fitAssessment': map_fit_assessment(resume_info.get('fit_assessment', 'Low')),
                    'keySkills': resume_info.get('key_skills', []),
                    'createdAt': attachment.get('created_at', datetime.utcnow().isoformat()),
                    'processingStatus': 'COMPLETED',
                    'downloadUrl': f"https://{os.environ.get('S3_BUCKET', 'bucket')}.s3.amazonaws.com/{attachment.get('filename', '')}",
                    'rank': 0  # Will be calculated after sorting
                }
            else:
                # Processed but no AI analysis
                ranked_resume = {
                    'id': attachment['id'],
                    'filename': attachment.get('filename', 'Unknown'),
                    'candidateName': extract_name_from_filename(attachment.get('filename', '')),
                    'overallScore': 25,
                    'experienceLevel': 'JUNIOR',
                    'experienceYears': 1,
                    'totalSkills': 1,
                    'fitAssessment': 'MEDIUM',
                    'keySkills': ['Technical Skills'],
                    'createdAt': attachment.get('created_at', datetime.utcnow().isoformat()),
                    'processingStatus': 'PROCESSING',
                    'downloadUrl': f"https://{os.environ.get('S3_BUCKET', 'bucket')}.s3.amazonaws.com/{attachment.get('filename', '')}",
                    'rank': 0
                }
            
            ranked_resumes.append(ranked_resume)
        
        # Apply filtering
        if filter_by != 'all':
            if filter_by == 'high_score':
                ranked_resumes = [r for r in ranked_resumes if r['overallScore'] >= 70]
            elif filter_by == 'senior':
                ranked_resumes = [r for r in ranked_resumes if r['experienceLevel'] in ['SENIOR', 'LEAD', 'EXECUTIVE']]
            elif filter_by == 'recent':
                # Filter last 30 days
                from datetime import datetime, timedelta
                cutoff = datetime.utcnow() - timedelta(days=30)
                ranked_resumes = [r for r in ranked_resumes if datetime.fromisoformat(r['createdAt'].replace('Z', '+00:00')) > cutoff]
        
        # Sort resumes
        if sort_by == 'overallScore':
            ranked_resumes.sort(key=lambda x: x['overallScore'], reverse=True)
        elif sort_by == 'experienceYears':
            ranked_resumes.sort(key=lambda x: x['experienceYears'], reverse=True)
        elif sort_by == 'totalSkills':
            ranked_resumes.sort(key=lambda x: x['totalSkills'], reverse=True)
        elif sort_by == 'createdAt':
            ranked_resumes.sort(key=lambda x: x['createdAt'], reverse=True)
        else:
            # Default: sort by overall score
            ranked_resumes.sort(key=lambda x: x['overallScore'], reverse=True)
        
        # Assign ranks
        for i, resume in enumerate(ranked_resumes):
            resume['rank'] = i + 1
        
        logger.info(f"Retrieved {len(ranked_resumes)} ranked resumes")
        
        return ranked_resumes
        
    except Exception as e:
        logger.error(f"Error in listRankedResumes resolver: {str(e)}")
        raise Exception(f"Error loading ranked resumes: {str(e)}")

def extract_name_from_filename(filename):
    """Extract candidate name from filename"""
    if not filename:
        return "Unknown Candidate"
    
    # Remove file extension and common prefixes
    clean_name = filename.replace('.pdf', '').replace('.docx', '').replace('.doc', '').replace('.txt', '')
    clean_name = clean_name.replace('Resume_', '').replace('CV_', '').replace('resume-', '').replace('cv-', '')
    clean_name = clean_name.replace('_', ' ').replace('-', ' ')
    
    # Remove years and numbers
    import re
    clean_name = re.sub(r'\d{4}', '', clean_name)
    clean_name = re.sub(r'\d+', '', clean_name)
    
    # Handle camelCase
    clean_name = re.sub(r'([a-z])([A-Z])', r'\1 \2', clean_name)
    
    clean_name = clean_name.strip().title()
    
    if len(clean_name.split()) >= 2:
        return clean_name
    
    return "Unknown Candidate"

def map_experience_level(level_str):
    """Map experience level string to enum"""
    level_map = {
        'entry': 'ENTRY',
        'entry-level': 'ENTRY',
        'junior': 'JUNIOR',
        'mid': 'MID',
        'mid-level': 'MID',
        'senior': 'SENIOR',
        'lead': 'LEAD',
        'executive': 'EXECUTIVE'
    }
    return level_map.get(level_str.lower(), 'JUNIOR')

def map_fit_assessment(fit_str):
    """Map fit assessment string to enum"""
    fit_map = {
        'low': 'LOW',
        'medium': 'MEDIUM',
        'high': 'HIGH',
        'excellent': 'EXCELLENT'
    }
    return fit_map.get(fit_str.lower(), 'MEDIUM')
