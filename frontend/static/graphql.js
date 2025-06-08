// GraphQL Queries
window.GRAPHQL_QUERIES = {
    GET_SYSTEM_HEALTH: `
        query GetSystemHealth {
            getSystemHealth {
                status
                totalResumes
                processedResumes
                successRate
                lastProcessedAt
            }
        }
    `,
    
    LIST_RESUMES: `
        query ListResumes {
            listResumes {
                id
                filename
                contentType
                size
                processingStatus
                createdAt
            }
        }
    `,
    
    GET_RESUME_ANALYSIS: `
        query GetResumeAnalysis($attachmentId: String!) {
            getResumeAnalysis(attachmentId: $attachmentId) {
                id
                candidate_name
                experience_years
                experience_level
                overall_score
                skill_diversity
                fit_assessment
                key_skills
                top_strengths
                top_recommendations
                summary
                created_at
            }
        }
    `,
    
    TRIGGER_S3_MONITOR: `
        mutation TriggerS3Monitor {
            triggerS3Monitor {
                message
                filesProcessed
            }
        }
    `,
    
    PROCESS_RESUME: `
        mutation ProcessResume($s3Key: String!) {
            processResume(s3Key: $s3Key) {
                message
                status
            }
        }
    `
};

// Working GraphQL client for AppSync
class GraphQLClient {
    constructor() {
        this.endpoint = window.AWS_CONFIG.graphqlEndpoint;
    }

    async query(query, variables = {}) {
        const token = authService.getIdToken();
        if (!token) {
            throw new Error('Not authenticated');
        }

        const response = await fetch(this.endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': token
            },
            body: JSON.stringify({
                query,
                variables
            })
        });

        const result = await response.json();
        
        if (result.errors) {
            console.error('GraphQL Error:', result.errors);
            throw new Error(result.errors[0].message);
        }
        
        return result.data;
    }

    async mutation(mutation, variables = {}) {
        return this.query(mutation, variables);
    }
}

// Initialize GraphQL client
const graphqlClient = new GraphQLClient();

// Working API service functions
window.apiService = {
    async getSystemHealth() {
        try {
            const data = await graphqlClient.query(window.GRAPHQL_QUERIES.GET_SYSTEM_HEALTH);
            return data.getSystemHealth;
        } catch (error) {
            console.error('Error fetching system health:', error);
            throw error;
        }
    },

    async listResumes() {
        try {
            const data = await graphqlClient.query(window.GRAPHQL_QUERIES.LIST_RESUMES);
            return data.listResumes || [];
        } catch (error) {
            console.error('Error fetching resumes:', error);
            throw error;
        }
    },

    async getResumeAnalysis(attachmentId) {
        try {
            const data = await graphqlClient.query(
                window.GRAPHQL_QUERIES.GET_RESUME_ANALYSIS,
                { attachmentId }
            );
            return data.getResumeAnalysis;
        } catch (error) {
            console.error('Error fetching resume analysis:', error);
            throw error;
        }
    },

    async triggerS3Monitor() {
        try {
            const data = await graphqlClient.mutation(window.GRAPHQL_QUERIES.TRIGGER_S3_MONITOR);
            return data.triggerS3Monitor;
        } catch (error) {
            console.error('Error triggering S3 monitor:', error);
            throw error;
        }
    },

    async listParsedResumes() {
        try {
            const query = `
                query ListParsedResumes {
                    listParsedResumes {
                        id
                        attachmentId
                        attachment_id
                        parsingStatus
                        createdAt
                    }
                }
            `;
            
            const data = await graphqlClient.query(query);
            return data.listParsedResumes;
        } catch (error) {
            console.error('Error fetching parsed resumes:', error);
            throw error;
        }
    },

    async listResumeAnalyses() {
        try {
            const query = `
                query ListResumeAnalyses {
                    listResumeAnalyses {
                        id
                        parsed_resume_id
                        candidate_name
                        experience_years
                        experience_level
                        overall_score
                        skill_diversity
                        fit_assessment
                        key_skills
                        strengths
                        recommendations
                        detailed_summary
                        key_achievements
                        education
                        certifications
                        skill_breakdown
                        total_skills
                        extraction_confidence
                        created_at
                    }
                }
            `;
            
            const data = await graphqlClient.query(query);
            return data.listResumeAnalyses;
        } catch (error) {
            console.error('Error fetching resume analyses:', error);
            throw error;
        }
    },

    async processResume(s3Key) {
        try {
            const data = await graphqlClient.mutation(
                window.GRAPHQL_QUERIES.PROCESS_RESUME,
                { s3Key }
            );
            return data.processResume;
        } catch (error) {
            console.error('Error processing resume:', error);
            throw error;
        }
    }
};
