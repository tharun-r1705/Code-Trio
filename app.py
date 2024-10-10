import os
import chainlit as cl
from chainlit import user_session
from langchain_groq import ChatGroq  # Importing Groq LLM

# Initialize the Groq model (adjust based on your Groq integration)
def init_groq_model():
    return ChatGroq(
        model="llama3-8b-8192",  # Groq model used
        temperature=0.0,
        max_retries=2,
        api_key="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"
    )

llm = init_groq_model()

# Validation function using Groq LLM
async def validate_answer_groq(question, answer):
    # Prompt the LLM to validate the answer and provide feedback
    prompt = f"""
    You are an interviewer. Check the answer below. 
    If the answer is irrelevant or insufficient, reply with a reason. 
    Otherwise, simply respond with 'yes'.

    Question: {question}
    Answer: {answer}
    """
    response = llm.invoke([("system", prompt),("human", answer)])

    validation_result = response.content

    # If Groq responds with 'yes', the answer is valid
    if "yes" in validation_result:
        return True, None
    else:
        # Return False and the feedback from Groq LLM
        return False, validation_result


# Define interview questions
INTERVIEW_QUESTIONS = [
    "What's your name?",
    "Can you tell me about yourself?",
    "Why are you interested in this position?",
    "What are your strengths and weaknesses?",
    "Where do you see yourself in five years?",
    "Do you have any questions for us?"
]


@cl.on_chat_start
async def start_chat():
    user_session.current_question = 0
    user_session.responses = []
    await cl.Message(content="Hello! I'm here to conduct your interview. Let's get started.").send()
    await ask_question()


async def ask_question():
    if user_session.current_question < len(INTERVIEW_QUESTIONS):
        question = INTERVIEW_QUESTIONS[user_session.current_question]
        await cl.Message(content=question).send()
    else:
        await conclude_interview()


@cl.on_message
async def handle_message(message: str):
    answer = message.content
    question_index = user_session.current_question

    # Get the current question
    question = INTERVIEW_QUESTIONS[question_index]

    # Validate the response using Groq LLM
    is_valid, feedback = await validate_answer_groq(question, answer)

    if is_valid:
        # If valid, move to the next question
        user_session.responses.append(answer)
        user_session.current_question += 1
    else:
        # If invalid, send feedback and ask the same question again
        await cl.Message(
            content=f"That doesn't seem quite right.\n\n {feedback} \n\nCould you please try answering again?").send()

    await ask_question()


async def conclude_interview():
    await cl.Message(content="Thank you for completing the interview! We'll get back to you soon.").send()
    # Optionally, process the responses
    print("User Responses:", user_session.responses)
