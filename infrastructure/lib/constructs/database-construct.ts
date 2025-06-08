import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { CfnOutput, RemovalPolicy } from 'aws-cdk-lib';

export interface DatabaseConstructProps {
  readonly appName: string;
}

export class DatabaseConstruct extends Construct {
  public readonly attachmentsTable: dynamodb.Table;
  public readonly parsedResumesTable: dynamodb.Table;
  public readonly resumeInformationTable: dynamodb.Table;

  constructor(scope: Construct, id: string, props: DatabaseConstructProps) {
    super(scope, id);

    // Attachments Table - Stores resume files and metadata
    this.attachmentsTable = new dynamodb.Table(this, 'AttachmentsTable', {
      tableName: `${props.appName}-attachments`,
      partitionKey: {
        name: 'id',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: RemovalPolicy.DESTROY, // For development
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: true,
      },
      timeToLiveAttribute: 'ttl', // Optional TTL for cleanup
    });

    // Add GSI for filename queries
    this.attachmentsTable.addGlobalSecondaryIndex({
      indexName: 'filename-index',
      partitionKey: {
        name: 'filename',
        type: dynamodb.AttributeType.STRING,
      },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    // Parsed Resumes Table - Stores extracted text content
    this.parsedResumesTable = new dynamodb.Table(this, 'ParsedResumesTable', {
      tableName: `${props.appName}-parsed-resumes`,
      partitionKey: {
        name: 'id',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: RemovalPolicy.DESTROY, // For development
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: true,
      },
    });

    // Add GSI for attachment_id queries
    this.parsedResumesTable.addGlobalSecondaryIndex({
      indexName: 'attachment-id-index',
      partitionKey: {
        name: 'attachmentId',
        type: dynamodb.AttributeType.STRING,
      },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    // Resume Information Table - Stores AI analysis results
    this.resumeInformationTable = new dynamodb.Table(this, 'ResumeInformationTable', {
      tableName: `${props.appName}-resume-information`,
      partitionKey: {
        name: 'id',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: RemovalPolicy.DESTROY, // For development
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: true,
      },
    });

    // Add GSI for parsed_resume_id queries
    this.resumeInformationTable.addGlobalSecondaryIndex({
      indexName: 'parsed-resume-id-index',
      partitionKey: {
        name: 'parsedResumeId',
        type: dynamodb.AttributeType.STRING,
      },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    // Outputs
    new CfnOutput(this, 'AttachmentsTableName', {
      value: this.attachmentsTable.tableName,
      description: 'DynamoDB Attachments Table Name',
    });

    new CfnOutput(this, 'ParsedResumesTableName', {
      value: this.parsedResumesTable.tableName,
      description: 'DynamoDB Parsed Resumes Table Name',
    });

    new CfnOutput(this, 'ResumeInformationTableName', {
      value: this.resumeInformationTable.tableName,
      description: 'DynamoDB Resume Information Table Name',
    });
  }
}
