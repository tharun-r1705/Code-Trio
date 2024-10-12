import pandas as pd
import chainlit as cl
from chainlit import user_session
import random
from langchain_groq import ChatGroq  # Importing Groq LLM

# Initialize the Groq model (or replace with your Llama model initialization)
def init_llama_model():
    return ChatGroq(
        model="llama3-8b-8192",  # Replace with your model name
        temperature=0.0,
        max_retries=2,
        api_key="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"  # Your API key here
    )

llm = init_llama_model()

# Load the Kaggle dataset (assuming it's in CSV format)
DATASET_PATH = 'public/Software Questions.csv'  # Make sure this path is correct and accessible
data = pd.read_csv(DATASET_PATH, encoding='ISO-8859-1')  # Adjust encoding if needed

# Extract a list of questions based on a column from the dataset
questions = data['Question'].tolist()  # Adjust 'Question' to the actual column name in your CSV

@cl.on_chat_start
async def start_chat():
    user_session.responses = []  # Initialize an empty list to store user responses
    user_session.remaining_questions = questions.copy()  # Copy of questions to track remaining ones
    await cl.Message(content="Welcome! Let's start the interview based on our dataset.").send()
    await ask_question()  # Start asking questions

async def ask_question():
    # Check if there are more questions to ask
    if user_session.remaining_questions:
        question = random.choice(user_session.remaining_questions)  # Randomly select a question
        user_session.remaining_questions.remove(question)  # Remove the selected question from remaining questions
        await cl.Message(content=question).send()  # Send the question to the user
    else:
        await conclude_interview()  # No more questions, conclude the interview

@cl.on_message
async def handle_message(message: cl.Message):
    answer = message.content  # Capture the user's response
    user_session.responses.append(answer)  # Store the answer

    # Evaluate the response using Llama model
    feedback = await evaluate_response_with_llama(answer)
    await cl.Message(content=feedback).send()  # Send feedback to the user

    await ask_question()  # Ask the next question

async def evaluate_response_with_llama(answer):
    # Prepare the prompt for evaluation
    prompt = f"""
    You are a feedback evaluator. Assess the following answer based on clarity, relevance, and depth.
    
    Answer: {answer}
    
    Provide a brief evaluation and suggest improvements if necessary.
    """

    # Call the Llama model to get the feedback
    response = llm.invoke([("system", prompt)])
    return response.content.strip()  # Get the generated feedback

async def conclude_interview():
    await cl.Message(content="Thank you for participating in the interview!").send()
    print("User Responses:", user_session.responses)  # Log user responses for further analysis
