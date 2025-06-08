#!/usr/bin/env python3
"""
Monitor the processing progress of resumes
"""
import boto3
import time
import json
from datetime import datetime

def check_progress():
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    
    # Check each table
    attachments_table = dynamodb.Table('resume-ranking-attachments')
    parsed_table = dynamodb.Table('resume-ranking-parsed-resumes')
    analysis_table = dynamodb.Table('resume-ranking-resume-information')
    
    # Count items in each table
    attachments_count = attachments_table.scan(Select='COUNT')['Count']
    parsed_count = parsed_table.scan(Select='COUNT')['Count']
    analysis_count = analysis_table.scan(Select='COUNT')['Count']
    
    print(f"📊 Processing Progress - {datetime.now().strftime('%H:%M:%S')}")
    print(f"📁 Attachments: {attachments_count}/10")
    print(f"📄 Parsed: {parsed_count}/10")
    print(f"🤖 AI Analysis: {analysis_count}/10")
    print("-" * 40)
    
    if analysis_count == 10:
        print("✅ All processing complete!")
        
        # Show sample analysis
        response = analysis_table.scan(Limit=1)
        if response['Items']:
            item = response['Items'][0]
            print(f"📋 Sample: {item.get('candidate_name', 'Unknown')} - Score: {item.get('overall_score', 0)}")
        
        return True
    
    return False

if __name__ == "__main__":
    print("🔍 Starting processing monitor...")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            complete = check_progress()
            if complete:
                break
            time.sleep(10)  # Check every 10 seconds
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped")
