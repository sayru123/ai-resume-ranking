# 🚀 Deployment Guide - AI Resume Ranking System

**Complete step-by-step deployment guide for the AWS Serverless Resume Ranking System**

## 📋 **Prerequisites**

### **Required Tools**
- **AWS CLI** v2.x configured with appropriate permissions
- **Node.js** 18+ and npm (for AWS CDK)
- **Python** 3.8+ (for scripts)
- **Git** (for version control)

### **AWS Permissions Required**
Your AWS user/role needs permissions for:
- **S3**: Create buckets, upload/download objects
- **DynamoDB**: Create tables, read/write items
- **Lambda**: Create functions, manage code
- **AppSync**: Create GraphQL APIs
- **Cognito**: Create user pools
- **Amplify**: Deploy frontend applications
- **Bedrock**: Access Nova Premier model
- **IAM**: Create roles and policies
- **CloudFormation**: Deploy stacks

### **AWS Services Setup**
```bash
# Verify AWS CLI configuration
aws sts get-caller-identity

# Ensure you have access to Bedrock Nova Premier
aws bedrock list-foundation-models --region us-east-1 | grep nova-premier
```

## 🏗️ **Step 1: Infrastructure Deployment**

### **1.1 Clone and Setup**
```bash
# Clone the repository
git clone <your-repo-url>
cd postmark

# Install CDK dependencies
cd infrastructure
npm install

# Verify CDK installation
npx cdk --version
```

### **1.2 Configure CDK**
```bash
# Bootstrap CDK (first time only)
npx cdk bootstrap

# Review what will be deployed
npx cdk diff
```

### **1.3 Deploy Infrastructure**
```bash
# Deploy all AWS resources
npx cdk deploy --require-approval never

# This creates:
# - S3 bucket for file storage
# - 3 DynamoDB tables
# - 10+ Lambda functions
# - AppSync GraphQL API
# - Cognito user pool
# - Amplify app for frontend
```

### **1.4 Note the Outputs**
After deployment, save these important outputs:
```
ResumeRankingStack.GraphQLApiGraphQLApiUrl = https://xxx.appsync-api.us-east-1.amazonaws.com/graphql
ResumeRankingStack.AuthUserPoolId = us-east-1_xxxxxxx
ResumeRankingStack.AuthUserPoolClientId = xxxxxxxxxxxxxxxxxx
ResumeRankingStack.AuthIdentityPoolId = us-east-1:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
ResumeRankingStack.S3BucketName = resume-ranking-bucket-xxxxx-us-east-1
ResumeRankingStack.WebhookUrl = https://xxx.execute-api.us-east-1.amazonaws.com/prod/webhook
```

## 🎨 **Step 2: Auto-Configure Frontend**

### **2.1 Automatic Configuration from CDK Outputs**
```bash
# Automatically extract CDK outputs and configure frontend
python3 scripts/update-frontend-config.py

# This script will:
# - Extract all CDK outputs from CloudFormation
# - Update .env file with real AWS resource values
# - Generate frontend/static/config.js from template using environment variables
# - Provide deployment-ready configuration without hardcoded values
```

The script output will show:
```
🚀 Auto-updating frontend configuration from CDK outputs
============================================================
🔍 Fetching CDK outputs for stack: ResumeRankingStack
  ✅ S3BucketName: resume-ranking-bucket-xxxxx-us-east-1
  ✅ UserPoolId: us-east-1_xxxxxxx
  ✅ GraphQLApiUrl: https://xxx.appsync-api.us-east-1.amazonaws.com/graphql
  ...
📝 Updating .env file
🎨 Generating config.js from template
✅ Configuration update complete!
```

### **2.2 Template-Based Configuration**
The system uses a template-based approach for secure configuration:

**Template file** (`frontend/static/config.js.template`):
```javascript
window.AWS_CONFIG = {
    region: '${AWS_REGION}',
    userPoolId: '${USER_POOL_ID}',
    userPoolWebClientId: '${USER_POOL_CLIENT_ID}',
    identityPoolId: '${IDENTITY_POOL_ID}',
    graphqlEndpoint: '${GRAPHQL_ENDPOINT}',
    apiId: '${API_ID}'
};
```

**Environment variables** (`.env`):
```bash
AWS_REGION=us-east-1
USER_POOL_ID=us-east-1_xxxxxxx
USER_POOL_CLIENT_ID=xxxxxxxxxx
IDENTITY_POOL_ID=us-east-1:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
GRAPHQL_ENDPOINT=https://xxx.appsync-api.us-east-1.amazonaws.com/graphql
API_ID=xxxxxxxxxx
```

