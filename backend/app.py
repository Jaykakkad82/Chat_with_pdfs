from flask import Flask, request, jsonify
from flask_cors import CORS
# from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceInstructEmbeddings
from langchain.vectorstores import FAISS
# from langchain.chat_models import ChatOpenAI
from langchain_community.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.schema import AIMessage, HumanMessage
import os

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests, consider restricting origins in production

# Load environment variables
# load_dotenv()

# Initialize session storage
conversations = {}

def get_pdf_text(pdf_files):
    text = ""
    for pdf in pdf_files:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator="",
        chunk_size=800,
        chunk_overlap=50,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks

def get_vectorstore(text_chunks, api_key):
    embeddings = OpenAIEmbeddings(api_key=api_key)
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vectorstore

def get_conversation_chain(vectorstore, api_key):
    llm = ChatOpenAI(api_key=api_key)
    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory
    )
    return conversation_chain

@app.route('/api/v1/store-api-key', methods=['POST'])
def store_api_key():
    data = request.json
    session_id = data.get('session_id', 'default')
    api_key = data.get('api_key')
    
    if not api_key:
        return jsonify({"error": "API key is missing"}), 400
    
    # Store the API key for the session
    conversations[session_id] = {"api_key": api_key}
    
    return jsonify({"message": "API key stored successfully", "session_id": session_id})

@app.route('/api/v1/upload-pdfs', methods=['POST'])
def upload_pdfs():
    if 'pdfs' not in request.files:
        return jsonify({"error": "No PDF files uploaded"}), 400

    session_id = request.form.get('session_id', 'default')

    if session_id not in conversations or 'api_key' not in conversations[session_id]:
        return jsonify({"error": "No API key found for this session"}), 400

    api_key = conversations[session_id]['api_key']

    pdf_files = request.files.getlist('pdfs')
    raw_text = get_pdf_text(pdf_files)
    text_chunks = get_text_chunks(raw_text)
    vectorstore = get_vectorstore(text_chunks, api_key)
    
    # Create conversation chain and store it
    conversations[session_id]["conversation_chain"] = get_conversation_chain(vectorstore, api_key)
    
    return jsonify({"message": "PDFs processed successfully", "session_id": session_id})

@app.route('/api/v1/ask-question', methods=['POST'])
def ask_question():
    data = request.json
    session_id = data.get('session_id', 'default')
    user_question = data.get('question')
    
    if session_id not in conversations or "conversation_chain" not in conversations[session_id]:
        return jsonify({"error": "No active session found"}), 400
    
    conversation_chain = conversations[session_id]["conversation_chain"]
    response = conversation_chain({'question': user_question})
    
    # Extract the content of each message in chat_history and serialize it
    serialized_chat_history = []
    for message in response['chat_history']:
        if isinstance(message, HumanMessage) or isinstance(message, AIMessage):
            serialized_chat_history.append(message.content)
        else:
            serialized_chat_history.append(str(message))
    
    return jsonify({
        "answer": response['answer'],
        "chat_history": serialized_chat_history
    })

if __name__ == '__main__':
    app.run(debug=True)
