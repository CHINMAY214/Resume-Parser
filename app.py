import os
import re
import PyPDF2
import spacy
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import subprocess

# Check if spaCy model exists, if not, download it
model_name = "en_core_web_sm"
try:
    nlp = spacy.load(model_name)
except OSError:
    subprocess.run(["python", "-m", "spacy", "download", model_name])
    nlp = spacy.load(model_name)

print("spaCy model loaded successfully!")

# Load NLP model
nlp = spacy.load("en_core_web_sm")

def extract_text_from_pdf(pdf_file):
    """Extract text from an uploaded PDF file."""
    text = ""
    reader = PyPDF2.PdfReader(pdf_file)
    for page in reader.pages:
        text += page.extract_text() + " "
    return text

def extract_skills(text):
    """Extract skills from text using NLP."""
    doc = nlp(text.lower())
    skills = set()
    skill_keywords = {"python", "sql", "mysql", "machine learning", "data science", "data analysis",
                      "excel", "deep learning", "nlp", "java", "c++", "power bi", "streamlit", "azure"}

    for token in doc:
        if token.text in skill_keywords:
            skills.add(token.text)

    return list(skills)

def extract_experience(text):
    """Extract experience details from text."""
    experience_patterns = [r'\b\d+\s+years?\b', r'\b\d+\s+months?\b']
    experience = []
    for pattern in experience_patterns:
        matches = re.findall(pattern, text.lower())
        experience.extend(matches)
    return experience

def match_resumes_to_jobs(resume_texts, job_descriptions):
    """Match resumes to job descriptions using TF-IDF and cosine similarity."""
    vectorizer = TfidfVectorizer()
    all_texts = resume_texts + job_descriptions
    tfidf_matrix = vectorizer.fit_transform(all_texts)

    resume_vectors = tfidf_matrix[:len(resume_texts)]
    job_vectors = tfidf_matrix[len(resume_texts):]

    similarity_matrix = cosine_similarity(resume_vectors, job_vectors)
    return similarity_matrix

# Streamlit UI
st.title("Resume Analyzer & Job Matching")

uploaded_file = st.file_uploader("Upload Your Resume (PDF)", type=["pdf"])

if uploaded_file is not None:
    st.subheader("Extracted Information")
    resume_text = extract_text_from_pdf(uploaded_file)
    extracted_skills = extract_skills(resume_text)
    extracted_experience = extract_experience(resume_text)
    
    st.write("**Extracted Skills:**", extracted_skills)
    st.write("**Extracted Experience:**", extracted_experience if extracted_experience else "Not Found")
    
    job_descriptions = [
        "Looking for a Python developer with experience in machine learning and SQL.",
        "Data analyst role requiring expertise in Excel, SQL, and data visualization."
    ]
    
    similarity_scores = match_resumes_to_jobs([resume_text], job_descriptions)
    
    st.subheader("Job Matching Scores")
    for i, job in enumerate(job_descriptions):
        st.write(f"**Job {i+1}:** {job}")
        st.write(f"**Matching Score:** {similarity_scores[0][i]:.2f}")
