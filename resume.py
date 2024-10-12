import os
import chainlit as cl
from dotenv import load_dotenv
import logging
import re
from PyPDF2 import PdfReader       
from docx import Document

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

@cl.on_chat_start
async def main():
    await cl.Message(content="Welcome to the Resume Evaluation Chatbot! Type 'upload resume' to get started.").send()

# Function to handle user messages
@cl.on_message
async def handle_message(message: cl.Message):
    user_input = message.content.lower().strip()
    
    if "upload resume" in user_input:
        await handle_file_upload()
    else:
        await cl.Message(content="Please type 'upload resume' to submit your resume.").send()

async def handle_file_upload():
    try:
        files = await cl.AskFileMessage(
            content="Please upload your resume (PDF or Word).",
            accept=[
                "application/pdf", 
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ]
        ).send()

        if files and len(files) > 0:
            resume_file = files[0]  # Get the first uploaded file
            logging.info(f"Received file: {resume_file.name}, Type: {resume_file.type}")

            # Extract text from the uploaded resume file
            resume_text = await extract_text_from_file(resume_file)

            # Analyze the resume text
            rating, feedback = analyze_resume(resume_text)

            # After analyzing, evaluate the resume and provide suggestions for improvement
            is_good, suggestions = evaluate_resume(resume_text)
            suggestion_message = "\n".join(suggestions) if suggestions else "Your resume looks good!"

            # Send feedback and suggestions to the user
            await cl.Message(content=f"Your resume rating is: {rating}/100\n\nFeedback:\n{feedback}\n\nSuggestions:\n{suggestion_message}").send()
        else:
            await cl.Message(content="No file uploaded. Please try again.").send()
    except Exception as e:
        logging.error(f"Error during file upload: {e}")
        await cl.Message(content="An error occurred while uploading your resume. Please try again.").send()

async def extract_text_from_file(resume_file):
    """Extract text from PDF or Word document."""
    
    # Assume resume_file has a 'path' attribute to access the file on disk
    file_path = resume_file.path
    
    if resume_file.type == "application/pdf":
        # Extract text from PDF
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
    elif resume_file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
                              "application/msword"]:
        # Extract text from Word document
        doc = Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
    
    return text

