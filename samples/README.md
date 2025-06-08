# Sample Resume Files for Demo

This folder contains 10 professionally crafted sample PDF resumes for demonstrating the Resume Ranking System's AI analysis capabilities.

## 📋 **Sample Profiles**

### **1. Sarah Chen - Cloud Solutions Architect**
- **Experience**: 8+ years
- **Specialization**: AWS, Azure, GCP, Infrastructure as Code
- **Level**: Senior
- **Location**: Seattle, WA

### **2. Marcus Johnson - DevOps Engineer**
- **Experience**: 6 years
- **Specialization**: Kubernetes, CI/CD, Container Orchestration
- **Level**: Senior
- **Location**: Austin, TX

### **3. Priya Patel - Data Engineer**
- **Experience**: 5+ years
- **Specialization**: Big Data, ML Infrastructure, Real-time Processing
- **Level**: Senior
- **Location**: San Francisco, CA

### **4. James Rodriguez - Cybersecurity Specialist**
- **Experience**: 7 years
- **Specialization**: Cloud Security, Compliance, Incident Response
- **Level**: Senior
- **Location**: New York, NY

### **5. Emily Zhang - Full Stack Developer**
- **Experience**: 4 years
- **Specialization**: React, Node.js, Cloud Technologies
- **Level**: Mid-level
- **Location**: Denver, CO

### **6. David Kim - MLOps Engineer**
- **Experience**: 6 years
- **Specialization**: ML Infrastructure, Model Deployment, Monitoring
- **Level**: Senior
- **Location**: Chicago, IL

### **7. Rachel Thompson - Site Reliability Engineer**
- **Experience**: 5 years
- **Specialization**: High Availability, Monitoring, Reliability Engineering
- **Level**: Senior
- **Location**: Atlanta, GA

### **8. Alex Rivera - Blockchain Developer**
- **Experience**: 3 years
- **Specialization**: Ethereum, Solidity, DeFi, NFTs
- **Level**: Mid-level
- **Location**: Phoenix, AZ

### **9. Lisa Wang - Technical Product Manager**
- **Experience**: 7 years
- **Specialization**: Cloud Products, AI/ML, Agile Methodologies
- **Level**: Senior
- **Location**: Portland, OR

### **10. Michael Brown - IoT Solutions Architect**
- **Experience**: 6 years
- **Specialization**: Connected Devices, Edge Computing, Industrial IoT
- **Level**: Senior
- **Location**: Miami, FL

## 🎯 **Demo Usage**

These resumes are designed to showcase the system's ability to:

- **Extract Contact Information**: Names, emails, phone numbers, locations
- **Identify Technical Skills**: Programming languages, cloud platforms, tools
- **Analyze Experience Levels**: Junior, Mid-level, Senior classifications
- **Categorize Specializations**: Different technology domains
- **Parse Work History**: Companies, roles, achievements
- **Recognize Certifications**: Industry-standard certifications

## 🔄 **How to Use for Demo**

1. **Upload to S3**: Copy these files to your S3 bucket for processing
2. **Email Testing**: Attach these files to emails sent to your Postmark webhook
3. **Manual Processing**: Use the "Check S3" button in the dashboard
4. **API Testing**: Use the `/process-resume/{s3_key}` endpoint

## 📊 **Expected AI Analysis Results**

The Amazon Bedrock Nova Premier model should successfully:

- Extract names and contact details with high confidence
- Identify 20-30 technical skills per resume
- Classify experience levels accurately
- Recognize cloud certifications and specializations
- Parse work history and achievements

## 🛠️ **Regenerating Samples**

To regenerate these samples with different profiles:

```bash
# From project root
python generate_sample_resumes.py
```

The generation script creates diverse, realistic profiles across different:
- **Experience Levels**: 3-8+ years
- **Technology Domains**: Cloud, DevOps, Data, Security, Development
- **Geographic Locations**: Major US tech hubs
- **Company Types**: Startups, enterprises, consulting firms

---

**Note**: These are fictional profiles created for demonstration purposes. All names, companies, and contact information are generated for testing only.