### **2.3 Deploy Frontend**
```bash
# Deploy frontend to Amplify (automatically generates config from template)
python3 scripts/deploy-frontend.py
```

The deployment script will:
1. Generate `config.js` from template using environment variables
2. Create deployment package
3. Upload to Amplify
4. Start deployment

### **2.4 Access Your Application**
The deployment script will output your application URL:
```
📱 Your app will be available at: https://xxxxx.amplifyapp.com
```

## 🔐 **Step 3: Authentication Setup**

### **3.1 Create Admin User**
```bash
# Create your first admin user
aws cognito-idp admin-create-user \
    --user-pool-id us-east-1_YOUR-USER-POOL-ID \
    --username admin \
    --user-attributes Name=email,Value=your-email@example.com \
    --temporary-password TempPass123! \
    --message-action SUPPRESS
```

### **3.2 Set Permanent Password**
```bash
# Set permanent password
aws cognito-idp admin-set-user-password \
    --user-pool-id us-east-1_YOUR-USER-POOL-ID \
    --username admin \
    --password YourSecurePassword123! \
    --permanent
```

## 📧 **Step 4: Email Integration (Postmark)**

### **4.1 Configure Postmark Webhook**
1. Log into your Postmark account
2. Go to your server settings
3. Add a webhook with URL: `https://YOUR-API-GATEWAY-ID.execute-api.us-east-1.amazonaws.com/prod/webhook`
4. Enable "Inbound" webhook type

### **4.2 Test Email Processing**
Send a test email with a PDF resume attachment to your monitored email address.

## 🧪 **Step 5: Testing & Verification**

### **5.1 Upload Sample Resumes**
```bash
# Upload sample resumes to S3
cd samples
for file in *.pdf; do
    aws s3 cp "$file" s3://YOUR-BUCKET-NAME/
done
```

### **5.2 Monitor Processing**
```bash
# Monitor the processing progress
python3 scripts/monitor_processing.py
```

### **5.3 Access Dashboard**
1. Visit your Amplify app URL
2. Login with your admin credentials
3. Verify all resumes appear with AI analysis

## 🔧 **Step 6: Advanced Configuration**

### **6.1 Custom Domain (Optional)**
```bash
# Add custom domain to Amplify app
aws amplify create-domain-association \
    --app-id YOUR-AMPLIFY-APP-ID \
    --domain-name yourdomain.com \
    --sub-domain-settings prefix=resume,branchName=main
```

### **6.2 SSL Certificate (Optional)**
```bash
# Request SSL certificate
aws acm request-certificate \
    --domain-name yourdomain.com \
    --validation-method DNS
```

### **6.3 CloudWatch Alarms**
```bash
# Set up monitoring alarms
aws cloudwatch put-metric-alarm \
    --alarm-name "ResumeProcessingErrors" \
    --alarm-description "Alert on processing errors" \
    --metric-name Errors \
    --namespace AWS/Lambda \
    --statistic Sum \
    --period 300 \
    --threshold 5 \
    --comparison-operator GreaterThanThreshold
```

## 📊 **Step 7: Performance Optimization**

### **7.1 DynamoDB Auto Scaling**
```bash
# Enable auto scaling for DynamoDB tables
aws application-autoscaling register-scalable-target \
    --service-namespace dynamodb \
    --resource-id table/resume-ranking-attachments \
    --scalable-dimension dynamodb:table:ReadCapacityUnits \
    --min-capacity 5 \
    --max-capacity 100
```

### **7.2 Lambda Concurrency Limits**
```bash
# Set reserved concurrency for critical functions
aws lambda put-reserved-concurrency-config \
    --function-name resume-ranking-s3-processor \
    --reserved-concurrent-executions 10
```

## 🔄 **Step 8: Backup & Recovery**

### **8.1 Enable Point-in-Time Recovery**
```bash
# Enable PITR for DynamoDB tables
aws dynamodb update-continuous-backups \
    --table-name resume-ranking-attachments \
    --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true
```

### **8.2 S3 Versioning**
```bash
# Enable S3 versioning
aws s3api put-bucket-versioning \
    --bucket YOUR-BUCKET-NAME \
    --versioning-configuration Status=Enabled
```

