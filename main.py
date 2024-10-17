from operator import itemgetter

import PyPDF2
import chainlit as cl
from chainlit import user_session, ThreadDict
from langchain.memory import ConversationBufferMemory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import MessagesPlaceholder, ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_groq import ChatGroq  # Importing Groq LLM
from rag import generate_question1, vectorize_text
from evaluateresume import generate_job_description, evaluate_resume_with_groq
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

def setup_runnable():
    memory = cl.user_session.get("memory")  # type: ConversationBufferMemory
    model = init_groq_model()
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful chatbot"),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ]
    )

    runnable = (
        RunnablePassthrough.assign(
            history=RunnableLambda(memory.load_memory_variables) | itemgetter("history")
        )
        | prompt
        | model
        | StrOutputParser()
    )
    cl.user_session.set("runnable", runnable)

@cl.oauth_callback
def oauth_callback(
  provider_id: str,
  token: str,
  raw_user_data: Dict[str, str],
  default_user: cl.User,
) -> Optional[cl.User]:
  return default_user

# Initialize the Groq model
def init_groq_model():
    return ChatGroq(
        model="llama-3.1-8b-instant",  # Groq model used
        temperature=0.0,
        max_retries=2,
        api_key="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"
    )

llm = init_groq_model()

async def generate_question(previous_responses):
    if not previous_responses:  # If no previous responses, ask a general question
        return "What is your name?"

    # Otherwise, generate a question based on the previous responses
    prompt = f"""
    You are an interview helper chatbot. Based on the following responses, generate the next interview question.
    You must help the user improve in interview aspects.
    Ask them to introduce themselves first. 
    Then based on previous response ask questions from their domain.
    Previous responses:
    {previous_responses}
    Just display the question alone. I don't want it to be inside double quotes.
    """
    response = llm.invoke([("system", prompt)])

    return response.content.strip()  # Get the generated question

# Validation function using Groq LLM
async def validate_answer_groq(question, answer):
    prompt = f"""
        You are an interviewer. Evaluate the answer below.
        If the answer is at least partially correct (even around 20%), acknowledge it by responding 'yes'. 
        If the answer is mostly incorrect or irrelevant, kindly suggest how the user can improve.

        Question: {question}
        Answer: {answer}
        """

    response = llm.invoke([("system", prompt), ("human", answer)])
    validation_result = response.content.lower()

    if "yes" in validation_result:
        return True, None
    else:
        return False, validation_result

@cl.set_chat_profiles
async def chat_profile():
    return [
        cl.ChatProfile(
            name="General Mode",
            markdown_description="Starts directly with interview.",
        ),
        cl.ChatProfile(
            name="Interview Mode",
            markdown_description="Must need a resume to start interview.",
        ),
        cl.ChatProfile(
            name="Resume ATS checker",
            markdown_description="Need a resume.",
        ),
    ]

@cl.on_chat_start
async def start_chat():
    chat_profile = cl.user_session.get("chat_profile")
    if chat_profile == "General Mode":
        await cl.Message(content="Welcome to interview helper chatbot.\n\nLet's start with the interview.").send()
        user_session.responses = []
        user_session.last_question = "What is Your name?"  # To store the last question asked
        user_session.question_count = 0
        await ask_question(docs = None)
    elif chat_profile == "Interview Mode":
        await cl.Message(content="Welcome to interview helper chatbot.\n\n").send()
        files = None
        while files == None:
            files = await cl.AskFileMessage(content= "To start the interview kindly upload your resume.",accept=["text/csv", "application/pdf"]).send()
        text_file = files[0]
        # Read PDF content using PyPDF2 PdfReader (updated for PyPDF2 3.0.0)
        docs = extract_text(text_file)
        user_session.set("docs", docs)
        print(docs)
        user_session.responses = []
        user_session.last_question = "Tell me about Yourself"  # To store the last question asked
        user_session.question_count = 0
        await ask_question(docs)
    else:
        await cl.Message(content="Welcome to Resume ATS checker..\n\n").send()
        files = None
        while files == None:
            files = await cl.AskFileMessage(content="To find the ATS score, Kindly upload your resume.",accept=["text/csv", "application/pdf"]).send()
        text_file = files[0]
        # Read PDF content using PyPDF2 PdfReader (updated for PyPDF2 3.0.0)
        docs = extract_text(text_file)
        job_description = await generate_job_description()
        rating, missing_keywords, feedback = await evaluate_resume_with_groq(docs, job_description)
        feedback_message = (
            f"\n{feedback}"
        )
        await cl.Message(content=feedback_message).send()
def extract_text(text_file):
    with open(text_file.path, 'rb') as file:  # Open in binary mode
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:  # Ensure that text was extracted
                text += page_text + "\n"
        return text

async def ask_question(docs):
    # Stop if 10 questions have been asked
    if user_session.question_count >= 5:
        await conclude_interview()
        return
    chat = cl.user_session.get("chat_profile")
    # Generate a new question based on previous responses
    previous_responses = "\n".join(user_session.responses)
    previous_questions = "\n".join(user_session.last_question)
    if chat == "General Mode":
        question = await generate_question(previous_responses)
    else:
        retriever = vectorize_text(docs)
        question = await generate_question1(previous_responses,retriever,previous_questions)
    user_session.last_question = question  # Save the last question for validation
    user_session.question_count += 1  # Increment the question count
    await cl.Message(content=question).send()

@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    memory = ConversationBufferMemory(return_messages=True)
    root_messages = [m for m in thread["steps"] if m["parentId"] == None]
    for message in root_messages:
        if message["type"] == "user_message":
            memory.chat_memory.add_user_message(message["output"])
        else:
            memory.chat_memory.add_ai_message(message["output"])

    cl.user_session.set("memory", memory)

    setup_runnable()

@cl.on_message
async def handle_message(message: str):
    cha = user_session.get("chat_profile")
    docs = user_session.get("docs")
    answer = message.content
    last_question = user_session.last_question  # Get the last question asked

    if last_question:
        # Validate the response using Groq LLM
        is_valid, feedback = await validate_answer_groq(last_question, answer)

        if is_valid:
            user_session.responses.append(answer)  # Add the valid answer to the responses
        else:
            await cl.Message(
                content=f"That doesn't seem quite right.\n\n {feedback} \n\nCould you please try answering again?").send()
            return  # Stop here and let the user re-answer
    if cha == "General Mode":
        await ask_question(docs=None)  # Ask the next question if the current answer is valid
    else:
        await ask_question(docs)
async def conclude_interview():

    await cl.Message(content="We will assess your responses. Thank you for completing the interview! We'll get back to you soon.").send()