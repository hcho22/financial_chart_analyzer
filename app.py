import streamlit as st
from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.docstore.document import Document
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain

from htmlTemplates import css, bot_template, user_template
from gpt4o_technical_analyst import analyze_chart
import os


def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks

def get_vectorstore(text_chunks):
    embeddings = OpenAIEmbeddings()
    documents = [Document(page_content=chunk) for chunk in text_chunks]
    persist_directory = "vector_db"
    vectorstore = Chroma.from_documents(documents=documents, embedding=embeddings, persist_directory = persist_directory)
    
    return vectorstore

def get_conversation_chain(vectorstore):
    llm = ChatOpenAI()
    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm, 
        retriever = vectorstore.as_retriever(),
        memory=memory
    )
    return conversation_chain

def handle_userinput(user_question):
    response = st.session_state.conversation({'question': user_question})
    #st.write(response)
    st.session_state.chat_history = response['chat_history']

    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)


def main():
    st.set_page_config(page_title="ML Trading Bot", page_icon=":money_with_wings:")
    st.write(css, unsafe_allow_html=True)

    # initialize the session state if haven't
    if "conversation" not in st.session_state:
        st.session_state.conversation = None

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    st.header("Chat with ML Chart Analyzer :money_with_wings:")
    
    st.subheader("Your documents")
    file = st.file_uploader(
        "Upload your screenshot and click 'Analyze'")
    
    if file is not None:
        file_details = {"FileName":file.name, "FileType":file.type}
        file_path = os.path.join(file.name)
        with open(file_path,"wb") as f:
            f.write(file.getbuffer())
    
    if st.button("Analyze"):
        with st.spinner("Processing"):
            analysis = analyze_chart(file_path)
            st.write(analysis)
            #st.session_state.chat_history.append({"content": analysis})

            text_chunks = get_text_chunks(analysis)
            vectorstore = get_vectorstore(text_chunks)
            
            st.session_state.conversation = get_conversation_chain(vectorstore)

    user_question = st.text_input("Ask a question about your analysis:")
    if user_question:
        handle_userinput(user_question)

if __name__ == '__main__':
    main()