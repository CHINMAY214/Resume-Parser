import streamlit as st
import docx
import os
from fpdf import FPDF
import PyPDF2
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

TEMPLATE_PATH = "templates/"

# Function to replace placeholders in a template
def fill_template(template_path, user_data):
    doc = docx.Document(template_path)
    for para in doc.paragraphs:
        for key, value in user_data.items():
            if f"{{{key}}}" in para.text:
                para.text = para.text.replace(f"{{{key}}}", value)
    return doc

# Function to match resumes to job descriptions
def match_resumes_to_jobs(resumes, job_descriptions):
    vectorizer = TfidfVectorizer()
    combined_texts = resumes + job_descriptions
    tfidf_matrix = vectorizer.fit_transform(combined_texts)
    resume_vectors = tfidf_matrix[:len(resumes)]
    job_vectors = tfidf_matrix[len(resumes):]
    return cosine_similarity(resume_vectors, job_vectors)

# Function to load job data
def load_job_data(file_path="job_descriptions1.csv"):
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        st.error(f"Error loading job data: {e}")
        return pd.DataFrame()

# Function to extract text from PDF
def extract_text_from_pdf(uploaded_file):
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    return "\n".join([page.extract_text() for page in pdf_reader.pages])

# Function to extract skills from text
import re

def extract_skills(text):
    skills_list = [
        # Software Development
        "Python", "Java", "C++", "C#", "JavaScript", "TypeScript", "Go", "Swift", "Kotlin", "Ruby", "PHP", "Rust",
        "HTML", "CSS", "React", "Angular", "Vue.js", "Node.js", "Django", "Flask", "Spring Boot", "Express.js",
        "Git", "Docker", "Kubernetes", "CI/CD", "Jenkins", "GraphQL", "REST API", "SOAP", "Microservices",
        
        # Data Science & AI
        "Machine Learning", "Deep Learning", "Data Science", "Artificial Intelligence", "NLP", "Computer Vision",
        "TensorFlow", "PyTorch", "Scikit-Learn", "Pandas", "NumPy", "Matplotlib", "Seaborn", "Keras", "OpenCV",
        "Big Data", "Hadoop", "Spark", "Apache Kafka", "ETL", "Tableau", "Power BI", "Data Visualization",
        
        # Cloud Computing
        "AWS", "Azure", "Google Cloud", "DevOps", "Cloud Security", "Terraform", "Ansible", "CloudFormation",
        "Serverless", "Lambda", "EC2", "S3", "Kubernetes", "Cloud Networking",
        
        # Cybersecurity
        "Ethical Hacking", "Penetration Testing", "Malware Analysis", "Network Security", "SIEM", "SOC", 
        "Firewall Management", "Incident Response", "Cryptography", "Zero Trust Security", "Identity Management",
        
        # Business & Management
        "Agile", "Scrum", "Kanban", "Project Management", "Business Analysis", "Risk Management",
        "Stakeholder Management", "Product Management", "Lean Methodology", "Six Sigma",
        
        # Digital Marketing
        "SEO", "SEM", "Google Ads", "Facebook Ads", "Social Media Marketing", "Email Marketing",
        "Marketing Automation", "Content Strategy", "Copywriting", "PPC", "Google Analytics",
        
        # Finance & Accounting
        "Financial Analysis", "Accounting", "Budgeting", "Forecasting", "Investment Analysis",
        "Risk Assessment", "Auditing", "Taxation", "Excel", "QuickBooks", "SAP",
        
        # Networking & IT Support
        "Network Security", "CCNA", "CCNP", "Routing", "Switching", "LAN", "WAN", "VPN", "TCP/IP",
        "Linux Administration", "Windows Server", "Active Directory",
        
        # Soft Skills
        "Communication", "Leadership", "Time Management", "Problem Solving", "Critical Thinking",
        "Teamwork", "Adaptability", "Creativity"
    ]
    
    return list(set([word for word in re.findall(r'\b\w+\b', text) if word.lower() in [skill.lower() for skill in skills_list]]))

