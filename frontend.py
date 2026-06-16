import streamlit as st
import re
import uuid
from basic_chatbot import chatbot, retrieve_all_threads, llm
from langchain_core.messages import HumanMessage, SystemMessage
from rag_engine import process_uploaded_file, query_rag, is_rag_ready
from audiorecorder import audiorecorder
from voice_utils import text_to_speech, speech_to_text

def generate_thread_id():
    return str(uuid.uuid4())

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    st.session_state['chat_names'][thread_id] = "New Chat"
    add_thread(thread_id)
    st.session_state['message_history'] = []

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def load_conversation(thread_id):
    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}}).values
    return state.get('messages', [])

def delete_thread(thread_id):
    from basic_chatbot import delete_thread_from_db
    delete_thread_from_db(thread_id)
    st.session_state['chat_threads'].remove(thread_id)
    st.session_state['chat_names'].pop(thread_id, None)
    if st.session_state['thread_id'] == thread_id:
        st.session_state['thread_id'] = generate_thread_id()
        st.session_state['message_history'] = []

def render_message(content, role=None, msg_index=None):
    if "IMAGE_FILE:" in content:
        path = re.search(r'IMAGE_FILE:(\S+\.png)', content)
        if path:
            st.image(path.group(1))
        text_only = re.sub(r'IMAGE_FILE:\S+\.png', '', content).strip()
        if text_only:
            st.write(text_only)
    elif "IMAGE:" in content:
        urls = re.findall(r'IMAGE:(https://image\.pollinations\.ai/prompt/[^\s\n]+)', content)
        for url in urls:
            st.image(url)
        text_only = re.sub(r'IMAGE:https://[^\s\n]+', '', content).strip()
        if text_only:
            st.write(text_only)
    else:
        st.markdown(content)
        if role == 'assistant' and msg_index is not None:
            if st.button("🔊", key=f"tts_{msg_index}"):
                audio_bytes = text_to_speech(content)
                st.audio(audio_bytes, format="audio/mp3", autoplay=True)

def stream_response(user_input, config):
    for message_chunk, metadata in chatbot.stream(
        {'messages': [HumanMessage(content=user_input)]},
        config=config, stream_mode='messages'
    ):
        if message_chunk.content and metadata.get('langgraph_node') == 'chat_node':
            yield message_chunk.content

# session state init
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []
if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()
if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrieve_all_threads()
if 'chat_names' not in st.session_state:
    st.session_state['chat_names'] = {}
    for i in retrieve_all_threads():
        msg = load_conversation(i)
        if msg:
            chat_name_1 = msg[0].content[:25]
        else:
            chat_name_1 = "New Chat"
        st.session_state['chat_names'][i] = chat_name_1
if 'voice_input' not in st.session_state:
    st.session_state['voice_input'] = ""
if 'last_recognized' not in st.session_state:
    st.session_state['last_recognized'] = ""

add_thread(st.session_state['thread_id'])

# welcome screen
if not st.session_state['message_history']:
    st.markdown("""
    <div style='text-align: center; padding: 60px 20px;'>
        <div style='font-size: 4em; animation: pulse 2s infinite;'>🤖</div>
        <h1 style='
            font-size: 3.2em;
            font-weight: 900;
            margin: 15px 0 5px 0;
            background: linear-gradient(135deg, #a78bfa, #60a5fa, #f472b6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        '>AXON</h1>
        <p style='color: #6b7280; font-size: 1em; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 30px;'>
            Your Multimodal AI Assistant
        </p>
        <div style='
            display: flex;
            justify-content: center;
            gap: 15px;
            flex-wrap: wrap;
            margin: 30px 0;
        '>
            <span style='background: #1e1b4b; color: #a78bfa; padding: 8px 18px; border-radius: 20px; font-size: 0.85em;'>💬 Chat</span>
            <span style='background: #1e1b4b; color: #60a5fa; padding: 8px 18px; border-radius: 20px; font-size: 0.85em;'>🎙️ Voice</span>
            <span style='background: #1e1b4b; color: #f472b6; padding: 8px 18px; border-radius: 20px; font-size: 0.85em;'>🖼️ Images</span>
            <span style='background: #1e1b4b; color: #34d399; padding: 8px 18px; border-radius: 20px; font-size: 0.85em;'>📄 Documents</span>
        </div>
        <p style='color: #4b5563; font-size: 1em; margin-top: 20px; line-height: 1.8;'>
            Ask me anything, upload a PDF, generate images,<br>or just talk to me 🤍
        </p>
    </div>
    <style>
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }
    </style>
""", unsafe_allow_html=True)
# sidebar
st.sidebar.title('AXON')

