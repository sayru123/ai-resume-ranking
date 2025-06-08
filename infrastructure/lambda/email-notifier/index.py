#!/usr/bin/env python3
"""
Email Notification Lambda Function
Sends rich HTML email notifications via Postmark API when resume analysis is complete
"""

import json
import os
import boto3
import requests
from datetime import datetime
from decimal import Decimal
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
POSTMARK_SERVER_TOKEN = os.environ.get('POSTMARK_SERVER_TOKEN')
NOTIFICATION_EMAIL = os.environ.get('NOTIFICATION_EMAIL', 'info@viaan.tech')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@viaan.tech')
POSTMARK_API_URL = 'https://api.postmarkapp.com/email'

# DynamoDB client
dynamodb = boto3.resource('dynamodb')

def decimal_to_int(obj):
    """Convert Decimal objects to int/float for JSON serialization"""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    return obj

def get_resume_analysis(resume_info_id):
    """Get complete resume analysis from DynamoDB"""
    try:
        table = dynamodb.Table('resume-ranking-resume-information')
        response = table.get_item(Key={'id': resume_info_id})
        
        if 'Item' not in response:
            logger.error(f"Resume analysis not found: {resume_info_id}")
            return None
            
        return response['Item']
    except Exception as e:
        logger.error(f"Error fetching resume analysis: {str(e)}")
        return None