## 🚨 **Troubleshooting**

### **Common Deployment Issues**

#### **CDK Bootstrap Error**
```bash
# If bootstrap fails, try with explicit region
npx cdk bootstrap aws://ACCOUNT-ID/us-east-1
```

#### **Permission Denied**
```bash
# Check your AWS credentials
aws sts get-caller-identity

# Verify IAM permissions
aws iam get-user
```

#### **Bedrock Access Denied**
```bash
# Request access to Bedrock Nova Premier model
# Go to AWS Console > Bedrock > Model Access
# Request access to Nova Premier model
```

#### **Frontend Not Loading**
1. Check config.js has correct values
2. Verify Amplify deployment succeeded
3. Check browser console for errors
4. Ensure CORS is configured correctly
5. **NEW**: Verify config.js was generated from template

#### **Configuration Issues**
```bash
# Check if config.js was generated properly
cat frontend/static/config.js

# Regenerate config from template
python3 scripts/update-frontend-config.py

# Check environment variables
cat .env

# Verify template exists
cat frontend/static/config.js.template
```

### **Debugging Commands**

#### **Check Lambda Logs**
```bash
# View recent Lambda logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/resume-ranking"

# Tail specific function logs
aws logs tail /aws/lambda/resume-ranking-s3-processor --follow
```

#### **Check DynamoDB Data**
```bash
# Count items in tables
aws dynamodb scan --table-name resume-ranking-attachments --select COUNT
aws dynamodb scan --table-name resume-ranking-parsed-resumes --select COUNT
aws dynamodb scan --table-name resume-ranking-resume-information --select COUNT
```

#### **Check S3 Contents**
```bash
# List S3 bucket contents
aws s3 ls s3://YOUR-BUCKET-NAME/ --recursive
```

## 🔄 **Updates & Maintenance**

### **Updating Infrastructure**
```bash
# Pull latest changes
git pull origin main

# Deploy updates
cd infrastructure
npx cdk deploy
```

### **Updating Frontend**
```bash
# Deploy frontend changes
python3 scripts/deploy-frontend.py
```

### **Database Maintenance**
```bash
# Clear all data (use with caution)
python3 scripts/clear-all-resources.py

# Monitor system health
python3 scripts/monitor_processing.py
```

## 📈 **Scaling Considerations**

### **For High Volume (1000+ resumes/day)**
1. **Increase Lambda concurrency limits**
2. **Enable DynamoDB auto-scaling**
3. **Use S3 Transfer Acceleration**
4. **Set up CloudFront for frontend**
5. **Implement SQS for processing queue**

### **For Enterprise Use**
1. **Multi-region deployment**
2. **VPC endpoints for security**
3. **AWS WAF for API protection**
4. **Enhanced monitoring with X-Ray**
5. **Automated backup strategies**

## 💰 **Cost Optimization**

### **Estimated Monthly Costs (1000 resumes) - CORRECTED**
- **Lambda**: ~$0.20 (1,000 invocations)
- **DynamoDB**: ~$3.75 (3,000 writes + 10,000 reads)
- **S3**: ~$2.30 (10GB storage + requests)
- **Bedrock**: ~$15.00 (Nova Premier analysis)
- **AppSync**: ~$4.00 (1 million requests)
- **Amplify**: ~$3.00 (moderate traffic)
- **Cognito**: ~$2.75 (5,000 MAU)
- **CloudWatch**: ~$2.00 (moderate logging)
- **Total**: ~$33.00/month

### **Cost Reduction Tips**
1. Use S3 Intelligent Tiering
2. Set DynamoDB to On-Demand pricing
3. Optimize Lambda memory allocation
4. Use CloudWatch to monitor unused resources

## 🎉 **Deployment Complete!**

Your AI Resume Ranking System is now fully deployed and ready for production use!

### **Next Steps**
1. **Test the system** with sample resumes
2. **Configure email integration** with Postmark
3. **Set up monitoring** and alerts
4. **Train users** on the dashboard features
5. **Scale as needed** based on usage

### **Support Resources**
- **AWS Documentation**: https://docs.aws.amazon.com/
- **CDK Documentation**: https://docs.aws.amazon.com/cdk/
- **Bedrock Documentation**: https://docs.aws.amazon.com/bedrock/
- **Project Issues**: GitHub Issues page

---

**🚀 Your enterprise-grade AI Resume Ranking System is now live and ready to revolutionize your talent management process!**
