#!/usr/bin/env python3
"""
Generate 10 diverse sample PDF resumes for demo purposes
"""
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import os

def create_resume_pdf(filename, profile_data):
    """Create a professional PDF resume"""
    doc = SimpleDocTemplate(filename, pagesize=letter, topMargin=0.5*inch)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=6,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=6,
        spaceBefore=12,
        textColor=colors.darkblue
    )
    
    content = []
    
    # Header
    content.append(Paragraph(profile_data['name'], title_style))
    content.append(Paragraph(f"{profile_data['email']} | {profile_data['phone']} | {profile_data['location']}", styles['Normal']))
    content.append(Paragraph(profile_data['linkedin'], styles['Normal']))
    content.append(Spacer(1, 12))
    
    # Professional Summary
    content.append(Paragraph("PROFESSIONAL SUMMARY", heading_style))
    content.append(Paragraph(profile_data['summary'], styles['Normal']))
    content.append(Spacer(1, 12))
    
    # Technical Skills
    content.append(Paragraph("TECHNICAL SKILLS", heading_style))
    for category, skills in profile_data['skills'].items():
        content.append(Paragraph(f"<b>{category}:</b> {skills}", styles['Normal']))
    content.append(Spacer(1, 12))
    
    # Professional Experience
    content.append(Paragraph("PROFESSIONAL EXPERIENCE", heading_style))
    for exp in profile_data['experience']:
        content.append(Paragraph(f"<b>{exp['title']}</b> | {exp['company']} | {exp['duration']}", styles['Normal']))
        content.append(Paragraph(exp['location'], styles['Normal']))
        for achievement in exp['achievements']:
            content.append(Paragraph(f"• {achievement}", styles['Normal']))
        content.append(Spacer(1, 8))
    
    # Education
    content.append(Paragraph("EDUCATION", heading_style))
    for edu in profile_data['education']:
        content.append(Paragraph(f"<b>{edu['degree']}</b> | {edu['school']} | {edu['year']}", styles['Normal']))
        if 'details' in edu:
            content.append(Paragraph(edu['details'], styles['Normal']))
    content.append(Spacer(1, 12))
    
    # Certifications
    if 'certifications' in profile_data:
        content.append(Paragraph("CERTIFICATIONS", heading_style))
        for cert in profile_data['certifications']:
            content.append(Paragraph(f"• {cert}", styles['Normal']))
    
    doc.build(content)

