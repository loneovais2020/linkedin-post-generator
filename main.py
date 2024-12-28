import streamlit as st
from groq import Groq
import random
import os
from dotenv import load_dotenv
from langchain.chains import ConversationChain, LLMChain
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.messages import SystemMessage
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain_community.document_loaders import WebBaseLoader



SYSTEM_PROMPT = """Act as a professional Linkedin Post writer capable of writing compelling linkedin posts with hastags at the end of the post. You should use the following format:

<compelling title>
<post content.>
<perspective that is related to the post>
<motivation for discussion >
<hashtags for the increasing popularity of the post>

Make sure the post has enough content to entice the reader to have discussions through the post's comments section.
"""

model = 'llama3-8b-8192'


def get_web_context(web_url):
    web_context = ""
    loader = WebBaseLoader(web_url)
    docs = loader.load()
    for doc in docs:
        web_context += doc.page_content

    return web_context



def main():
    """
    This function is the main entry point of the application. It sets up the Groq client, the Streamlit interface, and handles the chat interaction.
    """
    
    load_dotenv()

    # The title and greeting message of the Streamlit application
    st.title("OTL's LinkedIn Post Writer")
    st.write("Hello! I'm OTL's LinkedIn Post Writer. I can help you write compelling LinkedIn posts.")
    with st.sidebar:
        # Add customization options to the sidebar
        st.title('Customization')
    

        use_web_source = st.toggle("Use Websource")
        if use_web_source:
            web_url = st.text_input("Web URL:")
        else:
            content_length = st.number_input('Content length:', min_value=100, max_value=500, value=150, step=50)
        conversational_memory_length = st.slider('Conversational memory length:', 0, 10, value = 5)

    memory = ConversationBufferWindowMemory(k=conversational_memory_length, memory_key="chat_history", return_messages=True)


    if not use_web_source:
        user_query = st.text_input("Enter the topic for the post:")

    generate_post = st.button("Generate Post")

    # session state variable
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history=[]
    else:
        for message in st.session_state.chat_history:
            memory.save_context(
                {'input':message['human']},
                {'output':message['AI']}
                )


    # Initialize Groq Langchain chat object and conversation
    groq_chat = ChatGroq(
            # groq_api_key=groq_api_key, 
            model_name=model
    )


    # If the user has generate_posted a question,
    if generate_post:

        # Construct a chat prompt template using various components
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(
                    content=SYSTEM_PROMPT
                ),  # This is the persistent system prompt that is always included at the start of the chat.

                MessagesPlaceholder(
                    variable_name="chat_history"
                ),  # This placeholder will be replaced by the actual chat history during the conversation. It helps in maintaining context.

                HumanMessagePromptTemplate.from_template(
                    "{human_input}"
                ),  # This template is where the user's current input will be injected into the prompt.
            ]
        )

        # Create a conversation chain using the LangChain LLM (Language Learning Model)
        conversation = LLMChain(
            llm=groq_chat,  # The Groq LangChain chat object initialized earlier.
            prompt=prompt,  # The constructed prompt template.
            verbose=True,   # Enables verbose output, which can be useful for debugging.
            memory=memory,  # The conversational memory object that stores and manages the conversation history.
        )

        if use_web_source:
            web_context = get_web_context(web_url)
            # print("----------------------------------")
            # print(web_context)
            # print("----------------------------------")

            user_query  = f"""
Write a Linkedin post using the below content. You have to summarize the content and write a compelling Linkedin post making sure all the important information is retained in the post. The content to use as reference is as follows:

{web_context}
"
"""
        else:
            user_query = f"""{user_query} .The content length should be around "+{str(content_length)} words."""

        response = conversation.predict(human_input=user_query)


#         response = """
# The Future of Human-Agent Collaboration: Unlocking the Power of LLMs and Vision Models

# Imagine a world where AI-powered agents, fueled by Large Language Models (LLMs) and Vision Models, collaborate seamlessly with humans to transform industries and revolutionize the way we live and work.

# """
        message = {'human':user_query,'AI':response}
        st.session_state.chat_history.append(message)
        st.markdown(response, unsafe_allow_html=True)



if __name__ == "__main__":
    main()