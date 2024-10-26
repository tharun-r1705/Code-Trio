import os
import asyncio
from together import AsyncTogether
from dotenv import load_dotenv
import chainlit as cl

load_dotenv()
async_client = AsyncTogether(api_key=os.environ.get('TOGETHER_API'))

# Initialize a list to hold questions and answers
questions_and_answers = []

async def generate_questions_and_answers():
    # Create a prompt to generate questions
    prompt = f"""
        Your job is to ask aptitude questions.
        Give 4 options.
        Ask easy questions.
        """
    tasks = [
        async_client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-405B-Instruct-Lite-Pro",
            messages=[{"role": "user", "content": prompt}],
        )
    ]
    responses = await asyncio.gather(*tasks)

    # Process the response to create questions and answers
    for response in responses:
        # Assuming the response is in the desired format
        content = response.choices[0].message.content
        # Here you would need to parse the content to extract questions and options
        # For now, we will mock the questions for demonstration purposes
        return [
            {"question": "If a train travels 60 miles in 1 hour, how far will it travel in 3 hours?",
             "options": ["A) 120 miles", "B) 180 miles", "C) 240 miles", "D) 300 miles"], "answer": "B"},
            {"question": "What is 5 + 3?",
             "options": ["A) 6", "B) 7", "C) 8", "D) 9"], "answer": "C"},
            {"question": "How many days are there in a week?",
             "options": ["A) 5", "B) 6", "C) 7", "D) 8"], "answer": "C"},
            {"question": "What is the capital of France?",
             "options": ["A) Berlin", "B) Madrid", "C) Paris", "D) Rome"], "answer": "C"},
            {"question": "Which shape has three sides?",
             "options": ["A) Square", "B) Triangle", "C) Circle", "D) Rectangle"], "answer": "B"},
        ]

@cl.on_chat_start
async def greet_user():
    # Generate questions and answers before starting the quiz
    global questions_and_answers
    questions_and_answers = await generate_questions_and_answers()
    await cl.Message(content="Welcome to the aptitude quiz! Let's get started.").send()
    await ask_question()

# Track the current question index
current_question_index = 0

async def ask_question():
    global current_question_index
    if current_question_index < len(questions_and_answers):
        q_and_a = questions_and_answers[current_question_index]
        question = q_and_a["question"]
        options = "\n".join(q_and_a["options"])
        await cl.Message(content=f"Question {current_question_index + 1}: {question}\n{options}").send()
    else:
        await cl.Message(content="Quiz complete! Thanks for participating.").send()

@cl.on_message
async def on_message(message: cl.Message):
    global current_question_index
    user_answer = message.content.strip().upper()

    # Check if the answer is correct
    correct_answer = questions_and_answers[current_question_index]["answer"]
    if user_answer == correct_answer:
        await cl.Message(content="Correct! 🎉").send()
    else:
        await cl.Message(content=f"Incorrect. The correct answer was {correct_answer}.").send()

    # Move to the next question
    current_question_index += 1
    await ask_question()
