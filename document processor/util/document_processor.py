import requests
import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

# You might need to replace `some_library` and `another_library` with actual imports depending on where these classes and functions come from.

def get_vectorstore_from_url(url):
    # get the text in document form
    loader = WebBaseLoader(url)
    document = loader.load()
    
    # split the document into chunks
    text_splitter = RecursiveCharacterTextSplitter()
    document_chunks = text_splitter.split_documents(document)
    
    # create a vectorstore from the chunks
    vector_store = Chroma.from_documents(document_chunks, OpenAIEmbeddings())

    return vector_store

def get_context_retriever_chain(vector_store):
    llm = ChatOpenAI()
    
    retriever = vector_store.as_retriever()
    
    prompt = ChatPromptTemplate.from_messages([
      MessagesPlaceholder(variable_name="chat_history"),
      ("user", "{input}"),
      ("user", "Given the above conversation, generate a search query to look up in order to get information relevant to the conversation")
    ])
    
    retriever_chain = create_history_aware_retriever(llm, retriever, prompt)
    
    return retriever_chain
    

def get_conversational_rag_chain(retriever_chain): 
    llm = ChatOpenAI()
    
    prompt = ChatPromptTemplate.from_messages([
      ("system", "Answer thoughtfully in bullets the user's  based on the below context:\n\n{context}"),
      MessagesPlaceholder(variable_name="chat_history"),
      ("user", "{input}"),
    ])
    
    stuff_documents_chain = create_stuff_documents_chain(llm, prompt)
    
    return create_retrieval_chain(retriever_chain, stuff_documents_chain)


import re
from datetime import datetime

def extract_facts(question, document_url):
    # Step 1: Extract the date from the URL
    date_match = re.search(r'call_log_(\d{8})', document_url)
    if date_match:
        date_str = date_match.group(1)
        document_date = datetime.strptime(date_str, '%Y%m%d').date()
    else:
        raise ValueError("Date not found in URL or URL format is incorrect.")

    # Step 2: Create a vector store from the document and process it
    # These functions (get_vectorstore_from_url, get_context_retriever_chain, get_conversational_rag_chain)
    # are assumed to be defined elsewhere in your codebase
    vector_store = get_vectorstore_from_url(document_url)
    retriever_chain = get_context_retriever_chain(vector_store)
    conversational_rag_chain = get_conversational_rag_chain(retriever_chain)

    # Assuming the initialization of chat_history
    chat_history = []  # Initialize based on your application's logic
    
    # Invoke the chain to get the response
    response = conversational_rag_chain.invoke({
        "chat_history": chat_history,
        "input": question
    })

    # Extracted facts from the response
    # Ensure response handling accounts for possible errors or unexpected formats
    if 'answer' in response:
        facts = [response['answer']]  # Assuming the response contains the extracted facts as a string
    else:
        raise ValueError("Expected 'answer' key in response not found.")

    # Step 3: Organize facts by date
    facts_by_date = {str(document_date): facts}

    return facts_by_date



###def get_response(user_input, vector_store, chat_history):
    retriever_chain = get_context_retriever_chain(vector_store)
    conversation_rag_chain = get_conversational_rag_chain(retriever_chain)
    
    response = conversation_rag_chain.invoke({
        "chat_history": chat_history,
        "input": user_input
    })
    
    return response['answer']
