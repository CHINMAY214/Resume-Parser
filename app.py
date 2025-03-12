import streamlit as st
import docx
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

# Ensure the templates folder exists
if not os.path.exists(TEMPLATE_PATH):
    os.makedirs(TEMPLATE_PATH)

# Streamlit UI
st.title("📄 Resume Analyzer & Job Matching")

# Sidebar options
option = st.sidebar.radio("Choose an option:", ["Resume Analyzer", "Get Matching Score", "Get Job Recommendations", "Show Visualizations", "Resume Generator"])

# ============================= RESUME GENERATOR =============================
if option == "Resume Generator":
    st.subheader("📝 Create a Resume Using Templates")
    
    templates = [f for f in os.listdir(TEMPLATE_PATH) if f.endswith(".docx")]
    
    if templates:
        selected_template = st.selectbox("Select a Resume Template", templates)

        # User inputs
        name = st.text_input("Full Name", "John Doe")
        email = st.text_input("Email", "john@example.com")
        phone = st.text_input("Phone Number", "123-456-7890")
        skills = st.text_area("Skills", "Python, SQL, Data Science")
        experience = st.text_area("Experience", "2 years in Data Analysis")
        education = st.text_area("Education", "Bachelor of Engineering, XYZ University")
        certifications = st.text_area("Certifications", "PMP, AWS Certified Solutions Architect")

        if st.button("Generate Resume"):
            user_data = {
                "NAME": name,
                "EMAIL": email,
                "PHONE": phone,
                "SKILLS": skills,
                "EXPERIENCE": experience,
                "EDUCATION": education,
                "CERTIFICATIONS": certifications
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
