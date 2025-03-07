import os
import re
import PyPDF2
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rapidfuzz import process
import matplotlib.pyplot as plt
from collections import Counter

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

def match_skills(text, skill_list):
    """Fuzzy match skills using RapidFuzz."""
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

    # Job title matching (Fixed: Uses resume_text)
    job_titles = ["Data Analyst", "Machine Learning Engineer", "Software Developer", "Python Developer"]
    matches = [title for title in job_titles if title.lower() in resume_text.lower()]
    st.write("**Matched Job Titles:**", matches if matches else "No matches found")

    # Job description matching
    job_description = st.text_area("Paste a Job Description", "")
    if job_description:
        similarity_score = match_resumes_to_jobs([resume_text], [job_description])
        st.write(f"Matching Score: {similarity_score[0][0]:.2f}")

    # Skill visualization
    import matplotlib.pyplot as plt

# Skill visualization (Fixed)
skill_counts = Counter(extracted_skills)

if skill_counts:
    fig, ax = plt.subplots()  # Create a figure and axis
    ax.bar(skill_counts.keys(), skill_counts.values())  # Plot the bar chart
    ax.set_xlabel("Skills")
    ax.set_ylabel("Frequency")
    ax.set_title("Extracted Skills from Resume")
    st.pyplot(fig)  # Pass the figure to Streamlit
else:
    st.write("No skills extracted to display.")

else:
    st.warning("Please upload a resume first.")  # Prevents `resume_text` from being used before assignment
