"""
S3 Resume Processor with REAL PDF Extraction and AI Analysis using Amazon Bedrock Nova Premier
"""
import json
import boto3
import logging
import uuid
import os
import re
from datetime import datetime
from decimal import Decimal
import io

# Configure logging FIRST
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
lambda_client = boto3.client('lambda')

# PDF and document processing
try:
    import PyPDF2
    PDF_AVAILABLE = True
    logger.info("PyPDF2 imported successfully")
except ImportError as e:
    logger.error(f"PyPDF2 import failed: {str(e)}")
    PDF_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
    logger.info("python-docx imported successfully")
except ImportError as e:
    logger.error(f"python-docx import failed: {str(e)}")
    DOCX_AVAILABLE = False

# Initialize AWS clients
bedrock_client = boto3.client('bedrock-runtime')
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Get environment variables
S3_BUCKET = os.environ['S3_BUCKET']
ATTACHMENTS_TABLE = os.environ['ATTACHMENTS_TABLE']
PARSED_RESUMES_TABLE = os.environ['PARSED_RESUMES_TABLE']
RESUME_INFORMATION_TABLE = os.environ['RESUME_INFORMATION_TABLE']

def trigger_email_notification(resume_info_id):
    """Trigger email notification asynchronously via Lambda"""
    try:
        email_lambda_name = os.environ.get('EMAIL_NOTIFIER_FUNCTION_NAME', 'resume-ranking-email-notifier')
        
        payload = {
            'resume_info_id': resume_info_id
        }
        
        # Invoke email notification lambda asynchronously
        lambda_client.invoke(
            FunctionName=email_lambda_name,
            InvocationType='Event',  # Asynchronous invocation
            Payload=json.dumps(payload)
        )
        
        logger.info(f"Email notification triggered for resume: {resume_info_id}")
        
    except Exception as e:
        logger.warning(f"Failed to trigger email notification: {str(e)}")
        # Don't raise exception - email failure shouldn't break main flow

def handler(event, context):
    """Process S3 resume upload events with REAL AI analysis"""
    try:
        logger.info(f"Processing S3 event: {json.dumps(event)}")
        
        for record in event.get('Records', []):
            if record.get('eventSource') == 'aws:s3':
                bucket = record['s3']['bucket']['name']
                key = record['s3']['object']['key']
                
                logger.info(f"Processing file: {key} from bucket: {bucket}")
                result = process_resume_file(bucket, key)
                logger.info(f"Processing result: {result}")
        
        return {"statusCode": 200, "body": "Processing completed"}
        
    except Exception as e:
        logger.error(f"Error in S3 processor: {str(e)}")
        return {"statusCode": 500, "body": f"Error: {str(e)}"}