# All 10 resume profiles
profiles = [
    {
        'name': 'Sarah Chen',
        'email': 'sarah.chen@email.com',
        'phone': '(555) 123-4567',
        'location': 'Seattle, WA',
        'linkedin': 'linkedin.com/in/sarahchen-cloudarchitect',
        'summary': 'Senior Cloud Solutions Architect with 8+ years of experience designing and implementing scalable cloud infrastructure on AWS, Azure, and GCP. Proven track record of leading digital transformation initiatives and reducing operational costs by 40% through cloud optimization strategies.',
        'skills': {
            'Cloud Platforms': 'AWS (Expert), Microsoft Azure, Google Cloud Platform',
            'Infrastructure': 'Terraform, CloudFormation, Kubernetes, Docker, Ansible',
            'Programming': 'Python, Go, JavaScript, Bash',
            'Databases': 'PostgreSQL, MongoDB, DynamoDB, Redis',
            'Monitoring': 'CloudWatch, Prometheus, Grafana, ELK Stack'
        },
        'experience': [
            {
                'title': 'Senior Cloud Solutions Architect',
                'company': 'TechCorp Solutions',
                'duration': '2020 - Present',
                'location': 'Seattle, WA',
                'achievements': [
                    'Led cloud migration for 50+ enterprise applications, resulting in 35% cost reduction',
                    'Designed multi-region disaster recovery architecture serving 10M+ users',
                    'Implemented Infrastructure as Code practices reducing deployment time by 60%',
                    'Mentored team of 8 junior engineers on cloud best practices'
                ]
            },
            {
                'title': 'Cloud Engineer',
                'company': 'DataFlow Inc',
                'duration': '2018 - 2020',
                'location': 'Portland, OR',
                'achievements': [
                    'Built automated CI/CD pipelines using Jenkins and AWS CodePipeline',
                    'Optimized cloud costs by implementing auto-scaling and reserved instances'
                ]
            }
        ],
        'education': [
            {
                'degree': 'Master of Science in Computer Science',
                'school': 'University of Washington',
                'year': '2018'
            }
        ],
        'certifications': [
            'AWS Certified Solutions Architect - Professional',
            'Microsoft Azure Solutions Architect Expert',
            'Certified Kubernetes Administrator (CKA)'
        ]
    },
    
    {
        'name': 'Marcus Johnson',
        'email': 'marcus.johnson@email.com',
        'phone': '(555) 234-5678',
        'location': 'Austin, TX',
        'linkedin': 'linkedin.com/in/marcusjohnson-devops',
        'summary': 'DevOps Engineer with 6 years of experience in building robust CI/CD pipelines and managing containerized applications at scale. Expert in Kubernetes orchestration and cloud-native technologies.',
        'skills': {
            'Container Technologies': 'Docker, Kubernetes, OpenShift, Helm',
            'CI/CD Tools': 'Jenkins, GitLab CI, GitHub Actions, ArgoCD',
            'Cloud Platforms': 'AWS, Google Cloud Platform',
            'Programming': 'Python, Go, Shell Scripting, YAML',
            'Monitoring': 'Prometheus, Grafana, Jaeger, New Relic'
        },
        'experience': [
            {
                'title': 'Senior DevOps Engineer',
                'company': 'CloudNative Systems',
                'duration': '2021 - Present',
                'location': 'Austin, TX',
                'achievements': [
                    'Orchestrated migration of 200+ microservices to Kubernetes clusters',
                    'Implemented GitOps workflows reducing deployment errors by 70%',
                    'Built observability stack serving 500+ services with 99.9% uptime'
                ]
            }
        ],
        'education': [
            {
                'degree': 'Bachelor of Science in Computer Engineering',
                'school': 'University of Texas at Austin',
                'year': '2018'
            }
        ],
        'certifications': [
            'Certified Kubernetes Administrator (CKA)',
            'AWS Certified DevOps Engineer - Professional'
        ]
    },
    
    {
        'name': 'Priya Patel',
        'email': 'priya.patel@email.com',
        'phone': '(555) 345-6789',
        'location': 'San Francisco, CA',
        'linkedin': 'linkedin.com/in/priyapatel-dataengineer',
        'summary': 'Data Engineer with 5+ years of experience building scalable data pipelines and analytics platforms. Specialized in real-time data processing, machine learning infrastructure, and cloud data warehousing solutions.',
        'skills': {
            'Big Data': 'Apache Spark, Kafka, Hadoop, Airflow, Databricks',
            'Cloud Platforms': 'AWS, Google Cloud Platform, Snowflake',
            'Programming': 'Python, Scala, SQL, Java',
            'Databases': 'PostgreSQL, MongoDB, Cassandra, BigQuery',
            'ML Tools': 'TensorFlow, PyTorch, MLflow, Kubeflow'
        },
        'experience': [
            {
                'title': 'Senior Data Engineer',
                'company': 'DataTech Analytics',
                'duration': '2022 - Present',
                'location': 'San Francisco, CA',
                'achievements': [
                    'Built real-time data pipeline processing 10TB+ daily using Kafka and Spark',
                    'Designed ML feature store serving 50+ machine learning models',
                    'Reduced data processing costs by 45% through optimization strategies'
                ]
            },
            {
                'title': 'Data Engineer',
                'company': 'FinanceFlow Corp',
                'duration': '2020 - 2022',
                'location': 'San Jose, CA',
                'achievements': [
                    'Implemented data lake architecture on AWS S3 and Glue',
                    'Created automated ETL pipelines reducing manual work by 80%'
                ]
            }
        ],
        'education': [
            {
                'degree': 'Master of Science in Data Science',
                'school': 'Stanford University',
                'year': '2020'
            }
        ],
        'certifications': [
            'AWS Certified Data Analytics - Specialty',
            'Google Cloud Professional Data Engineer',
            'Databricks Certified Data Engineer Professional'
        ]
    },
    
    {
        'name': 'James Rodriguez',
        'email': 'james.rodriguez@email.com',
        'phone': '(555) 456-7890',
        'location': 'New York, NY',
        'linkedin': 'linkedin.com/in/jamesrodriguez-cybersecurity',
        'summary': 'Cybersecurity Specialist with 7 years of experience in cloud security, threat detection, and compliance. Expert in securing AWS and Azure environments with focus on zero-trust architecture and incident response.',
        'skills': {
            'Security Tools': 'Splunk, CrowdStrike, Nessus, Wireshark, Metasploit',
            'Cloud Security': 'AWS Security Hub, Azure Sentinel, GuardDuty',
            'Compliance': 'SOC 2, PCI DSS, HIPAA, ISO 27001',
            'Programming': 'Python, PowerShell, Bash, C++',
            'Networking': 'Firewalls, VPN, IDS/IPS, SIEM'
        },
        'experience': [
            {
                'title': 'Senior Cybersecurity Engineer',
                'company': 'SecureCloud Inc',
                'duration': '2021 - Present',
                'location': 'New York, NY',
                'achievements': [
                    'Implemented zero-trust security model for 500+ cloud workloads',
                    'Reduced security incidents by 60% through proactive threat hunting',
                    'Led SOC 2 Type II compliance audit with zero findings'
                ]
            },
            {
                'title': 'Security Analyst',
                'company': 'CyberDefense Corp',
                'duration': '2019 - 2021',
                'location': 'Boston, MA',
                'achievements': [
                    'Monitored and analyzed security events for 24/7 SOC operations',
                    'Developed automated incident response playbooks'
                ]
            }
        ],
        'education': [
            {
                'degree': 'Bachelor of Science in Cybersecurity',
                'school': 'New York University',
                'year': '2018'
            }
        ],
        'certifications': [
            'CISSP (Certified Information Systems Security Professional)',
            'AWS Certified Security - Specialty',
            'Certified Ethical Hacker (CEH)',
            'CompTIA Security+'
        ]
    },
    
    {
        'name': 'Emily Zhang',
        'email': 'emily.zhang@email.com',
        'phone': '(555) 567-8901',
        'location': 'Denver, CO',
        'linkedin': 'linkedin.com/in/emilyzhang-fullstack',
        'summary': 'Full Stack Developer with 4 years of experience building modern web applications using React, Node.js, and cloud technologies. Passionate about creating scalable, user-friendly applications with clean, maintainable code.',
        'skills': {
            'Frontend': 'React, Vue.js, TypeScript, HTML5, CSS3, Tailwind CSS',
            'Backend': 'Node.js, Express, Python, Django, REST APIs, GraphQL',
            'Databases': 'PostgreSQL, MongoDB, Redis, DynamoDB',
            'Cloud & DevOps': 'AWS, Docker, Kubernetes, CI/CD, Git',
            'Testing': 'Jest, Cypress, Selenium, Unit Testing'
        },
        'experience': [
            {
                'title': 'Full Stack Developer',
                'company': 'WebTech Solutions',
                'duration': '2022 - Present',
                'location': 'Denver, CO',
                'achievements': [
                    'Developed e-commerce platform serving 100K+ users with React and Node.js',
                    'Implemented microservices architecture reducing response time by 40%',
                    'Built automated testing suite achieving 95% code coverage'
                ]
            },
            {
                'title': 'Frontend Developer',
                'company': 'StartupHub',
                'duration': '2021 - 2022',
                'location': 'Boulder, CO',
                'achievements': [
                    'Created responsive web applications using React and TypeScript',
                    'Collaborated with UX team to implement pixel-perfect designs'
                ]
            }
        ],
        'education': [
            {
                'degree': 'Bachelor of Science in Computer Science',
                'school': 'University of Colorado Boulder',
                'year': '2021'
            }
        ],
        'certifications': [
            'AWS Certified Developer - Associate',
            'MongoDB Certified Developer',
            'React Developer Certification'
        ]
    },
    
    {
        'name': 'David Kim',
        'email': 'david.kim@email.com',
        'phone': '(555) 678-9012',
        'location': 'Chicago, IL',
        'linkedin': 'linkedin.com/in/davidkim-mlops',
        'summary': 'MLOps Engineer with 6 years of experience operationalizing machine learning models at scale. Expert in building ML infrastructure, model deployment pipelines, and monitoring systems for production ML workloads.',
        'skills': {
            'ML Platforms': 'MLflow, Kubeflow, SageMaker, Databricks, Vertex AI',
            'Container & Orchestration': 'Docker, Kubernetes, Helm, Istio',
            'Programming': 'Python, R, Scala, SQL, Go',
            'ML Libraries': 'TensorFlow, PyTorch, Scikit-learn, XGBoost',
            'Cloud Platforms': 'AWS, Google Cloud Platform, Azure'
        },
        'experience': [
            {
                'title': 'Senior MLOps Engineer',
                'company': 'AI Innovations Lab',
                'duration': '2022 - Present',
                'location': 'Chicago, IL',
                'achievements': [
                    'Built ML platform serving 200+ models with 99.9% uptime',
                    'Implemented automated model retraining reducing manual effort by 85%',
                    'Designed A/B testing framework for model performance evaluation'
                ]
            },
            {
                'title': 'Machine Learning Engineer',
                'company': 'DataScience Corp',
                'duration': '2020 - 2022',
                'location': 'Milwaukee, WI',
                'achievements': [
                    'Deployed recommendation system serving 5M+ daily predictions',
                    'Created model monitoring dashboard detecting drift and anomalies'
                ]
            }
        ],
        'education': [
            {
                'degree': 'Master of Science in Machine Learning',
                'school': 'Northwestern University',
                'year': '2020'
            }
        ],
        'certifications': [
            'Google Cloud Professional ML Engineer',
            'AWS Certified Machine Learning - Specialty',
            'Kubernetes Certified Application Developer'
        ]
    },
    
    {
        'name': 'Rachel Thompson',
        'email': 'rachel.thompson@email.com',
        'phone': '(555) 789-0123',
        'location': 'Atlanta, GA',
        'linkedin': 'linkedin.com/in/rachelthompson-sre',
        'summary': 'Site Reliability Engineer with 5 years of experience ensuring high availability and performance of large-scale distributed systems. Specialized in incident management, capacity planning, and reliability engineering practices.',
        'skills': {
            'Monitoring & Observability': 'Prometheus, Grafana, Datadog, New Relic, PagerDuty',
            'Infrastructure': 'Kubernetes, Terraform, Ansible, AWS, GCP',
            'Programming': 'Python, Go, Shell Scripting, YAML',
            'Databases': 'PostgreSQL, MySQL, Redis, Elasticsearch',
            'Reliability': 'SLI/SLO, Error Budgets, Chaos Engineering'
        },
        'experience': [
            {
                'title': 'Senior Site Reliability Engineer',
                'company': 'ScaleOps Technologies',
                'duration': '2022 - Present',
                'location': 'Atlanta, GA',
                'achievements': [
                    'Maintained 99.99% uptime for critical services serving 50M+ users',
                    'Reduced MTTR by 65% through improved monitoring and alerting',
                    'Implemented chaos engineering practices improving system resilience'
                ]
            },
            {
                'title': 'Platform Engineer',
                'company': 'CloudReliable Inc',
                'duration': '2020 - 2022',
                'location': 'Nashville, TN',
                'achievements': [
                    'Built self-healing infrastructure reducing manual interventions by 70%',
                    'Created capacity planning models preventing resource bottlenecks'
                ]
            }
        ],
        'education': [
            {
                'degree': 'Bachelor of Science in Systems Engineering',
                'school': 'Georgia Institute of Technology',
                'year': '2020'
            }
        ],
        'certifications': [
            'Google Cloud Professional Cloud Architect',
            'AWS Certified Solutions Architect - Professional',
            'Certified Kubernetes Administrator (CKA)'
        ]
    },
    
    {
        'name': 'Alex Rivera',
        'email': 'alex.rivera@email.com',
        'phone': '(555) 890-1234',
        'location': 'Phoenix, AZ',
        'linkedin': 'linkedin.com/in/alexrivera-blockchain',
        'summary': 'Blockchain Developer with 3 years of experience building decentralized applications and smart contracts. Specialized in Ethereum, Solidity, and Web3 technologies with focus on DeFi and NFT platforms.',
        'skills': {
            'Blockchain': 'Ethereum, Solidity, Web3.js, Hardhat, Truffle',
            'Programming': 'JavaScript, TypeScript, Python, Rust',
            'Frontend': 'React, Next.js, HTML5, CSS3',
            'Tools': 'MetaMask, IPFS, The Graph, OpenZeppelin',
            'Databases': 'MongoDB, PostgreSQL, Redis'
        },
        'experience': [
            {
                'title': 'Blockchain Developer',
                'company': 'CryptoInnovate Labs',
                'duration': '2022 - Present',
                'location': 'Phoenix, AZ',
                'achievements': [
                    'Developed DeFi protocol handling $10M+ in total value locked',
                    'Built NFT marketplace with gas-optimized smart contracts',
                    'Implemented multi-signature wallet with advanced security features'
                ]
            },
            {
                'title': 'Junior Blockchain Developer',
                'company': 'Web3 Startup',
                'duration': '2021 - 2022',
                'location': 'Remote',
                'achievements': [
                    'Created smart contracts for token distribution and staking',
                    'Integrated Web3 functionality into React applications'
                ]
            }
        ],
        'education': [
            {
                'degree': 'Bachelor of Science in Computer Science',
                'school': 'Arizona State University',
                'year': '2021'
            }
        ],
        'certifications': [
            'Certified Ethereum Developer',
            'Blockchain Council Certified Blockchain Expert',
            'ConsenSys Academy Blockchain Developer'
        ]
    },
    
    {
        'name': 'Lisa Wang',
        'email': 'lisa.wang@email.com',
        'phone': '(555) 901-2345',
        'location': 'Portland, OR',
        'linkedin': 'linkedin.com/in/lisawang-productmanager',
        'summary': 'Technical Product Manager with 7 years of experience leading cross-functional teams to deliver innovative cloud and AI products. Expert in agile methodologies, user research, and data-driven product decisions.',
        'skills': {
            'Product Management': 'Agile, Scrum, Kanban, Roadmapping, User Stories',
            'Analytics': 'Google Analytics, Mixpanel, Amplitude, A/B Testing',
            'Technical': 'APIs, Cloud Architecture, AI/ML, Database Design',
            'Tools': 'Jira, Confluence, Figma, Slack, Notion',
            'Programming': 'SQL, Python, JavaScript (Basic)'
        },
        'experience': [
            {
                'title': 'Senior Technical Product Manager',
                'company': 'CloudAI Solutions',
                'duration': '2021 - Present',
                'location': 'Portland, OR',
                'achievements': [
                    'Led development of AI-powered analytics platform with 300% user growth',
                    'Managed product roadmap for $50M+ revenue cloud infrastructure product',
                    'Coordinated cross-functional team of 25+ engineers, designers, and analysts'
                ]
            },
            {
                'title': 'Product Manager',
                'company': 'TechFlow Inc',
                'duration': '2019 - 2021',
                'location': 'Seattle, WA',
                'achievements': [
                    'Launched mobile application reaching 1M+ downloads in first year',
                    'Implemented data-driven feature prioritization increasing user engagement by 45%'
                ]
            }
        ],
        'education': [
            {
                'degree': 'MBA in Technology Management',
                'school': 'University of Oregon',
                'year': '2019'
            },
            {
                'degree': 'Bachelor of Science in Computer Science',
                'school': 'Oregon State University',
                'year': '2017'
            }
        ],
        'certifications': [
            'Certified Scrum Product Owner (CSPO)',
            'Google Analytics Certified',
            'AWS Cloud Practitioner'
        ]
    },
    
    {
        'name': 'Michael Brown',
        'email': 'michael.brown@email.com',
        'phone': '(555) 012-3456',
        'location': 'Miami, FL',
        'linkedin': 'linkedin.com/in/michaelbrown-iot',
        'summary': 'IoT Solutions Architect with 6 years of experience designing and implementing connected device ecosystems. Expert in edge computing, sensor networks, and industrial IoT applications with focus on scalability and security.',
        'skills': {
            'IoT Platforms': 'AWS IoT Core, Azure IoT Hub, Google Cloud IoT',
            'Protocols': 'MQTT, CoAP, LoRaWAN, Zigbee, Bluetooth, WiFi',
            'Programming': 'C/C++, Python, JavaScript, Embedded C',
            'Hardware': 'Arduino, Raspberry Pi, ESP32, ARM Cortex',
            'Edge Computing': 'AWS Greengrass, Azure IoT Edge, NVIDIA Jetson'
        },
        'experience': [
            {
                'title': 'Senior IoT Solutions Architect',
                'company': 'SmartTech Industries',
                'duration': '2021 - Present',
                'location': 'Miami, FL',
                'achievements': [
                    'Designed IoT platform managing 100K+ connected devices across 50 locations',
                    'Implemented predictive maintenance system reducing downtime by 40%',
                    'Led digital transformation for manufacturing clients saving $2M+ annually'
                ]
            },
            {
                'title': 'IoT Engineer',
                'company': 'ConnectedSystems Corp',
                'duration': '2019 - 2021',
                'location': 'Tampa, FL',
                'achievements': [
                    'Developed smart city solutions for traffic management and environmental monitoring',
                    'Built secure device provisioning and management system'
                ]
            }
        ],
        'education': [
            {
                'degree': 'Master of Science in Electrical Engineering',
                'school': 'University of Florida',
                'year': '2019'
            }
        ],
        'certifications': [
            'AWS Certified IoT - Specialty',
            'Microsoft Azure IoT Developer',
            'Certified IoT Professional (CIoTP)'
        ]
    }
]

def generate_all_resumes():
    """Generate all 10 sample resumes"""
    samples_dir = "samples"
    
    # Create samples directory if it doesn't exist
    if not os.path.exists(samples_dir):
        os.makedirs(samples_dir)
    
    print("Generating 10 diverse technology professional resumes...")
    print("=" * 60)
    
    for i, profile in enumerate(profiles, 1):
        filename = os.path.join(samples_dir, f"{profile['name'].replace(' ', '_')}_Resume.pdf")
        create_resume_pdf(filename, profile)
        print(f"{i:2d}. Generated: {profile['name']} - {filename}")
    
    print("=" * 60)
    print(f"✅ Successfully generated {len(profiles)} sample resumes in the 'samples' folder!")
    print("\nProfiles include:")
    print("• Cloud Solutions Architect (AWS/Azure/GCP)")
    print("• DevOps Engineer (Kubernetes/CI-CD)")
    print("• Data Engineer (Big Data/ML)")
    print("• Cybersecurity Specialist")
    print("• Full Stack Developer")
    print("• MLOps Engineer")
    print("• Site Reliability Engineer")
    print("• Blockchain Developer")
    print("• Technical Product Manager")
    print("• IoT Solutions Architect")

if __name__ == "__main__":
    generate_all_resumes()
