import os
import sqlite3
import json
from threading import Lock
from typing import TypedDict, Annotated

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
try:
    from langgraph.checkpoint.sqlite import SqliteSaver
except ImportError:
    from langgraph.checkpoint.sqlite import SqliteSaver as SqliteSaver
from langgraph.prebuilt import ToolNode, tools_condition

from tools.weather_tool import get_weather
from tools.stock_tool import get_stock_price
from tools.calculator_tool import calculator
from tools.wikipedia_tool import wikipedia_search
from tools.news_tool import get_news
from tools.code_debugger_tool import debug_code

import redis

# ── env ───────────────────────────────────────────
load_dotenv()

try:
    import streamlit as st
    GROQ_API_KEY = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
except Exception:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_MODEL = "llama-3.3-70b-versatile"

# ── Redis cache (Distributed Systems) ────────────
try:
    cache = redis.Redis(host='localhost', port=6379, db=0,
                        socket_connect_timeout=2)
    cache.ping()
    REDIS_AVAILABLE = True
except Exception:
    REDIS_AVAILABLE = False

# ── LLM + tools ──────────────────────────────────
llm = ChatGroq(api_key=GROQ_API_KEY, model=LLM_MODEL, streaming=True)
tools = [get_weather, get_stock_price, calculator, wikipedia_search, get_news, debug_code]
llm_with_tools = llm.bind_tools(tools)

# ── Graph state ───────────────────────────────────
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# ── chat node (sync — safe for Streamlit streaming) ──
def chat_node(state: ChatState):
    messages = state['messages']
    response = llm_with_tools.invoke(messages)
    return {'messages': [response]}

# ── SQLite + lock (Synchronization) ──────────────
conn = sqlite3.connect(database='chatbot.db', check_same_thread=False)
db_lock = Lock()
checkpointer = SqliteSaver(conn=conn)

# ── LangGraph ─────────────────────────────────────
tool_node = ToolNode(tools=tools)
graph = StateGraph(ChatState)
graph.add_node('chat_node', chat_node)
graph.add_node('tools', tool_node)
graph.add_edge(START, 'chat_node')
graph.add_conditional_edges('chat_node', tools_condition)
graph.add_edge('tools', 'chat_node')
chatbot = graph.compile(checkpointer=checkpointer)

# ── functions ─────────────────────────────────────
def retrieve_all_threads():
    # Distributed Systems: check Redis cache first
    if REDIS_AVAILABLE:
        cached = cache.get("all_threads")
        if cached:
            return json.loads(cached)

    # fallback to SQLite
    all_threads = set()
    for i in checkpointer.list(None):
        all_threads.add(i.config['configurable']['thread_id'])
    result = list(all_threads)

    # store in Redis cache for 5 min
    if REDIS_AVAILABLE:
        cache.set("all_threads", json.dumps(result), ex=300)

    return result

def delete_thread_from_db(thread_id):
    # Synchronization: lock on SQLite write
    with db_lock:
        conn.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
        conn.execute("DELETE FROM writes WHERE thread_id = ?", (thread_id,))
        conn.commit()

    # invalidate Redis cache
    if REDIS_AVAILABLE:
        cache.delete("all_threads")