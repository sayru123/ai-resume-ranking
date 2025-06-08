import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as s3n from 'aws-cdk-lib/aws-s3-notifications';
import { Duration } from 'aws-cdk-lib';
import * as path from 'path';

export interface LambdaConstructProps {
  readonly appName: string;
  readonly s3Bucket: s3.IBucket;
  readonly attachmentsTable: dynamodb.Table;
  readonly parsedResumesTable: dynamodb.Table;
  readonly resumeInformationTable: dynamodb.Table;
}

export class LambdaConstruct extends Construct {
  public readonly listResumesFunction: lambda.Function;
  public readonly getResumeFunction: lambda.Function;
  public readonly getResumeAnalysisFunction: lambda.Function;
  public readonly processResumeFunction: lambda.Function;
  public readonly triggerS3MonitorFunction: lambda.Function;
  public readonly s3ProcessorFunction: lambda.Function;
  public readonly getSystemHealthFunction: lambda.Function;
  public readonly listRankedResumesFunction: lambda.Function;
  public readonly listResumeAnalysesFunction: lambda.Function;
  public readonly listParsedResumesFunction: lambda.Function;
  public readonly emailNotifierFunction: lambda.Function;

  constructor(scope: Construct, id: string, props: LambdaConstructProps) {
    super(scope, id);

    // Common environment variables (removed AWS_REGION as it's reserved)
    const commonEnvironment = {
      ATTACHMENTS_TABLE: props.attachmentsTable.tableName,
      PARSED_RESUMES_TABLE: props.parsedResumesTable.tableName,
      RESUME_INFORMATION_TABLE: props.resumeInformationTable.tableName,
      S3_BUCKET: props.s3Bucket.bucketName,
    };

    // Common Lambda configuration (standard, no optimizations)
    const commonLambdaProps = {
      runtime: lambda.Runtime.PYTHON_3_11,
      timeout: Duration.seconds(30),
      memorySize: 128,
      environment: commonEnvironment,
    };

    // GraphQL Resolver Functions
    this.listResumesFunction = new lambda.Function(this, 'ListResumesFunction', {
      ...commonLambdaProps,
      functionName: `${props.appName}-list-resumes`,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/graphql-resolvers/list-resumes')),
      description: 'GraphQL resolver for listing all resumes',
    });

    this.getResumeFunction = new lambda.Function(this, 'GetResumeFunction', {
      ...commonLambdaProps,
      functionName: `${props.appName}-get-resume`,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/graphql-resolvers/get-resume')),
      description: 'GraphQL resolver for getting a specific resume',
    });

    this.getResumeAnalysisFunction = new lambda.Function(this, 'GetResumeAnalysisFunction', {
      ...commonLambdaProps,
      functionName: `${props.appName}-get-resume-analysis`,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/graphql-resolvers/get-resume-analysis')),
      description: 'GraphQL resolver for getting resume analysis',
    });

    this.processResumeFunction = new lambda.Function(this, 'ProcessResumeFunction', {
      ...commonLambdaProps,
      functionName: `${props.appName}-process-resume`,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/graphql-resolvers/process-resume')),
      description: 'GraphQL resolver for processing a specific resume',
      timeout: Duration.minutes(5), // Longer timeout for Bedrock processing
    });

    this.triggerS3MonitorFunction = new lambda.Function(this, 'TriggerS3MonitorFunction', {
      ...commonLambdaProps,
      functionName: `${props.appName}-trigger-s3-monitor`,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/graphql-resolvers/trigger-s3-monitor')),
      description: 'GraphQL resolver for triggering S3 monitoring',
      timeout: Duration.minutes(2),
    });

    this.getSystemHealthFunction = new lambda.Function(this, 'GetSystemHealthFunction', {
      ...commonLambdaProps,
      functionName: `${props.appName}-get-system-health`,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/graphql-resolvers/get-system-health')),
      description: 'GraphQL resolver for getting system health',
    });

    // List Ranked Resumes Function
    this.listRankedResumesFunction = new lambda.Function(this, 'ListRankedResumesFunction', {
      ...commonLambdaProps,
      functionName: `${props.appName}-list-ranked-resumes`,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/graphql-resolvers/list-ranked-resumes')),
      description: 'GraphQL resolver for listing ranked resumes with AI analysis',
    });

    // List Resume Analyses Function
    this.listResumeAnalysesFunction = new lambda.Function(this, 'ListResumeAnalysesFunction', {
      ...commonLambdaProps,
      functionName: `${props.appName}-list-resume-analyses`,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/graphql-resolvers/list-resume-analyses')),
      description: 'GraphQL resolver for listing all resume analyses',
    });

    // List Parsed Resumes Function
    this.listParsedResumesFunction = new lambda.Function(this, 'ListParsedResumesFunction', {
      ...commonLambdaProps,
      functionName: `${props.appName}-list-parsed-resumes`,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/graphql-resolvers/list-parsed-resumes')),
      description: 'GraphQL resolver for listing all parsed resumes',
    });

    // S3 Event Processor Function with Dependencies
    this.s3ProcessorFunction = new lambda.Function(this, 'S3ProcessorFunction', {
      ...commonLambdaProps,
      functionName: `${props.appName}-s3-processor`,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/s3-processor'), {
        bundling: {
          image: lambda.Runtime.PYTHON_3_9.bundlingImage,
          command: [
            'bash', '-c',
            'pip install -r requirements.txt -t /asset-output && cp -au . /asset-output'
          ],
        },
      }),
      description: 'Processes resume files uploaded to S3 with REAL PDF extraction and AI analysis',
      timeout: Duration.minutes(15), // Longer timeout for PDF processing and AI analysis
      memorySize: 1024, // More memory for PDF processing and Bedrock calls
      environment: {
        ...commonEnvironment,
        EMAIL_NOTIFIER_FUNCTION_NAME: `${props.appName}-email-notifier`,
      },
    });

    // Email Notifier Function
    this.emailNotifierFunction = new lambda.Function(this, 'EmailNotifierFunction', {
      ...commonLambdaProps,
      functionName: `${props.appName}-email-notifier`,
      handler: 'index.lambda_handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/email-notifier'), {
        bundling: {
          image: lambda.Runtime.PYTHON_3_11.bundlingImage,
          command: [
            'bash', '-c',
            'pip install requests -t /asset-output && cp -au . /asset-output'
          ],
        },
      }),
      description: 'Sends email notifications via Postmark API when resume analysis is complete',
      timeout: Duration.seconds(60), // Timeout for HTTP requests
      memorySize: 256, // Moderate memory for HTTP requests
      environment: {
        ...commonEnvironment,
        POSTMARK_SERVER_TOKEN: process.env.POSTMARK_SERVER_TOKEN || 'your-postmark-server-token-here',
        NOTIFICATION_EMAIL: process.env.NOTIFICATION_EMAIL || 'your-notification-email@example.com',
        FROM_EMAIL: process.env.FROM_EMAIL || 'your-from-email@example.com',
      },
    });

    // Grant DynamoDB permissions to all functions
    const allFunctions = [
      this.listResumesFunction,
      this.getResumeFunction,
      this.getResumeAnalysisFunction,
      this.processResumeFunction,
      this.triggerS3MonitorFunction,
      this.s3ProcessorFunction,
      this.getSystemHealthFunction,
      this.listResumeAnalysesFunction,
      this.listParsedResumesFunction,
      this.emailNotifierFunction,
    ];

    allFunctions.forEach(func => {
      props.attachmentsTable.grantReadWriteData(func);
      props.parsedResumesTable.grantReadWriteData(func);
      props.resumeInformationTable.grantReadWriteData(func);
      props.s3Bucket.grantReadWrite(func);
    });

    // Grant Bedrock permissions
    const bedrockPolicy = new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'bedrock:InvokeModel',
        'bedrock:InvokeModelWithResponseStream',
        'bedrock:ListFoundationModels',
        'bedrock:GetFoundationModel',
      ],
      resources: ['*'],
    });

    allFunctions.forEach(func => {
      func.addToRolePolicy(bedrockPolicy);
    });

    // Grant Lambda invoke permissions for process-resume and trigger-s3-monitor functions
    const lambdaInvokePolicy = new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['lambda:InvokeFunction'],
      resources: [this.s3ProcessorFunction.functionArn, this.emailNotifierFunction.functionArn],
    });

    this.processResumeFunction.addToRolePolicy(lambdaInvokePolicy);
    this.triggerS3MonitorFunction.addToRolePolicy(lambdaInvokePolicy);
    
    // Grant S3 processor permission to invoke email notifier
    const emailInvokePolicy = new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['lambda:InvokeFunction'],
      resources: [this.emailNotifierFunction.functionArn],
    });
    
    this.s3ProcessorFunction.addToRolePolicy(emailInvokePolicy);

    // Set up S3 event trigger for the processor function
    props.s3Bucket.addEventNotification(
      s3.EventType.OBJECT_CREATED,
      new s3n.LambdaDestination(this.s3ProcessorFunction),
      {
        suffix: '.pdf', // Only trigger for PDF files
      }
    );
  }
}
