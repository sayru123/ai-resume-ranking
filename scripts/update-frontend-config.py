#!/usr/bin/env python3
"""
Auto-update frontend configuration from CDK outputs and environment variables.

This script:
1. Reads CDK stack outputs from CloudFormation
2. Updates .env file with actual values
3. Updates frontend/static/config.js with real configuration
4. Provides a seamless deployment experience

Usage:
    python3 scripts/update-frontend-config.py
    python3 scripts/update-frontend-config.py --stack-name CustomStackName
"""

import json
import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(command):
    """Run a shell command and return the output."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running command: {command}")
        print(f"Error: {e.stderr}")
        return None

def get_cdk_outputs(stack_name):
    """Get CDK stack outputs from CloudFormation."""
    print(f"🔍 Fetching CDK outputs for stack: {stack_name}")
    
    command = f"aws cloudformation describe-stacks --stack-name {stack_name} --query 'Stacks[0].Outputs' --output json"
    output = run_command(command)
    
    if not output:
        print(f"❌ Failed to get stack outputs for {stack_name}")
        return None
    
    try:
        outputs = json.loads(output)
        output_dict = {}
        
        for item in outputs:
            key = item['OutputKey']
            value = item['OutputValue']
            output_dict[key] = value
            print(f"  ✅ {key}: {value}")
        
        return output_dict
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse stack outputs: {e}")
        return None

def update_env_file(outputs, env_path):
    """Update .env file with CDK outputs."""
    print(f"📝 Updating {env_path}")
    
    # Read existing .env file or create from template
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            env_content = f.read()
    elif os.path.exists(f"{env_path}.example"):
        with open(f"{env_path}.example", 'r') as f:
            env_content = f.read()
        print(f"  📋 Created {env_path} from template")
    else:
        print(f"❌ No .env file or .env.example found")
        return False
    
    # Update values from CDK outputs (map CDK output keys to env var names)
    updates = {
        'S3_BUCKET': outputs.get('S3BucketName', ''),
        'USER_POOL_ID': outputs.get('UserPoolId', outputs.get('AuthUserPoolIdC0605E59', '')),
        'USER_POOL_CLIENT_ID': outputs.get('UserPoolClientId', outputs.get('AuthUserPoolClientId8216BF9A', '')),
        'IDENTITY_POOL_ID': outputs.get('IdentityPoolId', outputs.get('AuthIdentityPoolIdFB6655FB', '')),
        'GRAPHQL_ENDPOINT': outputs.get('GraphQLApiUrl', outputs.get('GraphQLApiGraphQLApiUrl946C20BE', '')),
        'API_ID': outputs.get('WebhookUrl', '').split('.')[0].replace('https://', '') if outputs.get('WebhookUrl') else ''
    }
    
    # Replace values in env content
    for key, value in updates.items():
        if value:
            # Replace existing line or add new line
            if f"{key}=" in env_content:
                lines = env_content.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith(f"{key}="):
                        lines[i] = f"{key}={value}"
                        print(f"  ✅ Updated {key}")
                        break
                env_content = '\n'.join(lines)
            else:
                env_content += f"\n{key}={value}"
                print(f"  ✅ Added {key}")
    
    # Write updated content
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    return True

def update_frontend_config(env_vars, config_path):
    """Update frontend config.js from template using environment variables."""
    print(f"🎨 Updating {config_path}")
    
    template_path = str(config_path) + '.template'
    
    # Check if template exists
    if not os.path.exists(template_path):
        print(f"❌ Template file not found: {template_path}")
        return False
    
    # Read template
    with open(template_path, 'r') as f:
        template_content = f.read()
    
    # Replace template variables with environment values
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
            print(f"  ✅ Replaced {placeholder}")
        else:
            print(f"  ⚠️  Missing value for {placeholder}")
    
    # Add generation timestamp comment
    timestamp = subprocess.run(['date'], capture_output=True, text=True).stdout.strip()
    config_content = f"// Auto-generated from template on {timestamp}\n" + config_content
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    # Write config file
    with open(config_path, 'w') as f:
        f.write(config_content)
    
    print(f"  ✅ Frontend config generated from template")
    return True

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

def main():
    parser = argparse.ArgumentParser(description='Update frontend configuration from CDK outputs')
    parser.add_argument('--stack-name', default='ResumeRankingStack', help='CDK stack name')
    parser.add_argument('--env-file', default='.env', help='Environment file path')
    parser.add_argument('--config-file', default='frontend/static/config.js', help='Frontend config file path')
    
    args = parser.parse_args()
    
    print("🚀 Auto-updating frontend configuration from CDK outputs")
    print("=" * 60)
    
    # Get project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    env_path = project_root / args.env_file
    config_path = project_root / args.config_file
    
    # Get CDK outputs
    outputs = get_cdk_outputs(args.stack_name)
    if not outputs:
        print("❌ Failed to get CDK outputs. Make sure your stack is deployed.")
        sys.exit(1)
    
    # Load existing environment variables
    env_vars = load_env_file(env_path)
    
    # Merge CDK outputs with environment variables
    all_config = {**env_vars, **outputs}
    
    # Update .env file
    if not update_env_file(outputs, env_path):
        print("❌ Failed to update .env file")
        sys.exit(1)
    
    # Update frontend config from template using environment variables
    if not update_frontend_config(all_config, config_path):
        print("❌ Failed to update frontend config")
        sys.exit(1)
    
    print("=" * 60)
    print("✅ Configuration update complete!")
    print(f"📁 Updated files:")
    print(f"  - {env_path}")
    print(f"  - {config_path}")
    print()
    print("🎯 Next steps:")
    print("  1. Deploy frontend: python3 scripts/deploy-frontend.py")
    print("  2. Test your application at your Amplify URL")
    print("  3. Monitor processing: python3 scripts/monitor_processing.py")

if __name__ == "__main__":
    main()
