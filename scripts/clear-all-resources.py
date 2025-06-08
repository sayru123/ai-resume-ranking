#!/usr/bin/env python3
"""
Clear all AWS resources for the Resume Ranking System
Comprehensive cleanup script for DynamoDB, S3, CloudWatch, and more
"""
import boto3
import json
import os
from datetime import datetime
import argparse
import sys

class ResourceCleaner:
    def __init__(self, region='us-east-1', dry_run=False):
        self.region = region
        self.dry_run = dry_run
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.logs = boto3.client('logs', region_name=region)
        self.cognito_idp = boto3.client('cognito-idp', region_name=region)
        
        # Resource identifiers - dynamically determined
        self.bucket_name = self._get_bucket_name()
        self.table_names = [
            'resume-ranking-attachments',
            'resume-ranking-parsed-resumes', 
            'resume-ranking-resume-information'
        ]
        self.log_group_prefix = '/aws/lambda/resume-ranking'
        self.user_pool_id = None  # Will be detected automatically
        
    def _get_bucket_name(self):
        """Dynamically determine S3 bucket name from environment or AWS"""
        # Try environment variable first
        bucket_name = os.environ.get('S3_BUCKET')
        if bucket_name:
            return bucket_name
            
        # Try to find bucket with resume-ranking prefix
        try:
            s3_client = boto3.client('s3', region_name=self.region)
            response = s3_client.list_buckets()
            for bucket in response['Buckets']:
                if 'resume-ranking-bucket' in bucket['Name']:
                    return bucket['Name']
        except Exception as e:
            print(f"Warning: Could not auto-detect bucket name: {e}")
            
        # Fallback - construct expected name
        try:
            sts = boto3.client('sts')
            account_id = sts.get_caller_identity()['Account']
            return f'resume-ranking-bucket-{account_id}-{self.region}'
        except Exception as e:
            print(f"Error: Could not determine bucket name: {e}")
            return None
        
    def print_action(self, action, resource, status="PENDING"):
        """Print formatted action with status"""
        mode = "[DRY RUN]" if self.dry_run else "[EXECUTE]"
        print(f"{mode} {action}: {resource} - {status}")
    
    def clear_dynamodb_tables(self):
        """Clear all DynamoDB tables"""
        print("\n🗑️ Clearing DynamoDB Tables...")
        
        for table_name in self.table_names:
            try:
                table = self.dynamodb.Table(table_name)
                self.print_action("SCAN TABLE", table_name)
                
                if not self.dry_run:
                    # Scan and delete all items
                    response = table.scan(ProjectionExpression='id')
                    items = response.get('Items', [])
                    
                    deleted_count = 0
                    for item in items:
                        table.delete_item(Key={'id': item['id']})
                        deleted_count += 1
                        
                    # Handle pagination
                    while 'LastEvaluatedKey' in response:
                        response = table.scan(
                            ProjectionExpression='id',
                            ExclusiveStartKey=response['LastEvaluatedKey']
                        )
                        items = response.get('Items', [])
                        for item in items:
                            table.delete_item(Key={'id': item['id']})
                            deleted_count += 1
                    
                    self.print_action("CLEARED TABLE", f"{table_name} ({deleted_count} items)", "SUCCESS")
                else:
                    # Dry run - just count items
                    response = table.scan(Select='COUNT')
                    count = response.get('Count', 0)
                    self.print_action("WOULD CLEAR", f"{table_name} ({count} items)", "DRY RUN")
                    
            except Exception as e:
                self.print_action("ERROR", f"{table_name}: {e}", "FAILED")

    def clear_s3_bucket(self):
        """Clear S3 bucket contents including versions"""
        print("\n🗑️ Clearing S3 Bucket...")
        
        if not self.bucket_name:
            self.print_action("ERROR", "No bucket name determined", "FAILED")
            return
        
        try:
            self.print_action("LIST OBJECTS", self.bucket_name)
            
            if not self.dry_run:
                # Delete all object versions
                paginator = self.s3.get_paginator('list_object_versions')
                delete_count = 0
                
                for page in paginator.paginate(Bucket=self.bucket_name):
                    objects_to_delete = []
                    
                    # Add current versions
                    for obj in page.get('Versions', []):
                        objects_to_delete.append({
                            'Key': obj['Key'],
                            'VersionId': obj['VersionId']
                        })
                    
                    # Add delete markers
                    for obj in page.get('DeleteMarkers', []):
                        objects_to_delete.append({
                            'Key': obj['Key'],
                            'VersionId': obj['VersionId']
                        })
                    
                    # Delete in batches
                    if objects_to_delete:
                        self.s3.delete_objects(
                            Bucket=self.bucket_name,
                            Delete={'Objects': objects_to_delete}
                        )
                        delete_count += len(objects_to_delete)
                
                self.print_action("CLEARED BUCKET", f"{self.bucket_name} ({delete_count} objects)", "SUCCESS")
            else:
                # Dry run - count objects
                response = self.s3.list_objects_v2(Bucket=self.bucket_name)
                count = response.get('KeyCount', 0)
                self.print_action("WOULD CLEAR", f"{self.bucket_name} ({count} objects)", "DRY RUN")
                
        except Exception as e:
            self.print_action("ERROR", f"{self.bucket_name}: {e}", "FAILED")

    def clear_cloudwatch_logs(self):
        """Clear CloudWatch log groups"""
        print("\n🗑️ Clearing CloudWatch Logs...")
        
        try:
            self.print_action("LIST LOG GROUPS", f"prefix: {self.log_group_prefix}")
            
            # Get all log groups with our prefix
            paginator = self.logs.get_paginator('describe_log_groups')
            log_groups = []
            
            for page in paginator.paginate(logGroupNamePrefix=self.log_group_prefix):
                for group in page['logGroups']:
                    log_groups.append(group['logGroupName'])
            
            if not self.dry_run:
                deleted_count = 0
                for log_group in log_groups:
                    try:
                        self.logs.delete_log_group(logGroupName=log_group)
                        deleted_count += 1
                        self.print_action("DELETED LOG GROUP", log_group, "SUCCESS")
                    except Exception as e:
                        self.print_action("ERROR", f"{log_group}: {e}", "FAILED")
                
                if deleted_count == 0:
                    self.print_action("NO LOG GROUPS", "found with prefix", "INFO")
            else:
                for log_group in log_groups:
                    self.print_action("WOULD DELETE", log_group, "DRY RUN")
                if not log_groups:
                    self.print_action("NO LOG GROUPS", "found with prefix", "INFO")
                    
        except Exception as e:
            self.print_action("ERROR", f"CloudWatch logs: {e}", "FAILED")

    def clear_cognito_users(self):
        """Clear Cognito user pool users (optional)"""
        print("\n🗑️ Clearing Cognito Users...")
        
        try:
            # Auto-detect user pool ID
            if not self.user_pool_id:
                pools = self.cognito_idp.list_user_pools(MaxResults=60)
                for pool in pools['UserPools']:
                    if 'resume-ranking' in pool['Name'].lower():
                        self.user_pool_id = pool['Id']
                        break
            
            if not self.user_pool_id:
                self.print_action("NO USER POOL", "found with resume-ranking prefix", "INFO")
                return
            
            self.print_action("LIST USERS", f"pool: {self.user_pool_id}")
            
            if not self.dry_run:
                # List and delete all users
                paginator = self.cognito_idp.get_paginator('list_users')
                deleted_count = 0
                
                for page in paginator.paginate(UserPoolId=self.user_pool_id):
                    for user in page['Users']:
                        username = user['Username']
                        try:
                            self.cognito_idp.admin_delete_user(
                                UserPoolId=self.user_pool_id,
                                Username=username
                            )
                            deleted_count += 1
                            self.print_action("DELETED USER", username, "SUCCESS")
                        except Exception as e:
                            self.print_action("ERROR", f"{username}: {e}", "FAILED")
                
                if deleted_count == 0:
                    self.print_action("NO USERS", "found in user pool", "INFO")
            else:
                # Dry run - count users
                response = self.cognito_idp.list_users(UserPoolId=self.user_pool_id)
                count = len(response.get('Users', []))
                self.print_action("WOULD DELETE", f"{count} users", "DRY RUN")
                
        except Exception as e:
            self.print_action("ERROR", f"Cognito users: {e}", "FAILED")

    def run_cleanup(self, include_cognito=False):
        """Run the complete cleanup process"""
        print("🚨 AWS Resume Ranking System - Complete Resource Cleanup")
        print("=" * 60)
        print(f"Region: {self.region}")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'EXECUTE'}")
        print(f"Bucket: {self.bucket_name or 'NOT FOUND'}")
        print(f"Timestamp: {datetime.now()}")
        print("=" * 60)
        
        if not self.dry_run:
            confirm = input("⚠️  This will DELETE ALL data and resources. Type 'DELETE' to confirm: ")
            if confirm != 'DELETE':
                print("❌ Cancelled - confirmation not received")
                return False
        
        # Run cleanup operations
        self.clear_dynamodb_tables()
        self.clear_s3_bucket()
        self.clear_cloudwatch_logs()
        
        if include_cognito:
            self.clear_cognito_users()
        
        print("\n" + "=" * 60)
        if self.dry_run:
            print("✅ Dry run completed - no resources were actually deleted")
            print("💡 Run without --dry-run to execute the cleanup")
        else:
            print("✅ Cleanup completed!")
            print("💡 All specified resources have been removed")
        print("=" * 60)
        
        return True

def main():
    parser = argparse.ArgumentParser(description='Clear all AWS resources for Resume Ranking System')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be deleted without actually deleting')
    parser.add_argument('--region', default='us-east-1',
                       help='AWS region (default: us-east-1)')
    parser.add_argument('--include-cognito', action='store_true',
                       help='Also clear Cognito user pool users')
    parser.add_argument('--bucket-name', 
                       help='Override S3 bucket name (use with caution)')
    
    args = parser.parse_args()
    
    # Create cleaner instance
    cleaner = ResourceCleaner(region=args.region, dry_run=args.dry_run)
    
    # Override bucket name if provided
    if args.bucket_name:
        cleaner.bucket_name = args.bucket_name
        print(f"⚠️  Using override bucket name: {args.bucket_name}")
    
    # Run cleanup
    success = cleaner.run_cleanup(include_cognito=args.include_cognito)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
