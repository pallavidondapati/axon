import streamlit as st
from basic_chatbot import chatbot
from langchain_core.messages import HumanMessage
st.title("AgentX")
config = {'configurable': {'thread_id': 'thread-1'}}

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input('Type something here')
if user_input:
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)
    with st.chat_message('assistant'):
        def stream_response():
            for message_chunk,metadata in chatbot.stream({'messages':[HumanMessage(content=user_input)]},config=config,stream_mode='messages'):
                if message_chunk.content:
                    yield message_chunk.content
        
        ai_msg = st.write_stream(stream_response())
    
    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_msg})