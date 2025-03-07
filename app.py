import os
import re
import PyPDF2
import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
from collections import Counter

# Custom CSS for background styling
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
    .stTextArea textarea {
        background-color: #f0f0f0;
        border-radius: 5px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

def extract_text_from_pdf(pdf_file):
    text = ""
    reader = PyPDF2.PdfReader(pdf_file)
    for page in reader.pages:
        extracted_text = page.extract_text()
        if extracted_text:
            text += extracted_text + " "
    return text

def extract_skills(text):
    skill_keywords = {
        "python", "sql", "mysql", "machine learning", "deep learning", "nlp", "data science",
        "data analysis", "excel", "power bi", "tableau", "streamlit", "tensorflow", "pytorch",
        "azure", "aws", "gcp", "c++", "java", "r", "statistics", "data visualization", "big data",
        "business intelligence", "cloud computing", "hadoop", "spark", "flask", "django",
        "kubernetes", "docker", "devops", "git", "linux", "bash", "etl", "mongodb", "postgresql",
        "data wrangling", "data preprocessing", "feature engineering", "mlops", "cybersecurity"
    }
    words = re.findall(r'\b\w+\b', text.lower())
    extracted_skills = set(words).intersection(skill_keywords)
    return extracted_skills

def extract_experience(text):
    experience_patterns = [r'(\d+)\s*years?', r'(\d+)\s*months?']
    experience = []
    for pattern in experience_patterns:
        matches = re.findall(pattern, text.lower())
        experience.extend(matches)
    return experience if experience else ["Not Found"]

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
    recommended_jobs.sort(key=lambda x: x[2], reverse=True)
    return recommended_jobs

st.title("Resume Analyzer & Job Matching")

uploaded_file = st.file_uploader("Upload Your Resume (PDF)", type=["pdf"])

if uploaded_file is not None:
    resume_text = extract_text_from_pdf(uploaded_file)
    extracted_skills = extract_skills(resume_text)
    extracted_experience = extract_experience(resume_text)

    st.write("**Extracted Skills:**", extracted_skills)
    st.write("**Extracted Experience:**", extracted_experience)

    # Sidebar options
    option = st.sidebar.radio("Choose an option:", ["Get Matching Score", "Get Job Recommendations", "Show Visualizations"])

    if option == "Get Matching Score":
        job_description = st.text_area("Paste a Job Description", "")
        if job_description:
            similarity_score = match_resumes_to_jobs([resume_text], [job_description])
            st.write(f"Matching Score: {similarity_score[0][0]:.2f}")

    elif option == "Get Job Recommendations":
        job_df = load_job_data()
        recommended_jobs = recommend_jobs(extracted_skills, job_df)
        st.subheader("Recommended Job Postings")
        if recommended_jobs:
            for job, company, match_count, missing_skills in recommended_jobs[:10]:
                st.write(f"**{job}** at **{company}** - Matched Skills: {match_count}")
                st.write(f"Missing Skills: {', '.join(missing_skills) if missing_skills else 'None'}")
        else:
            st.write("No suitable job recommendations found.")

    elif option == "Show Visualizations":
        job_df = load_job_data()
        recommended_jobs = recommend_jobs(extracted_skills, job_df)
        missing_skills_counter = Counter()
        for _, _, _, missing_skills in recommended_jobs:
            missing_skills_counter.update(missing_skills)

        if missing_skills_counter:
            fig, ax = plt.subplots()
            ax.bar(missing_skills_counter.keys(), missing_skills_counter.values(), color="#ff5733")
            ax.set_xlabel("Missing Skills")
            ax.set_ylabel("Frequency")
            ax.set_title("Skills You Need to Improve")
            plt.xticks(rotation=45)
            st.pyplot(fig)
        else:
            st.write("No missing skills found.")
else:
    st.warning("Please upload a resume first.")
