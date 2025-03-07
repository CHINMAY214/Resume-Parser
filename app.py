import os
import re
import PyPDF2
import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rapidfuzz import process
import matplotlib.pyplot as plt
from collections import Counter

# Custom CSS for background image & styling
st.markdown(
    """
    <style>
    body {
        background-image: url("https://source.unsplash.com/1600x900/?technology,abstract");
        background-size: cover;
    }
    .stApp {
        background-color: rgba(0, 0, 0, 0.6);
        padding: 20px;
        border-radius: 10px;
        color: white;
    }
    .stButton > button {
        border-radius: 8px;
        background-color: #4CAF50;
        color: white;
        font-size: 18px;
    }
    .stTextArea textarea {
        background-color: #f0f0f0;
        border-radius: 5px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    text = ""
    reader = PyPDF2.PdfReader(pdf_file)
    for page in reader.pages:
        extracted_text = page.extract_text()
        if extracted_text:
            text += extracted_text + " "
    return text

# Extract skills using regex
def extract_skills(text):
    skill_keywords = {"python", "sql", "mysql", "machine learning", "data science", "data analysis",
                      "excel", "deep learning", "nlp", "java", "c++", "power bi", "streamlit", "azure"}
    words = re.findall(r'\b\w+\b', text.lower())
    skills = list(skill_keywords.intersection(words))
    return skills

# Extract experience
def extract_experience(text):
    experience_patterns = [r'(\d+)\s*years?', r'(\d+)\s*months?']
    experience = []
    for pattern in experience_patterns:
        matches = re.findall(pattern, text.lower())
        experience.extend(matches)
    return experience if experience else ["Not Found"]

# Match resumes with job descriptions
def match_resumes_to_jobs(resume_texts, job_descriptions):
    vectorizer = TfidfVectorizer()
    all_texts = resume_texts + job_descriptions
    tfidf_matrix = vectorizer.fit_transform(all_texts)
    resume_vectors = tfidf_matrix[:len(resume_texts)]
    job_vectors = tfidf_matrix[len(resume_texts):]
    return cosine_similarity(resume_vectors, job_vectors)

# Load job postings
@st.cache_data
def load_job_data():
    return pd.read_csv("jobs.csv")  # Ensure jobs.csv is in the same directory

# Recommend jobs
def recommend_jobs(extracted_skills, job_df):
    recommended_jobs = []
    for _, job in job_df.iterrows():
        job_skills = set(job["Required Skills"].lower().split(", "))
        match_count = len(job_skills.intersection(set(extracted_skills)))
        if match_count > 0:
            recommended_jobs.append((job["Job Title"], job["Company"], job["Location"], match_count))
    recommended_jobs.sort(key=lambda x: x[3], reverse=True)
    return recommended_jobs

# Streamlit UI
st.markdown("<h1 style='text-align: center; color: white;'>Resume Analyzer & Job Matching</h1>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("📂 Upload Your Resume (PDF)", type=["pdf"])

if uploaded_file is not None:
    with st.container():
        st.subheader("📌 Extracted Information")
        resume_text = extract_text_from_pdf(uploaded_file)
        extracted_skills = extract_skills(resume_text)
        extracted_experience = extract_experience(resume_text)

        st.write("✅ **Extracted Skills:**", extracted_skills)
        st.write("📆 **Extracted Experience:**", extracted_experience)

    # Layout with columns
    col1, col2 = st.columns(2)

    with col1:
        if st.button("📊 Get Matching Score"):
            job_description = st.text_area("📌 Paste a Job Description", "")
            if job_description:
                similarity_score = match_resumes_to_jobs([resume_text], [job_description])
                st.write(f"🔍 Matching Score: **{similarity_score[0][0]:.2f}**")

    with col2:
        if st.button("💼 Get Job Recommendations"):
            job_df = load_job_data()
            recommended_jobs = recommend_jobs(extracted_skills, job_df)
            st.subheader("🎯 Recommended Job Postings")
            if recommended_jobs:
                for job, company, location, match_count in recommended_jobs:
                    st.write(f"💼 **{job}** at **{company}** ({location}) - Matched Skills: {match_count}")
            else:
                st.write("❌ No suitable job recommendations found.")

    # Skill visualization
    skill_counts = Counter(extracted_skills)
    if skill_counts:
        fig, ax = plt.subplots()
        ax.bar(skill_counts.keys(), skill_counts.values(), color="#ffcc00")
        ax.set_xlabel("Skills")
        ax.set_ylabel("Frequency")
        ax.set_title("Extracted Skills from Resume")
        st.pyplot(fig)
    else:
        st.write("📌 No skills extracted to display.")

else:
    st.warning("⚠ Please upload a resume first.")
