import os
import re
import PyPDF2
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def extract_text_from_pdf(pdf_file):
    """Extract text from an uploaded PDF file."""
    text = ""
    reader = PyPDF2.PdfReader(pdf_file)
    for page in reader.pages:
        extracted_text = page.extract_text()
        if extracted_text:
            text += extracted_text + " "
    return text

def extract_skills(text):
    """Extract skills using regular expressions."""
    skill_keywords = {
        "python", "sql", "mysql", "machine learning", "data science", "data analysis",
        "excel", "deep learning", "nlp", "java", "c++", "power bi", "streamlit", "azure"
    }
    
    words = re.findall(r'\b\w+\b', text.lower())  # Tokenize text
    skills = list(skill_keywords.intersection(words))
    
    return skills

def extract_experience(text):
    """Extract experience details using regex."""
    experience_patterns = [
        r'(\d+)\s*years?',
        r'(\d+)\s*months?'
    ]
    
    experience = []
    for pattern in experience_patterns:
        matches = re.findall(pattern, text.lower())
        experience.extend(matches)
    
    return experience if experience else ["Not Found"]

def match_resumes_to_jobs(resume_texts, job_descriptions):
    """Match resumes to job descriptions using TF-IDF and cosine similarity."""
    vectorizer = TfidfVectorizer()
    all_texts = resume_texts + job_descriptions
    tfidf_matrix = vectorizer.fit_transform(all_texts)

    resume_vectors = tfidf_matrix[:len(resume_texts)]
    job_vectors = tfidf_matrix[len(resume_texts):]

    similarity_matrix = cosine_similarity(resume_vectors, job_vectors)
    return similarity_matrix
from rapidfuzz import process

def match_skills(text, skill_list):
    words = re.findall(r'\b\w+\b', text.lower())
    matched_skills = [process.extractOne(word, skill_list)[0] for word in words if process.extractOne(word, skill_list)[1] > 80]
    return list(set(matched_skills))


# Streamlit UI
st.title("Resume Analyzer & Job Matching")

uploaded_file = st.file_uploader("Upload Your Resume (PDF)", type=["pdf"])

if uploaded_file is not None:
    st.subheader("Extracted Information")
    resume_text = extract_text_from_pdf(uploaded_file)
    
    extracted_skills = extract_skills(resume_text)
    extracted_experience = extract_experience(resume_text)

    st.write("**Extracted Skills:**", extracted_skills)
    st.write("**Extracted Experience:**", extracted_experience)

    job_descriptions = [
        "Looking for a Python developer with experience in machine learning and SQL.",
        "Data analyst role requiring expertise in Excel, SQL, and data visualization."
    ]

    similarity_scores = match_resumes_to_jobs([resume_text], job_descriptions)

    st.subheader("Job Matching Scores")
    for i, job in enumerate(job_descriptions):
        st.write(f"**Job {i+1}:** {job}")
        st.write(f"**Matching Score:** {similarity_scores[0][i]:.2f}")
