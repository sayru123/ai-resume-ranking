"""
Get Detailed Resume Analysis from S3
Retrieves full analysis data that's too large for DynamoDB
"""
import json
import boto3
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    """Get detailed analysis from S3"""
    try:
        logger.info(f"Get detailed analysis event: {json.dumps(event)}")
        
        # Extract resume information ID from the event
        resume_info_id = event.get('arguments', {}).get('id')
        if not resume_info_id:
            return {"error": "Resume information ID is required"}
        
        # Get the S3 key from DynamoDB
        table = dynamodb.Table('resume-ranking-resume-information')
        response = table.get_item(Key={'id': resume_info_id})
        
        if 'Item' not in response:
            return {"error": "Resume information not found"}
        
        item = response['Item']
        s3_key = item.get('detailed_analysis_s3_key')
        
        if not s3_key:
            return {"error": "Detailed analysis not available"}
        
        # Retrieve detailed analysis from S3
        bucket_name = os.environ.get('S3_BUCKET', 'resume-ranking-bucket')
        s3_response = s3_client.get_object(
            Bucket=bucket_name,
            Key=s3_key
        )
        
        detailed_analysis = json.loads(s3_response['Body'].read().decode('utf-8'))
        
        # Combine with basic info from DynamoDB
        result = {
            "id": item['id'],
            "candidate_name": item['candidate_name'],
            "overall_score": int(item['overall_score']),
            "experience_level": item['experience_level'],
            "experience_years": int(item['experience_years']),
            
            # Detailed data from S3
            "full_summary": detailed_analysis.get('full_summary', ''),
            "all_skills": detailed_analysis.get('all_skills', []),
            "detailed_achievements": detailed_analysis.get('detailed_achievements', []),
            "full_education": detailed_analysis.get('full_education', []),
            "all_certifications": detailed_analysis.get('all_certifications', []),
            "complete_strengths": detailed_analysis.get('complete_strengths', []),
            "detailed_recommendations": detailed_analysis.get('detailed_recommendations', []),
            "skill_breakdown": detailed_analysis.get('skill_breakdown', {})
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting detailed analysis: {str(e)}")
        return {"error": f"Failed to get detailed analysis: {str(e)}"}
