import streamlit as st
import docx
import os
from fpdf import FPDF
import PyPDF2
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
from bs4 import BeautifulSoup
import requests

TEMPLATE_PATH = "templates/"

if "extracted_skills" not in st.session_state:
    st.session_state.extracted_skills = []
    
# Function to replace placeholders in a template
def fill_template(template_path, user_data):
    doc = docx.Document(template_path)
    for para in doc.paragraphs:
        for key, value in user_data.items():
            if f"{{{key}}}" in para.text:
                para.text = para.text.replace(f"{{{key}}}", value)
    return doc
# Function to scrape jobs from Indeed
def scrape_indeed_jobs(query, num_jobs=5):
    base_url = f"https://www.indeed.com/jobs?q={query}"
    response = requests.get(base_url)
    soup = BeautifulSoup(response.text, "html.parser")
    job_list = []

    for job_card in soup.find_all("div", class_="job_seen_beacon")[:num_jobs]:
        title = job_card.find("h2").text.strip()
        company = job_card.find("span", class_="companyName").text.strip()
        job_link = "https://www.indeed.com" + job_card.find("a")["href"]
        job_list.append({"title": title, "company": company, "link": job_link})

    return job_list

# Function to match resume skills with job descriptions
def match_resumes_to_jobs(resume_skills, job_list):
    vectorizer = TfidfVectorizer()
    job_titles = [job["title"] for job in job_list]
    combined_texts = resume_skills + job_titles
    tfidf_matrix = vectorizer.fit_transform(combined_texts)
    resume_vector = tfidf_matrix[:len(resume_skills)]
    job_vectors = tfidf_matrix[len(resume_skills):]
    similarity_scores = cosine_similarity(resume_vector, job_vectors)
    return similarity_scores

# Function to extract text from PDF
def extract_text_from_pdf(uploaded_file):
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    return "\n".join([page.extract_text() for page in pdf_reader.pages])

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

# ============================= JOB RECOMMENDATIONS =============================
elif option == "Get Job Recommendations":
    uploaded_file = st.file_uploader("Upload Your Resume (PDF) to Get Job Recommendations", type=["pdf"])

    if uploaded_file:
        resume_text = extract_text_from_pdf(uploaded_file)
        extracted_skills = extract_skills(resume_text)

        # ✅ Store extracted skills in session state
        st.session_state.extracted_skills = extracted_skills

        st.write("**Extracted Skills:**", extracted_skills)

    # ✅ Ensure extracted skills exist before proceeding
    if st.session_state.extracted_skills:
        jobs = scrape_indeed_jobs(",".join(st.session_state.extracted_skills), num_jobs=5)

        st.subheader("🔍 Recommended Job Listings")
        if jobs:
            for job in jobs:
                st.write(f"**{job['title']}** at **{job['company']}**")
                st.markdown(f"[Apply Here]({job['link']})", unsafe_allow_html=True)
        else:
            st.warning("No jobs found based on your skills.")
    else:
        st.warning("⚠️ Please upload a resume to get job recommendations.")


