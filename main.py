import PyPDF2
import chainlit as cl
from chainlit import user_session
from langchain_groq import ChatGroq  # Importing Groq LLM
from rag import generate_question1, vectorize_text

# Initialize the Groq model
def init_groq_model():
    return ChatGroq(
        model="llama-3.1-70b-versatile",  # Groq model used
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
    You are an interviewer. Check the answer below. 
    If the answer is irrelevant, suggest the user how they can improve.
    Otherwise, simply respond with 'yes'.

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
    else:
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
