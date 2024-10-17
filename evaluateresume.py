from langchain_groq import ChatGroq
import os
import re

def init_groq_model():
    return ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0.0,
        max_retries=2,
        api_key=os.getenv("GROQ_API_KEY", "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")
        # Ensure this is in your .env file
    )


groq_model = init_groq_model()


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

    prompt1 = "You are an expert ATS (Applicant Tracking System) evaluator with in-depth knowledge of job matching algorithms. Your task is to assess the provided resume against the given job description, simulating how an ATS would rank it on a scale of 100."
    response = groq_model.invoke([("system", prompt)])  # Invoke the model with the prompt
    response_text = response.content.strip()
    # Parse the response to extract the rating and missing keywords
    match = re.search(r'(\d{1,3})\s*/\s*100|(\d{1,3})\s*%\s*match', response_text, re.IGNORECASE)
    rating = match.group(1) if match else "N/A"

    missing_keywords_match = re.search(r'Missing Keywords:\s*(.*)', response_text)
    missing_keywords = missing_keywords_match.group(1).strip() if missing_keywords_match else "None"

    # Return the rating, missing keywords, and full response text
    return rating, missing_keywords, response_text  # Return the rating, missing keywords, and feedback