# Function to recommend jobs based on skills
def recommend_jobs(extracted_skills, job_df):
    recommendations = []
    for _, row in job_df.iterrows():
        required_skills = set(row["skills"].split(", "))
        matched_skills = extracted_skills.intersection(required_skills)
        missing_skills = required_skills - extracted_skills
        if matched_skills:
            recommendations.append((row["Job Title"], row["Company"], len(matched_skills), missing_skills))
    return sorted(recommendations, key=lambda x: x[2], reverse=True)

# Function to extract experience from text
import re

def extract_experience(text):
    """
    Extracts the full experience section from a resume.
    
    Parameters:
    text (str): Resume text.
    
    Returns:
    str: Extracted experience details or 'Experience not found' if not detected.
    """
    # Define common headers that indicate work experience sections
    experience_headers = [
        "work experience", "professional experience", "employment history",
        "career summary", "job experience", "experience"
    ]
    
    # Regex pattern to detect experience sections
    experience_pattern = r"(?:{})\s*(?:[:\-]?\s*)\n?(.*?)(?:\n\s*\n|\Z)".format("|".join(experience_headers))

    # Search for experience sections
    matches = re.findall(experience_pattern, text, re.IGNORECASE | re.DOTALL)

    if matches:
        return matches[0].strip()  # Return first match (assuming experience is listed once)
    
    return "Experience not found"


# Function to convert DOCX to PDF
def convert_docx_to_pdf(doc, pdf_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for para in doc.paragraphs:
        pdf.multi_cell(200, 10, txt=para.text.encode("latin-1", "ignore").decode("latin-1"), align='L')
    pdf.output(pdf_path)

if not os.path.exists(TEMPLATE_PATH):
    os.makedirs(TEMPLATE_PATH)

st.title("📄 Resume Analyzer & Job Matching")
option = st.sidebar.radio("Choose an option:", ["Resume Analyzer", "Get Job Recommendations", "Resume Generator"])

if option == "Resume Generator":
    st.subheader("📝 Create a Resume Using Templates")
    templates = [f for f in os.listdir(TEMPLATE_PATH) if f.endswith(".docx")]
    if templates:
        selected_template = st.selectbox("Select a Resume Template", templates)
        user_data = {key: st.text_input(key) for key in ["NAME", "EMAIL", "PHONE", "SKILLS", "EXPERIENCE", "EDUCATION", "CERTIFICATIONS"]}
        if st.button("Generate Resume"):
            updated_doc = fill_template(os.path.join(TEMPLATE_PATH, selected_template), user_data)
            updated_doc.save("Generated_Resume.docx")
            convert_docx_to_pdf(updated_doc, "Generated_Resume.pdf")
            st.download_button("Download Resume (DOCX)", open("Generated_Resume.docx", "rb"))
            st.download_button("Download Resume (PDF)", open("Generated_Resume.pdf", "rb"))
    else:
        st.warning("No resume templates found! Upload DOCX templates in 'templates/' folder.")

elif option == "Resume Analyzer":
    uploaded_file = st.file_uploader("Upload Your Resume (PDF)", type=["pdf"])
    if uploaded_file:
        resume_text = extract_text_from_pdf(uploaded_file)
        extracted_skills = extract_skills(resume_text)
        extracted_experience = extract_experience(resume_text)
        st.write("**Extracted Skills:**", extracted_skills)
        st.write("**Extracted Experience:**", extracted_experience)

elif option == "Get Job Recommendations":
    job_df = load_job_data()
    if not job_df.empty:
        extracted_skills = extract_skills(resume_text) if 'resume_text' in locals() else set()
        recommended_jobs = recommend_jobs(extracted_skills, job_df)
        st.subheader("Recommended Job Postings")
        for job, company, match_count, missing_skills in recommended_jobs[:10]:
            st.write(f"**{job}** at **{company}** - Matched Skills: {match_count}")
            st.write(f"Missing Skills: {', '.join(missing_skills) if missing_skills else 'None'}")
    else:
        st.warning("⚠️ No job data available.")

elif option == "Get Matching Score":
    job_description = st.text_area("Paste a Job Description", "")
    if job_description and 'resume_text' in locals():
        similarity_score = match_resumes_to_jobs([resume_text], [job_description])
        st.write(f"Matching Score: {similarity_score[0][0]:.2f}")
