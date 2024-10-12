import os
import chainlit as cl
from dotenv import load_dotenv
import logging
import re
from PyPDF2 import PdfReader       
from docx import Document
from langchain_groq import ChatGroq  # Import the ChatGroq class

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize the Groq model
def init_groq_model():
    return ChatGroq(
        model="llama-3.1-70b-versatile",
        temperature=0.0,
        max_retries=2,
        api_key=os.getenv("GROQ_API_KEY", "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")  # Ensure this is in your .env file
    )

groq_model = init_groq_model()

@cl.on_chat_start
async def main():
    intro_message = (
        "Welcome to the Resume Evaluation Chatbot! This chatbot will help you evaluate your resume against job descriptions.\n\n"
        "To get started, please upload your resume in PDF or Word format. The chatbot will analyze your resume and provide feedback on how well it matches industry standards and specific job requirements."
    )
    await cl.Message(content=intro_message).send()
    
    # Initiate the file upload process after the introduction
    await handle_file_upload()

# Function to handle file uploads
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

            # Generate a job description
            job_description = await generate_job_description()

            # Analyze the resume text using the Groq model
            rating, missing_keywords, feedback = await evaluate_resume_with_groq(resume_text, job_description)

            # Send feedback to the user
            feedback_message = (
                f"Feedback:\n{feedback}"
            )
            await cl.Message(content=feedback_message).send()
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

async def generate_job_description():
    """Generate a job description for comparison."""
    prompt = """
You are an experienced HR professional with expertise in Data Science, Full Stack Web Development, Big Data Engineering, DEVOPS, and Data Analysis.
Your task is to create a comprehensive job description for these roles, highlighting key responsibilities, required skills, and qualifications in a clear and concise manner.
    """
    response = groq_model.invoke([("system", prompt)])  # Invoke the model with the prompt
    job_description = response.content.strip()  # Extract job description from the model response
    return job_description

async def evaluate_resume_with_groq(resume_text, job_description):
    """Evaluate the resume using the GROQ model."""
    prompt = f"""
    You are a skilled ATS (Applicant Tracking System) scanner with a deep understanding of data science and ATS functionality. 
    Your task is to evaluate the resume against the provided job description.give rating out of 100.
    Please provide the percentage match, any missing keywords, and your final thoughts in a clear and structured format.
    
    **Job Description:**
    {job_description}
    
    **Resume Content:**
    {resume_text}
    
    Please include:
    - Percentage Match:
    - Missing Keywords:
    - Final Thoughts:
    """
    response = groq_model.invoke([("system", prompt)])  # Invoke the model with the prompt
    response_text = response.content.strip()

    # Parse the response to extract the rating and missing keywords
    match = re.search(r'(\d+)/100', response_text)
    rating = match.group(1) if match else "N/A"
    
    missing_keywords_match = re.search(r'Missing Keywords:\s*(.*)', response_text)
    missing_keywords = missing_keywords_match.group(1).strip() if missing_keywords_match else "None"

    # Return the rating, missing keywords, and full response text
    return rating, missing_keywords, response_text  # Return the rating, missing keywords, and feedback

if __name__ == "__main__":
    cl.run()
