# MYagenT — Multimodal Agentic AI Assistant

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)
![LangGraph](https://img.shields.io/badge/LangGraph-Agentic-purple?style=for-the-badge)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-red?style=for-the-badge&logo=streamlit)
![Groq](https://img.shields.io/badge/Groq-LLaMA_3.3_70B-orange?style=for-the-badge)
![FAISS](https://img.shields.io/badge/FAISS-Vector_Search-green?style=for-the-badge)

**A production-grade agentic AI assistant with multimodal capabilities — chat, voice, image generation, and document Q&A.**

</div>

---

## What is MYagenT?

MYagenT is not just a chatbot — it is a fully agentic AI system built on LangGraph. The LLM autonomously decides whether to answer directly, search the web, generate an image, or query an uploaded document. It maintains persistent memory across sessions, processes voice input and output, and is architected with production-grade patterns including async execution, multi-threading, distributed caching, and persistent vector storage.

---

## Features

| Feature | Details |
|---|---|
| 💬 Agentic Chat | LLaMA 3.3 70B via Groq with autonomous tool selection |
| 🎙️ Voice Input (STT) | Records audio → converts to WAV via pydub/ffmpeg → transcribes via Google Speech Recognition |
| 🔊 Voice Output (TTS) | gTTS converts assistant responses to audio, playable per message |
| 🖼️ Image Generation | HuggingFace Stable Diffusion via Inference API |
| 📄 Document Q&A (RAG) | Upload PDF → FAISS vector search → context-aware answers |
| 🧠 Persistent Memory | SQLite-backed LangGraph checkpointer stores full conversation history |
| 🗂️ Multi-thread Management | Create, switch, rename, and delete conversations |

---

## Architecture

```
User Input (Text / Voice)
        │
        ▼
┌─────────────────────┐
│   Streamlit Frontend │  ← frontend.py
│  STT / TTS / UI     │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   LangGraph Agent   │  ← basic_chatbot.py
│                     │
│  ┌───────────────┐  │
│  │  chat_node    │  │  ← async LLM call (ainvoke)
│  │  (async)      │  │
│  └──────┬────────┘  │
│         │            │
│  tools_condition     │  ← decides: tool or respond?
│         │            │
│  ┌──────▼────────┐  │
│  │  ToolNode     │  │
│  │  - image tool │  │
│  │  - search tool│  │
│  └───────────────┘  │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   Memory Layer      │
│  SQLite + db_lock   │  ← synchronized writes
│  Redis Cache        │  ← distributed session cache
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   RAG Engine        │  ← rag_engine.py
│  PyPDFLoader        │
│  ThreadPoolExecutor │  ← multi-threaded chunking
│  FAISS (persisted)  │  ← saved to disk, loaded on startup
│  HuggingFace Embed  │
└─────────────────────┘
```

---

## Tech Stack

### Core
- **LangGraph** — agentic graph orchestration (nodes, edges, conditional routing)
- **LangChain** — LLM abstractions, tool binding, RAG chain
- **Groq API** — ultra-fast LLaMA 3.3 70B inference
- **Streamlit** — web UI with session state management

### Memory & Storage
- **SQLite** — persistent LangGraph checkpointer for conversation memory
- **FAISS** — vector similarity search for RAG, persisted to disk
- **Redis** — distributed cache layer for session thread retrieval

### Voice
- **gTTS** — Google Text-to-Speech for audio output
- **streamlit-audiorecorder** — browser mic recording
- **SpeechRecognition** — Google STT for transcription
- **pydub + ffmpeg** — audio format conversion (WebM/MP3 → WAV)

### RAG
- **PyPDFLoader** — PDF text extraction
- **RecursiveCharacterTextSplitter** — intelligent document chunking
- **HuggingFace Embeddings** — `sentence-transformers/all-MiniLM-L6-v2`

### Image Generation
- **HuggingFace Inference API** — Stable Diffusion XL

---

## Production-Grade Additions

### 1. Async Concurrency
The `chat_node` uses `ainvoke` instead of `invoke`, enabling non-blocking LLM calls:
```python
async def chat_node(state: ChatState):
    response = await llm_with_tools.ainvoke(messages)
    return {'messages': [response]}
```

### 2. Multi-threaded PDF Processing
PDF chunks are processed in parallel using `ThreadPoolExecutor`:
```python
with ThreadPoolExecutor(max_workers=4) as executor:
    chunks = list(executor.map(
        lambda doc: splitter.split_documents([doc]),
        documents
    ))
```

### 3. Synchronized SQLite Writes
A `threading.Lock` prevents race conditions on concurrent database writes:
```python
db_lock = Lock()

def delete_thread_from_db(thread_id):
    with db_lock:
        conn.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
        conn.commit()
```

### 4. Persistent FAISS Vectorstore
The vectorstore is saved to disk after every upload and reloaded on startup — no re-embedding needed:
```python
vectorstore.save_local(FAISS_PATH)

# on startup
FAISS.load_local(FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
```

### 5. Redis Distributed Cache
Thread list retrieval hits Redis first before querying SQLite, with automatic fallback:
```python
if REDIS_AVAILABLE:
    cached = cache.get("all_threads")
    if cached:
        return json.loads(cached)
# fallback to SQLite if Redis unavailable
```

---

## Project Structure

```
ai_agent/
├── frontend.py          # Streamlit UI, STT/TTS, chat interface
├── basic_chatbot.py     # LangGraph agent, async chat node, Redis cache, SQLite lock
├── rag_engine.py        # PDF loading, FAISS vectorstore, RAG chain
├── voice_utils.py       # gTTS text-to-speech, Google STT speech-to-text
├── tools/
│   ├── image_tool.py    # HuggingFace image generation tool
│   └── search_tool.py   # Web search tool
├── models/              # Cached HuggingFace embeddings
├── faiss_index/         # Persisted FAISS vectorstore
├── data/                # Uploaded PDF files
├── checkpoints.db       # SQLite conversation memory
└── .env                 # API keys
```

---

## Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/pallavidondapati/myagent.git
cd myagent
```

### 2. Install dependencies
```bash
pip install streamlit langchain langgraph langchain-groq langchain-community
pip install langchain-huggingface langchain-text-splitters sentence-transformers
pip install faiss-cpu torch torchvision
pip install gtts streamlit-audiorecorder SpeechRecognition pydub
pip install redis python-dotenv pypdf pdfplumber
```

### 3. Set up environment variables
Create a `.env` file:
```
GROQ_API_KEY=your_groq_api_key
HF_API_KEY=your_huggingface_api_key
```

### 4. Install ffmpeg (required for voice input)
Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.
Then set the path in `voice_utils.py`:
```python
AudioSegment.converter = r"C:\path\to\ffmpeg.exe"
```

### 5. (Optional) Start Redis for caching
```bash
redis-server
```
App works without Redis — falls back to SQLite automatically.

### 6. Run the app
```bash
streamlit run frontend.py
```

---

## How It Works

**Text Chat** → User types → LangGraph agent decides → tool call or direct LLM response → streamed back to UI

**Voice Input** → User records → pydub converts to WAV → Google STT transcribes → sent to agent as text

**Voice Output** → Click 🔊 on any assistant message → gTTS generates MP3 → plays in browser

**Image Generation** → User says "generate image of X" → agent calls image tool → HuggingFace Stable Diffusion → displayed in chat

**Document Q&A** → Upload PDF → multi-threaded chunking → FAISS embedding → user asks question → RAG retrieves context → LLM answers

---

## Resume Bullet

> Architected MYagenT — a scalable agentic AI assistant (Groq LLaMA 3.3 70B) with concurrent async tool execution, multi-threaded PDF processing (ThreadPoolExecutor), synchronized SQLite writes (threading.Lock), Redis-backed distributed session cache, and persistent FAISS vectorstore; features multimodal I/O including STT/TTS voice pipeline (gTTS, Google Speech Recognition, pydub), RAG document Q&A, and HuggingFace image generation; deployed via Streamlit

---

## Author

**Pallavi Dondapati**
B.Tech CSE, MVGR College of Engineering (2024–2028)

[![GitHub](https://img.shields.io/badge/GitHub-pallavidondapati-black?style=flat&logo=github)](https://github.com/pallavidondapati)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-pallavi--dondapati-blue?style=flat&logo=linkedin)](https://linkedin.com/in/pallavi-dondapati)
[![LeetCode](https://img.shields.io/badge/LeetCode-pallavi__dondapati-orange?style=flat&logo=leetcode)](https://leetcode.com/pallavi_dondapati)
