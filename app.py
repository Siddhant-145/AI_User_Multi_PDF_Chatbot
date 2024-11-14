import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai


from langchain.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))



#Read PDFs and return the text
def get_pdf_text(pdf_docs):
    text =""
    for pdf in pdf_docs:
        pdf_reading = PdfReader(pdf)

        for page in pdf_reading.pages:
            text += page.extract_text()
    return text 

# Divide the text into chunks 

def get_text_chunks(text):
    #text_splitter is obj of Recursice text splitter class with parameters and split_text func of the obj of this class make chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size = 500, chunk_overlap = 100)
    chunks = text_splitter.split_text(text)
    return chunks

def get_vector_store(text_chunks):
    google_embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = FAISS.from_texts(text_chunks, embedding=google_embeddings)
    vector_store.save_local("faiss_index")


# def get_conversional_chain():
#      prompt_template = """
#     Answer the question as detailed as possible from the provided context, make sure to provide all the details, if the answer is not in
#     provided context just say, "answer is not available in the context", provide the answer according to you But mention the line coming up before the answer -"The answer is not present in pdf" if you generate your own answer \n\n
#     Context:\n {context}?\n
#     Question: \n{question}\n

#     Answer:
#     """
#      model = ChatGoogleGenerativeAI(model= "gemini-pro", temperature= 0.3 )
#      promt = PromptTemplate(template= prompt_template, input_variables=["context","question"])
#      chain = load_qa_chain(model, chain_type="stuff", promt= promt)
#      return chain

def get_conversional_chain():
    prompt_template = """
    Answer the question as detailed as possible from the provided context, make sure to provide all the details, if the answer is not in
    provided context just say, "answer is not available in the context", do not provide the wrong answer   \n\n
    Context:\n {context}?\n
    Question: \n{question}\n

    Answer:
    """
    model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)
    promt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=promt)  
    return chain



def user_input(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    # Check if the index file exists before loading
    if not os.path.exists("faiss_index"):
        st.error("FAISS index file not found. Please process your PDFs first.")
        return

    # Load FAISS index
    new_db = FAISS.load_local("faiss_index", embeddings,allow_dangerous_deserialization=True)
    docs = new_db.similarity_search(user_question)

    chain = get_conversional_chain()
    response = chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)

    print(response)
    st.write("Answer:", response["output_text"])


def main():
    st.set_page_config("Chat With Multiple PDFs")
    st.header("Chat With Multiple PDFs Using Ai")
    user_question = st.text_input("ASK QUESTION TO YOUR PDF Files")
    
    if user_question:
        user_input(user_question)

    with st.sidebar:
        st.title("Menu : ")  
        pdf_docs = st.file_uploader("Upload your PDF files and Click on the submit button", accept_multiple_files=True)
        if st.button("Submit & Process"):
            with st.spinner("Processing..."):
                raw_text = get_pdf_text(pdf_docs)
                text_chunks = get_text_chunks(raw_text)
                get_vector_store(text_chunks)
                st.success("Done")

if __name__ == "__main__":
    main()