st.sidebar.markdown("---")
st.sidebar.subheader("📄 Upload Document")
uploaded_file = st.sidebar.file_uploader("Upload PDF", type=['pdf'])
if uploaded_file:
    if st.session_state.get('last_uploaded') != uploaded_file.name:
        with st.spinner("Processing PDF..."):
            msg = process_uploaded_file(uploaded_file)
            st.session_state['last_uploaded'] = uploaded_file.name
            st.sidebar.success(msg)
    else:
        st.sidebar.success(f"✅ {uploaded_file.name} ready")

st.sidebar.markdown("---")
if st.sidebar.button('New chat'):
    reset_chat()

st.sidebar.text('my conversations')
for i in st.session_state['chat_threads'][::-1]:
    chat_name = st.session_state['chat_names'].get(i, "New Chat")
    col1, col2 = st.sidebar.columns([4, 1])
    with col1:
        if st.button(chat_name, key=f"btn_{i}"):
            st.session_state['thread_id'] = i
            messages = load_conversation(i)
            temp_messages = []
            for msg in messages:
                role = 'user' if isinstance(msg, HumanMessage) else 'assistant'
                temp_messages.append({'role': role, 'content': msg.content})
            st.session_state['message_history'] = temp_messages
    with col2:
        if st.button("🗑️", key=f"del_{i}"):
            delete_thread(i)
            st.rerun()

# config
config = {
    "configurable": {"thread_id": st.session_state["thread_id"]},
    "metadata": {"thread_id": st.session_state["thread_id"]},
    "run_name": "chat_turn",
}

# chat history display
for idx, message in enumerate(st.session_state['message_history']):
    if not message['content']:
        continue
    with st.chat_message(message['role']):
        render_message(message['content'], role=message['role'], msg_index=idx)

IMAGE_KEYWORDS = ["generate image", "create image", "draw", "make image", "generate a picture", "create a picture", "generate an image"]

# STT mic button
st.markdown("🎤 **Record voice input:**")
audio = audiorecorder("🎤 Click to record", "⏹ Stop recording")

if len(audio) > 0:
    audio_bytes = audio.export().read()
    recognized = speech_to_text(audio_bytes)
    if recognized and recognized != st.session_state['last_recognized']:
        st.session_state['voice_input'] = recognized
        st.session_state['last_recognized'] = recognized
        st.rerun()

user_input = st.chat_input('Type something here')

if not user_input and st.session_state['voice_input']:
    user_input = st.session_state['voice_input']
    st.session_state['voice_input'] = ""

if user_input:
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.markdown(user_input)

    if len(st.session_state['message_history']) == 1:
        st.session_state['chat_names'][st.session_state['thread_id']] = user_input[:25]

    if any(keyword in user_input.lower() for keyword in IMAGE_KEYWORDS):
        from tools.image_tool import generate_image
        with st.chat_message('assistant'):
            with st.spinner("Generating image..."):
                result = generate_image.invoke(user_input)
                path = re.search(r'IMAGE_FILE:(\S+\.png)', result)
                if path:
                    st.image(path.group(1))
                ai_msg = result
    else:
        with st.chat_message('assistant'):
            try:
                if is_rag_ready():
                    with st.spinner("Searching document..."):
                        ai_msg = query_rag(user_input, llm)
                    st.markdown(ai_msg)
                else:
                    ai_msg = st.write_stream(stream_response(user_input, config))
            except Exception as e:
                if "429" in str(e):
                    ai_msg = "⚠️ Rate limit reached. Please wait and try again."
                    st.warning(ai_msg)
                else:
                    ai_msg = f"⚠️ Error: {str(e)[:100]}"
                    st.error(ai_msg)

    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_msg})
    if len(st.session_state['message_history']) == 2:
        thread_id = st.session_state['thread_id']
        try:
            name_response = llm.invoke([
                SystemMessage(content="Give a very short 3 word chat title only. No punctuation. No quotes."),
                HumanMessage(content=f"Title for: {user_input[:50]}")
            ])
            st.session_state['chat_names'][thread_id] = name_response.content.strip()[:25]
        except:
            st.session_state['chat_names'][thread_id] = user_input[:25]
        st.rerun()