def process_resume_file(bucket, key):
    """Process individual resume file with REAL PDF extraction"""
    try:
        filename = key.split('/')[-1]
        
        # Skip non-resume files
        if not filename.lower().endswith(('.pdf', '.docx', '.doc', '.txt')):
            return {"status": "skipped", "reason": "not a resume file"}
        
        # Download file
        response = s3_client.get_object(Bucket=bucket, Key=key)
        file_content = response['Body'].read()
        content_type = response.get('ContentType', 'application/octet-stream')
        
        logger.info(f"Downloaded file: {filename}, size: {len(file_content)} bytes")
        
        # REAL TEXT EXTRACTION
        raw_text = extract_text_from_file(file_content, filename, content_type)
        logger.info(f"Extracted text length: {len(raw_text)} characters")
        logger.info(f"Text preview: {raw_text[:200]}...")
        
        if len(raw_text.strip()) < 50:
            logger.warning(f"Extracted text too short: {len(raw_text)} chars")
            raw_text = f"Unable to extract meaningful text from {filename}. File may be corrupted or in unsupported format."
        
        # Create attachment record
        attachments_table = dynamodb.Table(ATTACHMENTS_TABLE)
        attachment_id = str(uuid.uuid4())
        attachment = {
            'id': attachment_id,
            'filename': filename,
            'contentType': content_type,
            'size': len(file_content),
            'createdAt': datetime.utcnow().isoformat() + 'Z',
            'processingStatus': 'PROCESSING'
        }
        attachments_table.put_item(Item=attachment)
        
        # Store raw text in S3 instead of DynamoDB to avoid 400KB limit
        parsed_resume_id = str(uuid.uuid4())
        raw_text_s3_key = f"parsed-resumes/{parsed_resume_id}.txt"
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=raw_text_s3_key,
            Body=raw_text.encode('utf-8'),
            ContentType='text/plain'
        )
        
        # Create parsed resume record with S3 reference (not full text)
        parsed_resumes_table = dynamodb.Table(PARSED_RESUMES_TABLE)
        parsed_resume = {
            'id': parsed_resume_id,
            'attachment_id': attachment_id,
            'raw_text_s3_key': raw_text_s3_key,  # S3 reference instead of full text
            'text_length': len(raw_text),
            'text_preview': raw_text[:500] + "..." if len(raw_text) > 500 else raw_text,  # Preview only
            'parsing_status': 'completed',
            'created_at': datetime.utcnow().isoformat() + 'Z'
        }
        parsed_resumes_table.put_item(Item=parsed_resume)
        
        # REAL AI Analysis with Bedrock
        logger.info("Starting REAL AI analysis with Bedrock...")
        analysis = analyze_with_bedrock(raw_text, filename)
        
        # Save analysis with optimized storage (keep under 400KB DynamoDB limit)
        resume_info_table = dynamodb.Table(RESUME_INFORMATION_TABLE)
        
        # Store detailed analysis in S3 for large data
        detailed_analysis_s3_key = f"analysis/{str(uuid.uuid4())}.json"
        detailed_analysis = {
            "full_summary": analysis["detailed_summary"],
            "all_skills": analysis["key_skills"],
            "detailed_achievements": analysis.get("key_achievements", []),
            "full_education": analysis.get("education", []),
            "all_certifications": analysis.get("certifications", []),
            "complete_strengths": analysis["strengths"],
            "detailed_recommendations": analysis["recommendations"],
            "skill_breakdown": analysis["skill_breakdown"]
        }
        
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=detailed_analysis_s3_key,
            Body=json.dumps(detailed_analysis, indent=2).encode('utf-8'),
            ContentType='application/json'
        )
        
        # Store essential data in DynamoDB (optimized for size)
        resume_info = {
            'id': str(uuid.uuid4()),
            'parsed_resume_id': parsed_resume_id,
            'extraction_confidence': Decimal(str(analysis["extraction_confidence"])),
            'summary': analysis["summary"][:1000],  # Truncate to prevent size issues
            
            # Core analysis fields
            'candidate_name': analysis["candidate_name"],
            'experience_years': analysis["experience_years"],
            'experience_level': analysis["experience_level"],
            'total_skills': analysis["total_skills"],
            'overall_score': analysis["overall_score"],
            'skill_diversity': analysis["skill_diversity"],
            'fit_assessment': analysis["fit_assessment"],
            
            # Essential lists (truncated)
            'key_skills': analysis["key_skills"][:10],  # Top 10 skills only
            'top_strengths': analysis["strengths"][:5],  # Top 5 strengths
            'top_recommendations': analysis["recommendations"][:3],  # Top 3 recommendations
            
            # S3 references for detailed data
            'detailed_analysis_s3_key': detailed_analysis_s3_key,
            'raw_text_s3_key': raw_text_s3_key,
            
            'created_at': datetime.utcnow().isoformat() + 'Z'
        }
        resume_info_table.put_item(Item=resume_info)
        
        # Trigger email notification asynchronously (non-blocking)
        try:
            trigger_email_notification(resume_info['id'])
        except Exception as email_error:
            logger.warning(f"Failed to trigger email notification: {str(email_error)}")
            # Don't fail the main process if email fails
        
        # Update attachment status
        attachments_table.update_item(
            Key={'id': attachment_id},
            UpdateExpression='SET processingStatus = :status',
            ExpressionAttributeValues={':status': 'COMPLETED'}
        )
        
        logger.info(f"Successfully processed {filename} with real AI analysis")
        return {"status": "success", "attachment_id": attachment_id}
        
    except Exception as e:
        logger.error(f"Error processing file {key}: {str(e)}")
        return {"status": "error", "error": str(e)}

def extract_text_from_file(file_content, filename, content_type):
    """REAL text extraction from various file formats"""
    try:
        file_lower = filename.lower()
        
        if file_lower.endswith('.pdf'):
            return extract_pdf_text(file_content)
        elif file_lower.endswith(('.docx', '.doc')):
            return extract_docx_text(file_content)
        elif file_lower.endswith('.txt') or content_type.startswith('text/'):
            return file_content.decode('utf-8', errors='replace')
        else:
            logger.warning(f"Unsupported file type: {filename}")
            return f"Unsupported file format: {filename}"
            
    except Exception as e:
        logger.error(f"Error extracting text from {filename}: {str(e)}")
        return f"Error extracting text from {filename}: {str(e)}"

