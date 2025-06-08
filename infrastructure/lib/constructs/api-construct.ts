import { Construct } from 'constructs';
import * as appsync from 'aws-cdk-lib/aws-appsync';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import * as iam from 'aws-cdk-lib/aws-iam';
import { CfnOutput } from 'aws-cdk-lib';
import * as path from 'path';

export interface ApiConstructProps {
  readonly appName: string;
  readonly userPool: cognito.UserPool;
  readonly listResumesFunction: lambda.Function;
  readonly getResumeFunction: lambda.Function;
  readonly getResumeAnalysisFunction: lambda.Function;
  readonly processResumeFunction: lambda.Function;
  readonly triggerS3MonitorFunction: lambda.Function;
  readonly getSystemHealthFunction: lambda.Function;
  readonly listResumeAnalysesFunction: lambda.Function;
  readonly listParsedResumesFunction: lambda.Function;
}

export class ApiConstruct extends Construct {
  public readonly api: appsync.CfnGraphQLApi;
  private roleCounter = 0;

  constructor(scope: Construct, id: string, props: ApiConstructProps) {
    super(scope, id);

    // Read the GraphQL schema
    const fs = require('fs');
    const schemaPath = path.join(__dirname, '../../graphql/schema.graphql');
    const schema = fs.readFileSync(schemaPath, 'utf8');

    // Create AppSync GraphQL API using L1 construct (without logging for now)
    this.api = new appsync.CfnGraphQLApi(this, 'ResumeRankingApi', {
      name: `${props.appName}-graphql-api`,
      authenticationType: 'AMAZON_COGNITO_USER_POOLS',
      userPoolConfig: {
        userPoolId: props.userPool.userPoolId,
        awsRegion: 'us-east-1',
        defaultAction: 'ALLOW',
      },
      additionalAuthenticationProviders: [
        {
          authenticationType: 'AWS_IAM',
        },
      ],
      xrayEnabled: true,
    });

    // Create GraphQL Schema
    const graphqlSchema = new appsync.CfnGraphQLSchema(this, 'Schema', {
      apiId: this.api.attrApiId,
      definition: schema,
    });

    // Create Lambda Data Sources first
    const listResumesDataSource = this.createDataSource('ListResumes', props.listResumesFunction);
    const getResumeDataSource = this.createDataSource('GetResume', props.getResumeFunction);
    const getResumeAnalysisDataSource = this.createDataSource('GetResumeAnalysis', props.getResumeAnalysisFunction);
    const listResumeAnalysesDataSource = this.createDataSource('ListResumeAnalyses', props.listResumeAnalysesFunction);
    const listParsedResumesDataSource = this.createDataSource('ListParsedResumes', props.listParsedResumesFunction);
    const getSystemHealthDataSource = this.createDataSource('GetSystemHealth', props.getSystemHealthFunction);
    const processResumeDataSource = this.createDataSource('ProcessResume', props.processResumeFunction);
    const triggerS3MonitorDataSource = this.createDataSource('TriggerS3Monitor', props.triggerS3MonitorFunction);

    // Create Resolvers after data sources
    this.createResolver('ListResumes', 'Query', 'listResumes', listResumesDataSource, graphqlSchema);
    this.createResolver('GetResume', 'Query', 'getResume', getResumeDataSource, graphqlSchema);
    this.createResolver('GetResumeAnalysis', 'Query', 'getResumeAnalysis', getResumeAnalysisDataSource, graphqlSchema);
    this.createResolver('ListResumeAnalyses', 'Query', 'listResumeAnalyses', listResumeAnalysesDataSource, graphqlSchema);
    this.createResolver('ListParsedResumes', 'Query', 'listParsedResumes', listParsedResumesDataSource, graphqlSchema);
    this.createResolver('GetSystemHealth', 'Query', 'getSystemHealth', getSystemHealthDataSource, graphqlSchema);
    this.createResolver('GetAnalytics', 'Query', 'getAnalytics', getSystemHealthDataSource, graphqlSchema);
    this.createResolver('ProcessResume', 'Mutation', 'processResume', processResumeDataSource, graphqlSchema);
    this.createResolver('TriggerS3Monitor', 'Mutation', 'triggerS3Monitor', triggerS3MonitorDataSource, graphqlSchema);

    // Outputs
    new CfnOutput(this, 'GraphQLApiUrl', {
      value: this.api.attrGraphQlUrl,
      description: 'AppSync GraphQL API URL',
    });

    new CfnOutput(this, 'GraphQLApiId', {
      value: this.api.attrApiId,
      description: 'AppSync GraphQL API ID',
    });
  }

  private createDataSource(name: string, lambdaFunction: lambda.Function): appsync.CfnDataSource {
    // Create unique role for each data source
    const role = new iam.Role(this, `DataSourceRole${name}${++this.roleCounter}`, {
      assumedBy: new iam.ServicePrincipal('appsync.amazonaws.com'),
    });

    role.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['lambda:InvokeFunction'],
      resources: [lambdaFunction.functionArn],
    }));

    // Create Lambda Data Source
    const dataSource = new appsync.CfnDataSource(this, `${name}DataSource`, {
      apiId: this.api.attrApiId,
      name: `${name}DataSource`,
      type: 'AWS_LAMBDA',
      lambdaConfig: {
        lambdaFunctionArn: lambdaFunction.functionArn,
      },
      serviceRoleArn: role.roleArn,
    });

    dataSource.addDependency(this.api);
    return dataSource;
  }

  private createResolver(
    name: string,
    typeName: string,
    fieldName: string,
    dataSource: appsync.CfnDataSource,
    schema: appsync.CfnGraphQLSchema
  ): appsync.CfnResolver {
    // Create Resolver
    const resolver = new appsync.CfnResolver(this, `${name}Resolver`, {
      apiId: this.api.attrApiId,
      typeName: typeName,
      fieldName: fieldName,
      dataSourceName: dataSource.name,
      requestMappingTemplate: `{
        "version": "2017-02-28",
        "operation": "Invoke",
        "payload": $util.toJson($context)
      }`,
      responseMappingTemplate: `$util.toJson($context.result)`,
    });

    resolver.addDependency(dataSource);
    resolver.addDependency(schema);
    return resolver;
  }
}
