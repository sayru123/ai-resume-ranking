"""
Fixed Resume Processor using direct Bedrock calls to avoid conversation conflicts
"""
import json
import boto3
import logging
import uuid
from datetime import datetime
from typing import Dict, Any
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('resume_processor.log')
    ]
)

logger = logging.getLogger(__name__)

class ResumeProcessor:
    """Resume processor using direct Bedrock API calls"""
    
    def __init__(self):
        # Initialize Bedrock client
        self.bedrock_client = boto3.client('bedrock-runtime', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
        
        # Initialize S3 client
        self.s3_client = boto3.client('s3', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
        self.bucket_name = os.environ.get('S3_BUCKET')
        
        # Initialize DynamoDB
        self.dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
        self.attachments_table = self.dynamodb.Table(os.environ.get('ATTACHMENTS_TABLE'))
        self.parsed_resumes_table = self.dynamodb.Table(os.environ.get('PARSED_RESUMES_TABLE'))
        self.resume_info_table = self.dynamodb.Table(os.environ.get('RESUME_INFORMATION_TABLE'))
    
    async def analyze_resume_with_bedrock(self, resume_text: str, filename: str = "") -> Dict[str, Any]:
        """Analyze resume using direct Bedrock API call with improved prompting"""
        try:
            # Extract potential name from filename
            filename_name = ""
            if filename:
                # Remove file extension and common prefixes
                clean_filename = filename.replace('.pdf', '').replace('.docx', '').replace('.doc', '').replace('.txt', '')
                # Remove common resume prefixes
                clean_filename = clean_filename.replace('Resume_', '').replace('CV_', '').replace('resume-', '').replace('cv-', '')
                # Replace underscores and hyphens with spaces
                clean_filename = clean_filename.replace('_', ' ').replace('-', ' ')
                if len(clean_filename.split()) >= 2:
                    filename_name = clean_filename.strip()

            prompt = f"""You are an expert HR analyst. Analyze this resume thoroughly and extract comprehensive information.

FILENAME: {filename}
POTENTIAL NAME FROM FILENAME: {filename_name}

RESUME CONTENT:
{resume_text[:4000]}

CRITICAL NAME EXTRACTION INSTRUCTIONS:
1. The filename suggests the candidate name is: "{filename_name}"
2. Look for the candidate's name in this priority order:
   - If filename contains a clear full name, prioritize this
   - Header/top of resume (but be aware of OCR errors)
   - Contact information section
   - Email addresses (e.g., email patterns can suggest names)
3. IMPORTANT: If OCR text differs from filename, prioritize filename as it's likely more accurate
4. Use "Unknown Candidate" only if no name is found anywhere

ANALYSIS REQUIREMENTS:
- Calculate total years of professional experience from work history dates and experience statements
- Extract ALL technical skills, programming languages, frameworks, tools, and technologies mentioned
- Provide detailed analysis including strengths, recommendations, and comprehensive assessment

Respond with a detailed JSON object:
{{
    "candidate_name": "Full Name (prioritize filename over OCR errors)",
    "experience_years": 5,
    "experience_level": "Mid-level",
    "skills": ["Python", "AWS", "Docker", "React", "SQL", "etc"],
    "overall_score": 75,
    "skill_diversity": 60,
    "fit_assessment": "High",
    "strengths": ["Detailed strength 1", "Detailed strength 2", "Detailed strength 3"],
    "recommendations": ["Specific recommendation 1", "Specific recommendation 2"],
    "detailed_summary": "Comprehensive 2-3 sentence summary of the candidate's profile, experience, and key qualifications",
    "key_achievements": ["Achievement 1", "Achievement 2"],
    "education": ["Degree details"],
    "certifications": ["Certification details"]
}}

Provide ONLY the JSON response with comprehensive details:"""

            response = self.bedrock_client.converse(
                modelId="us.amazon.nova-premier-v1:0",
                messages=[
                    {
                        "role": "user",
                        "content": [{"text": prompt}]
                    }
                ],
                inferenceConfig={
                    "temperature": 0.7,
                    "maxTokens": 3000
                }
            )
            
            response_text = response['output']['message']['content'][0]['text']
            logger.info("Bedrock analysis completed successfully")
            
            # Try to parse JSON from response
            try:
                # Extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    analysis_data = json.loads(json_str)
                    
                    # Validate and set defaults with better fallbacks
                    result = {
                        "candidate_name": analysis_data.get("candidate_name", filename_name or "Unknown Candidate"),
                        "experience_years": max(1, analysis_data.get("experience_years", 1)),
                        "experience_level": analysis_data.get("experience_level", "Entry-level"),
                        "skills": analysis_data.get("skills", ["Technical Skills"]),
                        "overall_score": min(100, max(25, analysis_data.get("overall_score", 50))),
                        "skill_diversity": min(100, max(20, analysis_data.get("skill_diversity", 40))),
                        "fit_assessment": analysis_data.get("fit_assessment", "Medium"),
                        "strengths": analysis_data.get("strengths", ["Professional Background"]),
                        "recommendations": analysis_data.get("recommendations", ["Continue development"]),
                        "detailed_summary": analysis_data.get("detailed_summary", f"Analysis for {analysis_data.get('candidate_name', 'candidate')}"),
                        "key_achievements": analysis_data.get("key_achievements", []),
                        "education": analysis_data.get("education", []),
                        "certifications": analysis_data.get("certifications", [])
                    }
                    
                    # Calculate additional metrics
                    result["total_skills"] = len(result["skills"])
                    result["key_skills"] = result["skills"][:10]
                    result["skill_breakdown"] = self.categorize_skills(result["skills"])
                    
                    return result
                else:
                    logger.warning("No JSON found in Bedrock response")
                    return self.get_fallback_analysis(resume_text, filename)
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from Bedrock response: {e}")
                return self.get_fallback_analysis(resume_text, filename)
                
        except Exception as e:
            logger.error(f"Bedrock analysis failed: {str(e)}")
            return self.get_fallback_analysis(resume_text, filename)
    
    def categorize_skills(self, skills: list) -> Dict[str, int]:
        """Categorize skills into technical domains"""
        categories = {
            "Programming": ["python", "java", "javascript", "typescript", "c++", "c#", "go", "rust"],
            "Frontend": ["react", "angular", "vue", "html", "css", "bootstrap", "tailwind"],
            "Backend": ["node.js", "express", "django", "flask", "spring", "laravel"],
            "Database": ["sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch"],
            "Cloud": ["aws", "azure", "gcp", "docker", "kubernetes", "terraform"],
            "AI_ML": ["machine learning", "ai", "tensorflow", "pytorch", "data science"],
            "DevOps": ["git", "jenkins", "ci/cd", "devops", "docker", "kubernetes"],
            "Mobile": ["ios", "android", "react native", "flutter", "swift", "kotlin"]
        }
        
        skill_breakdown = {}
        for category, category_skills in categories.items():
            count = sum(1 for skill in skills if skill.lower() in [s.lower() for s in category_skills])
            skill_breakdown[category] = count
        
        return skill_breakdown
    
    def get_fallback_analysis(self, resume_text: str, filename: str = "") -> Dict[str, Any]:
        """Fallback analysis when AI fails"""
        import re
        
        # Extract basic info using regex
        candidate_name = "Unknown Candidate"
        
        # Try to extract name from filename first (most reliable)
        if filename:
            clean_filename = filename.replace('.pdf', '').replace('.docx', '').replace('.doc', '').replace('.txt', '')
            clean_filename = clean_filename.replace('Resume_', '').replace('CV_', '').replace('resume-', '').replace('cv-', '')
            clean_filename = clean_filename.replace('_', ' ').replace('-', ' ')
            
            # Handle specific patterns like "FirstLast2025" -> "First Last"
            import re
            # Remove years and numbers
            clean_filename = re.sub(r'\d{4}', '', clean_filename)
            clean_filename = re.sub(r'\d+', '', clean_filename)
            
            # Handle camelCase names like "FirstLast" -> "First Last"
            clean_filename = re.sub(r'([a-z])([A-Z])', r'\1 \2', clean_filename)
            
            clean_filename = clean_filename.strip()
            if len(clean_filename.split()) >= 2:
                candidate_name = clean_filename.title()
                logger.info(f"Extracted name from filename: {candidate_name}")
        
        # Extract skills
        skill_keywords = [
            'python', 'java', 'javascript', 'react', 'aws', 'azure', 'docker', 
            'kubernetes', 'sql', 'git', 'linux', 'html', 'css', 'node.js'
        ]
        
        found_skills = []
        text_lower = resume_text.lower()
        for skill in skill_keywords:
            if skill in text_lower:
                found_skills.append(skill.title())
        
        # Extract experience years
        year_patterns = [
            r'(\d+)\s*\+?\s*years?\s*(?:of\s*)?(?:experience|exp)',
            r'experience\s*(?:of\s*)?(\d+)\s*\+?\s*years?'
        ]
        
        experience_years = 1
        for pattern in year_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                try:
                    years = max([int(match) for match in matches])
                    experience_years = max(experience_years, years)
                except ValueError:
                    continue
        
        # Determine experience level
        if experience_years >= 7:
            experience_level = "Senior"
        elif experience_years >= 3:
            experience_level = "Mid-level"
        else:
            experience_level = "Junior"
        
        # Calculate scores
        overall_score = min(100, 25 + len(found_skills) * 5 + experience_years * 3)
        skill_diversity = min(100, len(found_skills) * 8)
        
        return {
            "candidate_name": candidate_name,
            "experience_years": experience_years,
            "experience_level": experience_level,
            "skills": found_skills or ["Technical Skills"],
            "total_skills": len(found_skills) or 1,
            "overall_score": overall_score,
            "skill_diversity": skill_diversity,
            "fit_assessment": "High" if overall_score >= 70 else "Medium" if overall_score >= 50 else "Low",
            "key_skills": found_skills[:10] or ["Technical Skills"],
            "skill_breakdown": self.categorize_skills(found_skills),
            "strengths": ["Professional Experience", "Technical Skills"],
            "recommendations": ["Continue skill development", "Expand technical expertise"],
            "detailed_summary": f"Fallback analysis for {candidate_name} with {experience_years} years of experience",
            "key_achievements": [],
            "education": [],
            "certifications": []
        }
    
    def process_resume_from_s3(self, s3_key: str) -> Dict[str, Any]:
        """Process a resume from S3 and save to database"""
        try:
            logger.info(f"Processing resume: {s3_key}")
            
            # Download from S3
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            file_content = response['Body'].read()
            content_type = response.get('ContentType', 'application/octet-stream')
            filename = s3_key.split('/')[-1]
            
            # Create attachment record
            attachment_id = str(uuid.uuid4())
            attachment = {
                'id': attachment_id,
                'filename': filename,
                'contentType': content_type,
                'content': file_content,
                'size': len(file_content),
                'createdAt': datetime.utcnow().isoformat() + 'Z',
                'processingStatus': 'PROCESSING'
            }
            
            self.attachments_table.put_item(Item=attachment)
            
            # Extract text from different file types
            if content_type.startswith('text/'):
                raw_text = file_content.decode('utf-8', errors='replace')
            elif content_type == 'application/pdf' or filename.lower().endswith('.pdf'):
                # Extract text from PDF
                logger.info(f"Extracting text from PDF: {filename}")
                try:
                    import pdfplumber
                    import io
                    
                    pdf_file = io.BytesIO(file_content)
                    extracted_text = ""
                    
                    with pdfplumber.open(pdf_file) as pdf:
                        logger.info(f"PDF has {len(pdf.pages)} pages")
                        for page_num, page in enumerate(pdf.pages):
                            page_text = page.extract_text()
                            if page_text:
                                extracted_text += f"\n--- PAGE {page_num + 1} ---\n"
                                extracted_text += page_text
                    
                    if extracted_text.strip():
                        raw_text = f"RESUME: {filename}\n\n{extracted_text}"
                        logger.info(f"Successfully extracted {len(extracted_text)} characters from PDF")
                    else:
                        raw_text = f"PDF Document: {filename}\nNo text could be extracted."
                        
                except Exception as e:
                    logger.error(f"Error extracting text from PDF: {str(e)}")
                    raw_text = f"PDF Document: {filename}\nError extracting text: {str(e)}"
            else:
                raw_text = f"Resume File: {filename}\nContent Type: {content_type}"
            
            # Create parsed resume record
            parsed_resume_id = str(uuid.uuid4())
            parsed_resume = {
                'id': parsed_resume_id,
                'attachment_id': attachment_id,
                'raw_text': raw_text,
                'parsing_status': 'processing',
                'created_at': datetime.utcnow().isoformat() + 'Z'
            }
            
            self.parsed_resumes_table.put_item(Item=parsed_resume)
            
            # Analyze with Bedrock
            logger.info("Analyzing resume with Nova Premier...")
            analysis_data = await self.analyze_resume_with_bedrock(raw_text, filename)
            
            # Update parsing status
            parsed_resume['parsing_status'] = 'completed'
            self.parsed_resumes_table.put_item(Item=parsed_resume)
            
            # Create resume information record
            resume_info = {
                'id': str(uuid.uuid4()),
                'parsed_resume_id': parsed_resume_id,
                'extraction_confidence': 0.9,
                'summary': analysis_data.get("detailed_summary", f"Analysis for {analysis_data['candidate_name']}"),
                
                # Structured analytics
                'candidate_name': analysis_data["candidate_name"],
                'experience_years': analysis_data["experience_years"],
                'experience_level': analysis_data["experience_level"],
                'total_skills': analysis_data["total_skills"],
                'overall_score': analysis_data["overall_score"],
                'skill_diversity': analysis_data["skill_diversity"],
                'fit_assessment': analysis_data["fit_assessment"],
                'key_skills': analysis_data["key_skills"],
                'skill_breakdown': analysis_data["skill_breakdown"],
                'strengths': analysis_data["strengths"],
                'recommendations': analysis_data["recommendations"],
                
                # New enhanced fields
                'detailed_summary': analysis_data.get("detailed_summary", ""),
                'key_achievements': analysis_data.get("key_achievements", []),
                'education': analysis_data.get("education", []),
                'certifications': analysis_data.get("certifications", []),
                
                'created_at': datetime.utcnow().isoformat() + 'Z'
            }
            
            self.resume_info_table.put_item(Item=resume_info)
            
            # Update attachment status
            attachment['processingStatus'] = 'COMPLETED'
            self.attachments_table.put_item(Item=attachment)
            
            logger.info(f"Successfully processed: {filename}")
            return {
                "status": "success",
                "attachment_id": attachment_id,
                "resume_id": resume_info['id'],
                "filename": filename,
                "analysis_preview": f"Processed {analysis_data['candidate_name']} - {analysis_data['experience_level']}",
                "processed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing resume: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "s3_key": s3_key
            }

# Global instance
resume_processor = ResumeProcessor()
