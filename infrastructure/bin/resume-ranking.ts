#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { ResumeRankingStack } from '../lib/resume-ranking-stack';

const app = new cdk.App();
new ResumeRankingStack(app, 'ResumeRankingStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
});