def extract_pdf_text(file_content):
    """Extract text from PDF using PyPDF2"""
    try:
        if not PDF_AVAILABLE:
            logger.error("PyPDF2 not available - cannot extract PDF text")
            return "PyPDF2 not available - cannot extract PDF text"
        
        pdf_file = io.BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n"
        
        logger.info(f"Successfully extracted {len(text)} characters from PDF")
        return text.strip()
        
    except Exception as e:
        logger.error(f"Error extracting PDF text: {str(e)}")
        return f"Error extracting PDF text: {str(e)}"

def extract_docx_text(file_content):
    """Extract text from DOCX using python-docx"""
    try:
        if not DOCX_AVAILABLE:
            logger.error("python-docx not available - cannot extract DOCX text")
            return "python-docx not available - cannot extract DOCX text"
        
        docx_file = io.BytesIO(file_content)
        doc = Document(docx_file)
        
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        logger.info(f"Successfully extracted {len(text)} characters from DOCX")
        return text.strip()
        
    except Exception as e:
        logger.error(f"Error extracting DOCX text: {str(e)}")
        return f"Error extracting DOCX text: {str(e)}"

def analyze_with_bedrock(resume_text, filename):
    """REAL AI analysis using Bedrock Nova Premier - NO HARDCODED DATA"""
    try:
        candidate_name = extract_name_from_filename(filename)
        
        # REAL AI PROMPT - NO HARDCODED EXAMPLES
        prompt = f"""You are an expert resume analyzer. Analyze this resume and extract REAL information.

RESUME CONTENT:
{resume_text}

FILENAME: {filename}

Analyze this resume and respond with ONLY a valid JSON object containing the actual information from the resume:

{{
    "candidate_name": "extract real name from resume or use filename",
    "experience_years": "count actual years of experience mentioned",
    "experience_level": "Entry/Junior/Mid-level/Senior/Lead based on actual experience",
    "skills": ["list actual skills mentioned in resume"],
    "overall_score": "score 1-100 based on resume quality and experience",
    "skill_diversity": "score 1-100 based on variety of skills",
    "fit_assessment": "Low/Medium/High based on overall assessment",
    "strengths": ["list actual strengths from resume"],
    "recommendations": ["provide specific improvement recommendations"],
    "detailed_summary": "write detailed summary of candidate's background",
    "key_achievements": ["list actual achievements mentioned"],
    "education": ["list education background"],
    "certifications": ["list certifications mentioned"]
}}

Respond with ONLY the JSON object, no other text."""

        # Call Bedrock Nova Premier with CORRECT parameters
        response = bedrock_client.converse(
            modelId="us.amazon.nova-premier-v1:0",
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={
                "temperature": 0.3,  # Lower temperature for more consistent analysis
                "maxTokens": 2000
                # Removed top_p - not supported by Nova Premier
            }
        )
        
        response_text = response['output']['message']['content'][0]['text']
        logger.info(f"Bedrock response: {response_text[:500]}...")
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        
        if json_match:
            try:
                data = json.loads(json_match.group())
                return process_real_analysis_data(data, candidate_name, resume_text)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {str(e)}")
                return get_fallback_analysis(candidate_name, resume_text)
        else:
            logger.warning("No JSON found in Bedrock response")
            return get_fallback_analysis(candidate_name, resume_text)
            
    except Exception as e:
        logger.error(f"Bedrock analysis failed: {str(e)}")
        return get_fallback_analysis(extract_name_from_filename(filename), resume_text)

