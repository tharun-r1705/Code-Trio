import os
from langchain_community.vectorstores import FAISS
from langchain_google_vertexai import VertexAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import vertexai
from vertexai.language_models import TextEmbeddingModel
from langchain_groq import ChatGroq
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

llm = ChatGroq(
        model="llama-3.1-8b-instant",  # Groq model used
        temperature=0.0,
        max_retries=2,
        api_key="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"
    )

'''google credentials setup'''
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'angelic-archery-434703-n1-72fb5ce2bbca.json'

'''vectorization using vertex ai'''
PROJECT_ID = "angelic-archery-434703-n1"
REGION = "us-central1"
MODEL_ID = "textembedding-gecko@001"

# chat = ChatGroq(model = "gemma2-9b-it")

vertexai.init(project=PROJECT_ID, location=REGION)
model = TextEmbeddingModel.from_pretrained("textembedding-gecko-multilingual@001")
embeddings = VertexAIEmbeddings(model=MODEL_ID)

# Specify the path to your PDF file
def vectorize_text(docs, k=10):  # Limit to top 10 documents
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_text(docs)

    # Create FAISS vectorstore
    embedding = VertexAIEmbeddings(model_name=MODEL_ID)
    vectorstore = FAISS.from_texts(texts=splits, embedding=embedding)

    # Retrieve and generate using the relevant snippets of the blog.
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    return retriever


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

async def generate_question1(previous_responses, retriever,previous_questions):
    if not previous_responses:  # If no previous responses, ask a general question
        return "Tell me about Yourself"
    system_prompt = (
        "As an interviewer, your role is to use the candidate's resume to ask relevant and insightful questions."
        " Thoroughly analyze the resume to cover different areas, ensuring a well-rounded interview."
        " Adapt your questions based on previous interactions and the candidate's responses."
        f"{previous_questions}"
        "The way of asking questions should not repeat the previous question."
        "Don't repeat the same questions."
        " Formulate follow-up questions based on earlier answers."
        f"{previous_responses}"
        " Only provide the next question, focusing on maintaining the flow of the conversation."
        "\n\n"
        "{context}")

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt)
        ]
    )
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    response = rag_chain.invoke({"input": "Can you ask questions based on the given content?"})
    return response["answer"]

