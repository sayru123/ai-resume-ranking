#!/usr/bin/env python3
"""
Deploy frontend to Amplify using AWS CLI with environment-based configuration
"""
import boto3
import zipfile
import os
import sys
import time
from pathlib import Path

def load_env_file(env_path):
    """Load environment variables from .env file."""
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
    return env_vars

def generate_config_from_template():
    """Generate config.js from template using environment variables."""
    project_root = Path.cwd()  # Use current working directory instead of __file__
    template_path = project_root / 'frontend' / 'static' / 'config.js.template'
    config_path = project_root / 'frontend' / 'static' / 'config.js'
    env_path = project_root / '.env'
    
    print("🔧 Generating config.js from template...")
    
    # Load environment variables
    env_vars = load_env_file(env_path)
    
    if not os.path.exists(template_path):
        print(f"❌ Template not found: {template_path}")
        return False
    
    # Read template
    with open(template_path, 'r') as f:
        template_content = f.read()
    
    # Replace template variables
    config_content = template_content
    replacements = {
        '${AWS_REGION}': env_vars.get('AWS_REGION', 'us-east-1'),
        '${USER_POOL_ID}': env_vars.get('USER_POOL_ID', ''),
        '${USER_POOL_CLIENT_ID}': env_vars.get('USER_POOL_CLIENT_ID', ''),
        '${IDENTITY_POOL_ID}': env_vars.get('IDENTITY_POOL_ID', ''),
        '${GRAPHQL_ENDPOINT}': env_vars.get('GRAPHQL_ENDPOINT', ''),
        '${API_ID}': env_vars.get('API_ID', '')
    }
    
    for placeholder, value in replacements.items():
        config_content = config_content.replace(placeholder, value)
        if value:
            print(f"  ✅ {placeholder} → {value}")
        else:
            print(f"  ⚠️  Missing: {placeholder}")
    
    # Add generation comment
    import subprocess
    timestamp = subprocess.run(['date'], capture_output=True, text=True).stdout.strip()
    config_content = f"// Auto-generated from template on {timestamp}\n" + config_content
    
    # Write config file
    with open(config_path, 'w') as f:
        f.write(config_content)
    
    print(f"  ✅ Generated: {config_path}")
    return True

def create_deployment_zip():
    """Create deployment zip from frontend static files"""
    frontend_dir = Path(__file__).parent.parent / 'frontend' / 'static'
    zip_path = Path(__file__).parent.parent / 'frontend' / 'frontend-deploy.zip'
    
    print(f"Creating deployment zip from: {frontend_dir}")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in frontend_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(frontend_dir)
                zipf.write(file_path, arcname)
                print(f"Added: {arcname}")
    
    print(f"Created deployment zip: {zip_path}")
    return zip_path

def deploy_to_amplify(zip_path, app_id='d146epnafgqu9f', branch_name='staging'):
    """Deploy zip file to Amplify"""
    client = boto3.client('amplify', region_name='us-east-1')
    
    try:
        # Upload zip file to S3 first (Amplify needs a URL)
        s3_client = boto3.client('s3')
        bucket_name = os.environ.get('S3_BUCKET')
        if not bucket_name:
            # Try to auto-detect bucket
            try:
                s3 = boto3.client('s3')
                response = s3.list_buckets()
                for bucket in response['Buckets']:
                    if 'resume-ranking-bucket' in bucket['Name']:
                        bucket_name = bucket['Name']
                        break
                
                if not bucket_name:
                    # Fallback - construct expected name
                    sts = boto3.client('sts')
                    account_id = sts.get_caller_identity()['Account']
                    bucket_name = f'resume-ranking-bucket-{account_id}-us-east-1'
            except Exception as e:
                print(f"Error: Could not determine bucket name: {e}")
                print("Please set S3_BUCKET environment variable or provide --bucket-name")
                return False
        s3_key = f'amplify-deployments/frontend-{int(time.time())}.zip'
        
        print(f"Uploading to S3: s3://{bucket_name}/{s3_key}")
        s3_client.upload_file(str(zip_path), bucket_name, s3_key)
        
        # Generate presigned URL
        zip_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': s3_key},
            ExpiresIn=3600
        )
        
        # Start Amplify deployment
        print(f"Starting Amplify deployment for app: {app_id}, branch: {branch_name}")
        response = client.start_deployment(
            appId=app_id,
            branchName=branch_name,
            sourceUrl=zip_url
        )
        
        job_id = response['jobSummary']['jobId']
        print(f"Deployment started! Job ID: {job_id}")
        print(f"Monitor at: https://console.aws.amazon.com/amplify/home?region=us-east-1#{app_id}")
        
        return job_id
        
    except Exception as e:
        print(f"Error deploying to Amplify: {str(e)}")
        return None

def main():
    """Main deployment function"""
    print("🚀 Starting Amplify Frontend Deployment")
    
    # Generate config.js from template first
    if not generate_config_from_template():
        print("❌ Failed to generate config from template")
        sys.exit(1)
    
    # Create deployment zip
    zip_path = create_deployment_zip()
    
    # Deploy to Amplify
    job_id = deploy_to_amplify(zip_path)
    
    if job_id:
        print(f"✅ Deployment initiated successfully!")
        print(f"📱 Your app will be available at: https://xxxxxx.amplifyapp.com")
        print(f"⏱️  Deployment typically takes 2-3 minutes")
    else:
        print("❌ Deployment failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()