def process_real_analysis_data(data, fallback_name, resume_text):
    """Process REAL AI analysis data - no hardcoding with proper data type handling"""
    skills = data.get("skills", [])
    if not skills:
        # Extract skills from text if AI didn't find any
        skills = extract_skills_from_text(resume_text)
    
    # Safe integer conversion with fallbacks
    def safe_int(value, default=0):
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            if value.lower() in ['n/a', 'na', 'unknown', '']:
                return default
            try:
                return int(value)
            except ValueError:
                return default
        return default
    
    return {
        "candidate_name": data.get("candidate_name", fallback_name),
        "experience_years": safe_int(data.get("experience_years"), 1),
        "experience_level": data.get("experience_level", "Junior"),
        "skills": skills,
        "total_skills": len(skills),
        "overall_score": min(100, max(1, safe_int(data.get("overall_score"), 50))),
        "skill_diversity": min(100, max(1, safe_int(data.get("skill_diversity"), 30))),
        "fit_assessment": data.get("fit_assessment", "Medium"),
        "key_skills": skills[:10],
        "skill_breakdown": categorize_skills(skills),
        "strengths": data.get("strengths", ["Professional Background"]),
        "recommendations": data.get("recommendations", ["Continue professional development"]),
        "detailed_summary": data.get("detailed_summary", f"Professional analysis for {fallback_name}"),
        "summary": data.get("detailed_summary", f"Professional analysis for {fallback_name}"),
        "key_achievements": data.get("key_achievements", []),
        "education": data.get("education", []),
        "certifications": data.get("certifications", []),
        "extraction_confidence": 0.85
    }

def extract_skills_from_text(text):
    """Extract skills from resume text using keyword matching"""
    common_skills = [
        "Python", "Java", "JavaScript", "TypeScript", "React", "Angular", "Vue",
        "Node.js", "Express", "Django", "Flask", "Spring", "HTML", "CSS",
        "SQL", "MySQL", "PostgreSQL", "MongoDB", "Redis", "AWS", "Azure", "GCP",
        "Docker", "Kubernetes", "Git", "Jenkins", "CI/CD", "Linux", "Windows",
        "Machine Learning", "AI", "TensorFlow", "PyTorch", "Pandas", "NumPy"
    ]
    
    found_skills = []
    text_lower = text.lower()
    
    for skill in common_skills:
        if skill.lower() in text_lower:
            found_skills.append(skill)
    
    return found_skills[:15]  # Limit to 15 skills

def extract_name_from_filename(filename):
    """Extract candidate name from filename"""
    if not filename:
        return "Unknown Candidate"
    
    clean_name = filename.replace('.pdf', '').replace('.docx', '').replace('.doc', '').replace('.txt', '')
    clean_name = clean_name.replace('Resume_', '').replace('CV_', '').replace('resume-', '').replace('cv-', '')
    clean_name = clean_name.replace('_', ' ').replace('-', ' ')
    clean_name = re.sub(r'\d+', '', clean_name)
    clean_name = re.sub(r'([a-z])([A-Z])', r'\1 \2', clean_name)
    clean_name = clean_name.strip().title()
    
    return clean_name if len(clean_name.split()) >= 2 else "Unknown Candidate"

def categorize_skills(skills):
    """Categorize skills into domains"""
    categories = {
        "Programming": ["python", "java", "javascript", "typescript", "c++", "c#"],
        "Frontend": ["react", "angular", "vue", "html", "css", "bootstrap"],
        "Backend": ["node.js", "express", "django", "flask", "spring"],
        "Database": ["sql", "mysql", "postgresql", "mongodb", "redis"],
        "Cloud": ["aws", "azure", "gcp", "docker", "kubernetes"],
        "DevOps": ["git", "jenkins", "ci/cd", "devops", "linux"]
    }
    
    result = {}
    for category, keywords in categories.items():
        count = sum(1 for skill in skills if skill.lower() in [k.lower() for k in keywords])
        result[category] = count
    
    return result

def get_fallback_analysis(candidate_name, resume_text):
    """Fallback analysis when AI fails - still try to extract real info"""
    skills = extract_skills_from_text(resume_text)
    
    return {
        "candidate_name": candidate_name,
        "experience_years": 1,
        "experience_level": "Junior",
        "skills": skills if skills else ["General Skills"],
        "total_skills": len(skills) if skills else 1,
        "overall_score": 45,
        "skill_diversity": 25,
        "fit_assessment": "Medium",
        "key_skills": skills[:10] if skills else ["General Skills"],
        "skill_breakdown": categorize_skills(skills) if skills else {"General": 1},
        "strengths": ["Professional Background"],
        "recommendations": ["Continue professional development"],
        "detailed_summary": f"Fallback analysis for {candidate_name} - AI analysis unavailable",
        "summary": f"Fallback analysis for {candidate_name}",
        "key_achievements": [],
        "education": [],
        "certifications": [],
        "extraction_confidence": 0.3
    }