def create_html_email_body(analysis):
    """Create rich HTML email body with resume analysis"""
    candidate_name = analysis.get('candidate_name', 'Unknown Candidate')
    overall_score = decimal_to_int(analysis.get('overall_score', 0))
    experience_level = analysis.get('experience_level', 'Unknown')
    experience_years = decimal_to_int(analysis.get('experience_years', 0))
    fit_assessment = analysis.get('fit_assessment', 'Unknown')
    key_skills = analysis.get('key_skills', [])
    top_strengths = analysis.get('top_strengths', [])
    top_recommendations = analysis.get('top_recommendations', [])
    summary = analysis.get('summary', 'No summary available')
    
    # Convert lists to HTML if they're stored as DynamoDB lists
    if isinstance(key_skills, list) and key_skills and isinstance(key_skills[0], dict):
        key_skills = [skill.get('S', skill) for skill in key_skills]
    if isinstance(top_strengths, list) and top_strengths and isinstance(top_strengths[0], dict):
        top_strengths = [strength.get('S', strength) for strength in top_strengths]
    if isinstance(top_recommendations, list) and top_recommendations and isinstance(top_recommendations[0], dict):
        top_recommendations = [rec.get('S', rec) for rec in top_recommendations]
    
    # Score color based on value
    if overall_score >= 90:
        score_color = "#10B981"  # Green
        score_label = "Excellent"
    elif overall_score >= 80:
        score_color = "#F59E0B"  # Yellow
        score_label = "Good"
    elif overall_score >= 70:
        score_color = "#EF4444"  # Red
        score_label = "Fair"
    else:
        score_color = "#6B7280"  # Gray
        score_label = "Needs Review"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Resume Analysis Complete</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f8fafc; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: white; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
            .content {{ padding: 30px; }}
            .score-badge {{ display: inline-block; background-color: {score_color}; color: white; padding: 8px 16px; border-radius: 20px; font-weight: bold; font-size: 14px; }}
            .section {{ margin-bottom: 25px; }}
            .section h3 {{ color: #374151; margin-bottom: 10px; font-size: 18px; }}
            .skills-grid {{ display: flex; flex-wrap: wrap; gap: 8px; }}
            .skill-tag {{ background-color: #e5e7eb; color: #374151; padding: 4px 12px; border-radius: 12px; font-size: 12px; }}
            .strength-item, .recommendation-item {{ background-color: #f3f4f6; padding: 12px; border-radius: 8px; margin-bottom: 8px; }}
            .footer {{ background-color: #f8fafc; padding: 20px; text-align: center; color: #6b7280; font-size: 14px; }}
            .summary-box {{ background-color: #f0f9ff; border-left: 4px solid #0ea5e9; padding: 15px; border-radius: 4px; }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 20px 0; }}
            .stat-card {{ background-color: #f8fafc; padding: 15px; border-radius: 8px; text-align: center; }}
            .stat-value {{ font-size: 24px; font-weight: bold; color: #1f2937; }}
            .stat-label {{ font-size: 12px; color: #6b7280; text-transform: uppercase; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎯 Resume Analysis Complete</h1>
                <p>AI-powered candidate evaluation results</p>
            </div>
            
            <div class="content">
                <div class="section">
                    <h2 style="color: #1f2937; margin-bottom: 20px;">📋 Candidate Overview</h2>
                    <h3 style="font-size: 24px; color: #1f2937; margin-bottom: 10px;">{candidate_name}</h3>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-value" style="color: {score_color};">{overall_score}</div>
                            <div class="stat-label">Overall Score</div>
                            <span class="score-badge">{score_label}</span>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{experience_years}</div>
                            <div class="stat-label">Years Experience</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{experience_level}</div>
                            <div class="stat-label">Experience Level</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{fit_assessment}</div>
                            <div class="stat-label">Fit Assessment</div>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <h3>📝 Executive Summary</h3>
                    <div class="summary-box">
                        {summary}
                    </div>
                </div>
                
                <div class="section">
                    <h3>🛠️ Key Skills ({len(key_skills)} identified)</h3>
                    <div class="skills-grid">
                        {''.join([f'<span class="skill-tag">{skill}</span>' for skill in key_skills[:15]])}
                        {f'<span class="skill-tag">+{len(key_skills)-15} more</span>' if len(key_skills) > 15 else ''}
                    </div>
                </div>
                
                <div class="section">
                    <h3>💪 Top Strengths</h3>
                    {''.join([f'<div class="strength-item">✅ {strength}</div>' for strength in top_strengths])}
                </div>
                
                <div class="section">
                    <h3>🎯 Recommendations for Improvement</h3>
                    {''.join([f'<div class="recommendation-item">💡 {rec}</div>' for rec in top_recommendations])}
                </div>
                
                <div class="section" style="text-align: center; margin-top: 30px;">
                    <p style="color: #6b7280;">View complete analysis in your dashboard</p>
                    <a href="https://d146epnafgqu9f.amplifyapp.com" 
                       style="display: inline-block; background-color: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                        Open Dashboard
                    </a>
                </div>
            </div>
            
            <div class="footer">
                <p>🤖 AI Resume Ranking System</p>
                <p>Powered by Amazon Bedrock Nova Premier • Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_body

def send_postmark_email(analysis):
    """Send email notification via Postmark API"""
    try:
        candidate_name = analysis.get('candidate_name', 'Unknown Candidate')
        overall_score = decimal_to_int(analysis.get('overall_score', 0))
        
        html_body = create_html_email_body(analysis)
        
        # Prepare email payload
        email_data = {
            "From": FROM_EMAIL,
            "To": NOTIFICATION_EMAIL,
            "Subject": f"🎯 Resume Analysis Complete: {candidate_name} (Score: {overall_score})",
            "HtmlBody": html_body,
            "TextBody": f"Resume analysis complete for {candidate_name}. Overall Score: {overall_score}. View full analysis in your dashboard.",
            "MessageStream": "outbound"
        }
        
        # Send email via Postmark API
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Postmark-Server-Token": POSTMARK_SERVER_TOKEN
        }
        
        response = requests.post(POSTMARK_API_URL, json=email_data, headers=headers)
        
        if response.status_code == 200:
            logger.info(f"Email sent successfully for {candidate_name}")
            return True
        else:
            logger.error(f"Failed to send email: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False

def lambda_handler(event, context):
    """
    Lambda handler for email notifications
    Triggered asynchronously after resume analysis completion
    """
    try:
        logger.info(f"Email notification triggered: {json.dumps(event)}")
        
        # Extract resume analysis ID from event
        resume_info_id = event.get('resume_info_id')
        if not resume_info_id:
            logger.error("No resume_info_id provided in event")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'resume_info_id required'})
            }
        
        # Get resume analysis data
        analysis = get_resume_analysis(resume_info_id)
        if not analysis:
            logger.error(f"Resume analysis not found: {resume_info_id}")
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Resume analysis not found'})
            }
        
        # Send email notification
        success = send_postmark_email(analysis)
        
        if success:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Email notification sent successfully',
                    'candidate': analysis.get('candidate_name', 'Unknown'),
                    'score': decimal_to_int(analysis.get('overall_score', 0))
                })
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Failed to send email notification'})
            }
            
    except Exception as e:
        logger.error(f"Error in email notification handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
