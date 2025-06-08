import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';

// Import our new constructs
import { AuthConstruct } from './constructs/auth-construct';
import { DatabaseConstruct } from './constructs/database-construct';
import { LambdaConstruct } from './constructs/lambda-construct';
import { ApiConstruct } from './constructs/api-construct';

export class ResumeRankingStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const appName = 'resume-ranking';

    // EXISTING RESOURCES (Keep as-is for backward compatibility)
    
    // S3 Bucket for resume storage (existing)
    const resumeBucket = new s3.Bucket(this, 'ResumeBucket', {
      bucketName: `resume-ranking-bucket-${this.account}-${this.region}`,
      versioned: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // For testing - remove in production
      autoDeleteObjects: true, // For testing - remove in production
    });

    // IAM Role for existing Lambda (keep as-is)
    const lambdaRole = new iam.Role(this, 'WebhookLambdaRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
      inlinePolicies: {
        S3Access: new iam.PolicyDocument({
          statements: [
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: ['s3:GetObject', 's3:PutObject', 's3:ListBucket'],
              resources: [
                resumeBucket.bucketArn,
                `${resumeBucket.bucketArn}/*`,
              ],
            }),
          ],
        }),
        BedrockAccess: new iam.PolicyDocument({
          statements: [
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: ['bedrock:InvokeModel', 'bedrock:ListFoundationModels'],
              resources: ['*'],
            }),
          ],
        }),
      },
    });

    // Lambda Function for Postmark Webhook (existing - keep as-is)
    const webhookLambda = new lambda.Function(this, 'WebhookHandler', {
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: 'lambda_function.handler',
      code: lambda.Code.fromAsset('lambda/webhook-handler'),
      role: lambdaRole,
      timeout: cdk.Duration.seconds(30),
      memorySize: 256,
      environment: {
        S3_BUCKET: resumeBucket.bucketName,
      },
    });

    // API Gateway for webhook endpoint (existing - keep as-is)
    const api = new apigateway.RestApi(this, 'WebhookApi', {
      restApiName: 'Resume Webhook API',
      description: 'API for Postmark webhook integration',
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
      },
    });

    const webhookResource = api.root.addResource('webhook');
    webhookResource.addMethod('POST', new apigateway.LambdaIntegration(webhookLambda));

    // NEW SERVERLESS ARCHITECTURE COMPONENTS

    // Authentication with Cognito
    const auth = new AuthConstruct(this, 'Auth', {
      appName,
    });

    // DynamoDB Database
    const database = new DatabaseConstruct(this, 'Database', {
      appName,
    });

    // Lambda Functions for GraphQL resolvers and S3 processing
    const lambdaFunctions = new LambdaConstruct(this, 'LambdaFunctions', {
      appName,
      s3Bucket: resumeBucket,
      attachmentsTable: database.attachmentsTable,
      parsedResumesTable: database.parsedResumesTable,
      resumeInformationTable: database.resumeInformationTable,
    });

    // AppSync GraphQL API
    const graphqlApi = new ApiConstruct(this, 'GraphQLApi', {
      appName,
      userPool: auth.userPool,
      listResumesFunction: lambdaFunctions.listResumesFunction,
      getResumeFunction: lambdaFunctions.getResumeFunction,
      getResumeAnalysisFunction: lambdaFunctions.getResumeAnalysisFunction,
      processResumeFunction: lambdaFunctions.processResumeFunction,
      triggerS3MonitorFunction: lambdaFunctions.triggerS3MonitorFunction,
      getSystemHealthFunction: lambdaFunctions.getSystemHealthFunction,
      listResumeAnalysesFunction: lambdaFunctions.listResumeAnalysesFunction,
      listParsedResumesFunction: lambdaFunctions.listParsedResumesFunction,
    });

    // OUTPUTS (existing + new)
    
    // Existing outputs
    new cdk.CfnOutput(this, "WebhookUrl", {
      value: `${api.url}webhook`,
      description: "Postmark webhook URL",
    });

    new cdk.CfnOutput(this, "S3BucketName", {
      value: resumeBucket.bucketName,
      description: "S3 bucket for resume storage",
    });

    new cdk.CfnOutput(this, "ApiGatewayUrl", {
      value: api.url,
      description: "API Gateway base URL",
    });

    // New outputs for frontend configuration
    new cdk.CfnOutput(this, "GraphQLApiUrl", {
      value: graphqlApi.api.attrGraphQlUrl,
      description: "AppSync GraphQL API URL",
    });

    new cdk.CfnOutput(this, "UserPoolId", {
      value: auth.userPool.userPoolId,
      description: "Cognito User Pool ID",
    });

    new cdk.CfnOutput(this, "UserPoolClientId", {
      value: auth.userPoolClient.userPoolClientId,
      description: "Cognito User Pool Client ID",
    });

    new cdk.CfnOutput(this, "IdentityPoolId", {
      value: auth.identityPool.ref,
      description: "Cognito Identity Pool ID",
    });

    new cdk.CfnOutput(this, "Region", {
      value: this.region,
      description: "AWS Region",
    });

    new cdk.CfnOutput(this, "AppName", {
      value: appName,
      description: "Application Name",
    });
  }
}