def analyze_resume(resume_text):
    # Initialize scoring criteria
    score = 0
    feedback = []

    # 1. Technical Skills & Keywords
    technical_keywords = [
        "Python", "R", "SQL", "Java", "C++", "Julia",
        "TensorFlow", "PyTorch", "Scikit-learn", "Keras",
        "Pandas", "NumPy", "Spark", "Hadoop",
        "Matplotlib", "Seaborn", "Tableau", "Power BI",
        "MySQL", "PostgreSQL", "MongoDB",
        "Deep Learning", "NLP", "Computer Vision",
        "Statistical Analysis", "Big Data", "Data Mining",
        "Predictive Modeling", "Git", "AWS", "Azure", "Google Cloud",
        "Docker", "Kubernetes", "Jupyter", "VS Code", "PyCharm"
    ]
    matched_technical = [kw for kw in technical_keywords if re.search(r'\b' + re.escape(kw.lower()) + r'\b', resume_text.lower())]
    if matched_technical:
        score += len(matched_technical) * 2  # Each keyword adds 2 points
        feedback.append(f"Technical Skills Found: {', '.join(set(matched_technical))}")
    else:
        feedback.append("No relevant technical skills or keywords found.")

    # 2. Educational Background
    education_patterns = [
        r"(b\.?tech|bachelor|master|ph\.?d\.)\s+in\s+(computer science|statistics|mathematics|data science|related fields)"
    ]
    education_matches = [match for pattern in education_patterns for match in re.findall(pattern, resume_text.lower())]
    if education_matches:
        score += 20
        feedback.append("Relevant educational background found.")
    else:
        feedback.append("No relevant educational background found.")

    # 3. Certifications & Courses
    certifications = [
        "aws certified machine learning", "google professional data engineer",
        "microsoft certified azure data scientist associate",
        "coursera", "edx", "udacity", "nanodegree"
    ]
    matched_certifications = [cert.title() for cert in certifications if re.search(cert, resume_text.lower())]
    if matched_certifications:
        score += len(matched_certifications) * 3  # Each certification adds 3 points
        feedback.append(f"Certifications/Courses Found: {', '.join(set(matched_certifications))}")
    else:
        feedback.append("No certifications or relevant courses found.")

    # 4. Project Experience
    project_patterns = [
        r"project", r"developed", r"implemented", r"built", r"deployed", r"analyzed"
    ]
    projects = [word for word in project_patterns if word in resume_text.lower()]
    if projects:
        score += len(projects) * 2  # Each project-related keyword adds 2 points
        feedback.append(f"Project Experience Mentioned: {len(projects)} instances found.")
    else:
        feedback.append("No project experience found.")

    # 5. Work Experience
    work_patterns = [
        r"data scientist", r"machine learning engineer", r"data analyst",
        r"research scientist", r"model developer", r"data engineer"
    ]
    work_experiences = [role.title() for role in work_patterns if re.search(role, resume_text.lower())]
    if work_experiences:
        score += len(work_experiences) * 5  # Each role adds 5 points
        feedback.append(f"Relevant Work Experience: {', '.join(set(work_experiences))}")
    else:
        feedback.append("No relevant work experience found.")

    # 6. Publications & Contributions
    publication_patterns = [
        r"published", r"research paper", r"conference", r"journal",
        r"open source", r"github"
    ]
    publications = [word for word in publication_patterns if word in resume_text.lower()]
    if publications:
        score += len(publications) * 2  # Each publication-related keyword adds 2 points
        feedback.append(f"Publications/Contributions Mentioned: {len(publications)} instances found.")
    else:
        feedback.append("No publications or open-source contributions found.")

    # 7. Soft Skills & Leadership
    soft_skills = [
        "problem-solving", "critical thinking", "communication", "teamwork",
        "project management", "leadership", "mentoring", "managed", "led"
    ]
    matched_soft_skills = [skill for skill in soft_skills if re.search(r'\b' + re.escape(skill.lower()) + r'\b', resume_text.lower())]
    if matched_soft_skills:
        score += len(set(matched_soft_skills)) * 2  # Each unique soft skill adds 2 points
        feedback.append(f"Soft Skills Found: {', '.join(set(matched_soft_skills))}")
    else:
        feedback.append("No soft skills or leadership roles mentioned.")

    # 8. Resume Formatting & Clarity
    # Simple checks for clarity and formatting
    grammar_errors = 0  # Placeholder for grammar checking logic
    if grammar_errors == 0:
        score += 10
        feedback.append("Resume formatting and clarity are good.")
    else:
        score -= grammar_errors * 2
        feedback.append(f"Detected {grammar_errors} grammar/spelling errors.")

    # 9. Tools & Technologies Proficiency
    tools = [
        "git", "github", "gitlab", "aws", "azure", "google cloud",
        "docker", "kubernetes", "jupyter", "vs code", "pycharm"
    ]
    matched_tools = [tool.title() for tool in tools if re.search(r'\b' + re.escape(tool.lower()) + r'\b', resume_text.lower())]
    if matched_tools:
        score += len(set(matched_tools)) * 2
        feedback.append(f"Tools & Technologies Proficiency: {', '.join(set(matched_tools))}")
    else:
        feedback.append("No tools or technologies proficiency mentioned.")

    # 10. Overall Resume Length
    word_count = len(resume_text.split())
    if word_count < 400:
        feedback.append("Resume is too short. Consider adding more details about your experience and projects.")
        score -= 5
    elif word_count > 1200:
        feedback.append("Resume is too long. Try to make it more concise and focused.")
        score -= 5
    else:
        feedback.append("Resume length is appropriate.")
        score += 5

    # Cap the score between 0 and 100
    score = max(0, min(score, 100))

    # Detailed Feedback
    detailed_feedback = "\n".join(feedback)

    return score, detailed_feedback

# Function to evaluate the resume and provide suggestions
def evaluate_resume(resume_text):
    suggestions = []
    
    # Basic checks for common resume elements
    if len(resume_text) < 300:  # Example check for length
        suggestions.append("Your resume seems a bit short. Consider adding more details about your experience and skills.")
    
    if "experience" not in resume_text.lower():
        suggestions.append("Make sure to include a section on your work experience.")
    
    if "education" not in resume_text.lower():
        suggestions.append("Don't forget to include your educational background.")
    
    if "skills" not in resume_text.lower():
        suggestions.append("Highlight your skills to showcase your qualifications.")
    
    if not suggestions:
        return True, []  # Resume is good
    else:
        return False, suggestions  # Resume needs improvement

if __name__ == "__main__":
    cl.run()
