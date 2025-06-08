import json
import os
import boto3
import logging
import base64
from urllib.parse import unquote

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize S3 client
s3 = boto3.client('s3')
bucket_name = os.environ.get('S3_BUCKET')

def handler(event, context):
    """Lambda function to handle Postmark webhooks"""
    try:
        logger.info("Received webhook event")
        
        # Parse the webhook payload
        body = json.loads(event['body'])
        message_id = body.get('MessageID')
        
        # Process attachments
        attachments = body.get('Attachments', [])
        processed_files = []
        
        for attachment in attachments:
            # Check if it's likely a resume
            if _is_resume_file(attachment):
                # Generate unique filename
                filename = f"{message_id}/{attachment['Name']}"
                
                # Decode attachment content
                content = base64.b64decode(attachment['Content'])
                
                # Upload to S3
                s3.put_object(
                    Bucket=bucket_name,
                    Key=filename,
                    Body=content,
                    ContentType=attachment['ContentType']
                )
                
                processed_files.append(filename)
                logger.info(f"Uploaded file to S3: {filename}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Webhook processed successfully',
                'message_id': message_id,
                'processed_files': processed_files
            })
        }
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f'Error processing webhook: {str(e)}'
            })
        }

def _is_resume_file(attachment):
    """Check if the attachment is likely a resume"""
    name = attachment.get('Name', '').lower()
    content_type = attachment.get('ContentType', '').lower()
    
    # Check file extension
    resume_extensions = ['.pdf', '.docx', '.doc', '.txt', '.rtf']
    is_resume_ext = any(name.endswith(ext) for ext in resume_extensions)
    
    # Check content type
    resume_types = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/msword',
        'text/plain',
        'application/rtf'
    ]
    is_resume_type = content_type in resume_types
    
    # Check filename keywords
    resume_keywords = ['resume', 'cv', 'curriculum', 'vitae']
    has_resume_keyword = any(keyword in name for keyword in resume_keywords)
    
    return (is_resume_ext and is_resume_type) or has_resume_keyword