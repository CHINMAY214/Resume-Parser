import streamlit as st
import docx
from docx.shared import Pt
import os
from fpdf import FPDF
import PyPDF2
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
from collections import Counter
import re

TEMPLATE_PATH = "templates/"

# Function to replace placeholders in a template
def fill_template(template_path, user_data):
    doc = docx.Document(template_path)
    for para in doc.paragraphs:
        for key, value in user_data.items():
            if f"{{{key}}}" in para.text:  # Example: {NAME}, {EMAIL}
                para.text = para.text.replace(f"{{{key}}}", value)
    return doc

# Function to convert DOCX to PDF
def convert_docx_to_pdf(doc, pdf_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    for para in doc.paragraphs:
        clean_text = para.text.encode("latin-1", "ignore").decode("latin-1")
        pdf.multi_cell(200, 10, txt=clean_text, align='L')
    
    pdf.output(pdf_path)

# Function to extract text from PDF resumes
def extract_text_from_pdf(pdf_file):
    text = ""
    reader = PyPDF2.PdfReader(pdf_file)
    for page in reader.pages:
        extracted_text = page.extract_text()
        if extracted_text:
            text += extracted_text + " "

    # Debug: Show extracted text
    st.write("📄 Extracted Resume Text:", text[:500])  # Show first 500 characters

    if not text.strip():
        st.error("⚠️ No text extracted! Ensure the resume is not image-based.")

    return text

# Extract skills from resume
def extract_skills(text):
    skill_keywords = {
        "python", "sql", "mysql", "machine learning", "deep learning", "nlp", "data science",
        "data analysis", "excel", "power bi", "tableau", "streamlit", "tensorflow", "pytorch",
        "azure", "aws", "gcp", "c++", "java", "r", "statistics", "data visualization", "big data",
        "business intelligence", "cloud computing", "hadoop", "spark", "flask", "django",
        "kubernetes", "docker", "devops", "git", "linux", "bash", "etl", "mongodb", "postgresql",
        "data wrangling", "data preprocessing", "feature engineering", "mlops", "cybersecurity"
    }
    words = re.findall(r'\b\w+\b', text.lower())  # Extract words properly
    extracted_skills = set(words).intersection(skill_keywords)

    # Debug: Show matched skills
    st.write("✅ Extracted Skills:", extracted_skills)

    return extracted_skills

# Extract experience from resume
def extract_experience(text):
    experience_patterns = [r'(\d+)\s*years?', r'(\d+)\s*months?']
    experience = []
    for pattern in experience_patterns:
        matches = re.findall(pattern, text.lower())
        experience.extend(matches)
    return experience if experience else ["Not Found"]

# Resume Matching Function
def match_resumes_to_jobs(resume_texts, job_descriptions):
    vectorizer = TfidfVectorizer()
    all_texts = resume_texts + job_descriptions
    tfidf_matrix = vectorizer.fit_transform(all_texts)
    resume_vectors = tfidf_matrix[:len(resume_texts)]
    job_vectors = tfidf_matrix[len(resume_texts):]
    return cosine_similarity(resume_vectors, job_vectors)

@st.cache_data
def load_job_data():
    return pd.read_csv("job_descriptions1.csv")

def recommend_jobs(extracted_skills, job_df):
    recommended_jobs = []
    
    for _, job in job_df.iterrows():
        job_skills = set(map(str.lower, job["skills"].split(", ")))

        match_count = len(job_skills.intersection(extracted_skills))
        missing_skills = job_skills - extracted_skills

        if match_count > 0:
            recommended_jobs.append((job["Job Title"], job["Company"], match_count, missing_skills))

    recommended_jobs.sort(key=lambda x: x[2], reverse=True)  # Sort by match count
    
    return recommended_jobs

# Streamlit UI
st.title("📄 Resume Analyzer & Job Matching")

# Sidebar options
option = st.sidebar.radio("Choose an option:", ["Resume Analyzer", "Get Matching Score", "Get Job Recommendations", "Show Visualizations", "Resume Generator"])

# ============================= RESUME GENERATOR =============================
if option == "Resume Generator":
    st.subheader("📝 Create a Resume Using Templates")

    if not os.path.exists(TEMPLATE_PATH):
        os.makedirs(TEMPLATE_PATH)

    templates = [f for f in os.listdir(TEMPLATE_PATH) if f.endswith(".docx")]
    
    if templates:
        selected_template = st.selectbox("Select a Resume Template", templates)

        # User inputs
        name = st.text_input("Full Name", "John Doe")
        email = st.text_input("Email", "john@example.com")
        phone = st.text_input("Phone Number", "123-456-7890")
        skills = st.text_area("Skills", "Python, SQL, Data Science")
        experience = st.text_area("Experience", "2 years in Data Analysis")

        if st.button("Generate Resume"):
            user_data = {
                "NAME": name,
                "EMAIL": email,
                "PHONE": phone,
                "SKILLS": skills,
                "EXPERIENCE": experience
            }

            template_path = os.path.join(TEMPLATE_PATH, selected_template)
            updated_doc = fill_template(template_path, user_data)

            docx_path = "Generated_Resume.docx"
            updated_doc.save(docx_path)

            pdf_path = "Generated_Resume.pdf"
            convert_docx_to_pdf(updated_doc, pdf_path)

            with open(docx_path, "rb") as docx_file:
                st.download_button("Download Resume (DOCX)", docx_file, file_name="Generated_Resume.docx")

            with open(pdf_path, "rb") as pdf_file:
                st.download_button("Download Resume (PDF)", pdf_file, file_name="Generated_Resume.pdf")

    else:
        st.warning("No resume templates found! Please upload DOCX templates in the 'templates/' folder.")

# ============================= RESUME ANALYZER =============================
elif option == "Resume Analyzer":
    uploaded_file = st.file_uploader("Upload Your Resume (PDF)", type=["pdf"])

    if uploaded_file is not None:
        resume_text = extract_text_from_pdf(uploaded_file)
        extracted_skills = extract_skills(resume_text)
        extracted_experience = extract_experience(resume_text)

        st.write("**Extracted Skills:**", extracted_skills)
        st.write("**Extracted Experience:**", extracted_experience)

# ============================= JOB RECOMMENDATIONS =============================
elif option == "Get Job Recommendations":
    job_df = load_job_data()
    
    extracted_skills = extracted_skills if 'extracted_skills' in locals() else set()
    
    recommended_jobs = recommend_jobs(extracted_skills, job_df)

    st.subheader("Recommended Job Postings")
    if recommended_jobs:
        for job, company, match_count, missing_skills in recommended_jobs[:10]:
            st.write(f"**{job}** at **{company}** - Matched Skills: {match_count}")
            st.write(f"Missing Skills: {', '.join(missing_skills) if missing_skills else 'None'}")
    else:
        st.warning("⚠️ No suitable job recommendations found.")

# ============================= JOB MATCHING =============================
elif option == "Get Matching Score":
    job_description = st.text_area("Paste a Job Description", "")
    if job_description:
        similarity_score = match_resumes_to_jobs([resume_text], [job_description])
        st.write(f"Matching Score: {similarity_score[0][0]:.2f}")
