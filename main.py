# import os
# import google.generativeai as genai
# from fastapi import FastAPI, HTTPException, UploadFile, File, Form
# from dotenv import load_dotenv
# from fastapi.middleware.cors import CORSMiddleware
# from typing import Optional
# import sqlite3
# import json

# # 1. Setup & Config
# load_dotenv()
# genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# # 2. Define the Socratic Engine
# # We use gemini-flash-latest for speed and the best free tier
# model = genai.GenerativeModel(
#     model_name="gemini-flash-latest",
#     system_instruction=(
#         "You are 'Scientia', a Socratic Science Tutor for children. "
#         "Your mission is to guide students to discovery through questions, not answers.\n\n"
#         "CORE RULES:\n"
#         "1. NEVER give the answer directly. If they ask 'What is gravity?', ask what they feel when they jump.\n"
#         "2. LANGUAGE BRIDGE: If the session is in Dari or Turkish, and the student uses or asks about "
#         "a scientific term, explain it in their language but ALWAYS include the English term (e.g., 'Photosynthesis') "
#         "so they build an international scientific vocabulary.\n"
#         "3. VISION RULE: If the student uploads an image, analyze it. Ask a question about a specific part "
#         "of the image to guide them. (e.g., if it's a diagram of a cell, ask 'What do you think that green part does?').\n"
#         "4. ADAPTIVE LEVEL: Use simple analogies (layman terms) initially. Increase complexity only as the student proves understanding.\n"
#         "5. TONE: Encouraging, patient, and curious."
#     )
# )

# app = FastAPI()

# # 3. Enable CORS for Frontend communication
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# --- ADDED: DATABASE LOGIC ---
# DB_PATH = "tutor_sessions.db"

# def init_db():
#     conn = sqlite3.connect(DB_PATH)
#     c = conn.cursor()
#     c.execute('''CREATE TABLE IF NOT EXISTS sessions 
#                  (user_id TEXT PRIMARY KEY, history TEXT)''')
#     conn.commit()
#     conn.close()

# init_db()

# def get_db_history(user_id: str):
#     conn = sqlite3.connect(DB_PATH)
#     c = conn.cursor()
#     c.execute("SELECT history FROM sessions WHERE user_id=?", (user_id,))
#     row = c.fetchone()
#     conn.close()
#     return json.loads(row[0]) if row else []

# def save_db_history(user_id: str, history):
#     # Convert Gemini objects to simple dicts for JSON storage
#     serializable = []
#     for content in history:
#         serializable.append({
#             "role": content.role,
#             "parts": [{"text": p.text} for p in content.parts if hasattr(p, 'text')]
#         })
#     conn = sqlite3.connect(DB_PATH)
#     c = conn.cursor()
#     c.execute("INSERT OR REPLACE INTO sessions (user_id, history) VALUES (?, ?)",
#               (user_id, json.dumps(serializable)))
#     conn.commit()
#     conn.close()
# # ------------------------------

# # 4. Session Memory (In-memory for Demo)
# # sessions = {}

# # --- ADDED: HISTORY ENDPOINT ---
# @app.get("/history/{user_id}")
# async def get_chat_history(user_id: str):
#     history = get_db_history(user_id)
#     # Clean up for frontend: only send relevant text
#     messages = []
#     for entry in history:
#         role = "ai" if entry['role'] == "model" else "user"
#         # Avoid sending the hidden system priming messages to the UI
#         if "The student wants to learn in" in entry['parts'][0]['text']: continue
#         messages.append({"role": role, "text": entry['parts'][0]['text']})
#     return {"history": messages}

# # class ChatRequest(BaseModel):
# #     user_id: str
# #     message: str
# #     language: str

# @app.post("/ask")
# # async def ask_tutor(request: ChatRequest):
# async def ask_tutor(
#     user_id: str = Form(...),
#     message: str = Form(...),
#     language: str = Form(...),
#     file: Optional[UploadFile] = File(None) 
# ):
    
#     # --- CHANGED: Load from DB instead of dict ---
#     history = get_db_history(user_id)
#     chat_session = model.start_chat(history=history)
    
#     # Initialize if history is empty
#     if not history:
#         init_prompt = (
#             f"The student wants to learn in {language}. "
#             f"Please welcome them in {language} and ask what science topic they want to explore today."
#         )
#         await chat_session.send_message_async(init_prompt)
    
#     # # Initialize a new session if it doesn't exist
#     # if user_id not in sessions:
#     #     sessions[user_id] = model.start_chat(history=[])
#     #     # Hidden first message to set the language context without alerting the student
#     #     init_prompt = (
#     #         f"The student wants to learn in {language}. "
#     #         f"Please welcome them in {language} and ask what science topic they want to explore today."
#     #     )
#     #     sessions[user_id].send_message(init_prompt)

#     content_parts = [message]

#     if file:
#         try:
#             image_data = await file.read()
#             content_parts.append({
#                 "mime_type": file.content_type,
#                 "data": image_data
#             })
#         except Exception as e:
#             raise HTTPException(status_code=400, detail="Could not read image file.")

#     try:
#         # chat_session = sessions[user_id]
#         # response = chat_session.send_message(content_parts)
#         # --- CHANGED: Added await/async for better performance ---
#         response = await chat_session.send_message_async(content_parts)
        
#         # --- ADDED: Save updated history to DB ---
#         save_db_history(user_id, chat_session.history)
#         return {"tutor_response": response.text}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")
    
# Run: uvicorn main:app --reload

import os
import google.generativeai as genai
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
# --- ADDED: Database & JSON support ---
import sqlite3
import json
# --------------------------------------

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = genai.GenerativeModel(
    model_name="gemini-flash-latest",
    system_instruction=(
        "You are 'Scientia', a Socratic Science Tutor for children. "
        "Your mission is to guide students to discovery through questions, not answers.\n\n"
        "CORE RULES:\n"
        "1. NEVER give the answer directly. If they ask 'What is gravity?', ask what they feel when they jump.\n"
        "2. LANGUAGE BRIDGE: If the session is in Dari or Turkish, and the student uses or asks about "
        "a scientific term, explain it in their language but ALWAYS include the English term (e.g., 'Photosynthesis') "
        "so they build an international scientific vocabulary.\n"
        "3. VISION RULE: If the student uploads an image, analyze it. Ask a question about a specific part "
        "of the image to guide them. (e.g., if it's a diagram of a cell, ask 'What do you think that green part does?').\n"
        "4. ADAPTIVE LEVEL: Use simple analogies (layman terms) initially. Increase complexity only as the student proves understanding.\n"
        "5. TONE: Encouraging, patient, and curious."
)
)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ADDED: DATABASE LOGIC ---
DB_PATH = "tutor_sessions.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sessions 
                 (user_id TEXT PRIMARY KEY, history TEXT)''')
    conn.commit()
    conn.close()

init_db()

def get_db_history(user_id: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT history FROM sessions WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return json.loads(row[0]) if row else []

def save_db_history(user_id: str, history):
    # Convert Gemini objects to simple dicts for JSON storage
    serializable = []
    for content in history:
        serializable.append({
            "role": content.role,
            "parts": [{"text": p.text} for p in content.parts if hasattr(p, 'text')]
        })
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO sessions (user_id, history) VALUES (?, ?)",
              (user_id, json.dumps(serializable)))
    conn.commit()
    conn.close()
# ------------------------------

# REMOVED: sessions = {} (We now use the DB)

# --- ADDED: HISTORY ENDPOINT ---
@app.get("/history/{user_id}")
async def get_chat_history(user_id: str):
    history = get_db_history(user_id)
    # Clean up for frontend: only send relevant text
    messages = []
    for entry in history:
        role = "ai" if entry['role'] == "model" else "user"
        # Avoid sending the hidden system priming messages to the UI
        if "The student wants to learn in" in entry['parts'][0]['text']: continue
        messages.append({"role": role, "text": entry['parts'][0]['text']})
    return {"history": messages}
# ------------------------------

@app.post("/ask")
async def ask_tutor(
    user_id: str = Form(...),
    message: str = Form(...),
    language: str = Form(...),
    file: Optional[UploadFile] = File(None) 
):
    # --- CHANGED: Load from DB instead of dict ---
    history = get_db_history(user_id)
    chat_session = model.start_chat(history=history)
    
    # Initialize if history is empty
    if not history:
        init_prompt = (
            f"The student wants to learn in {language}. "
            f"Please welcome them in {language} and ask what science topic they want to explore today."
        )
        await chat_session.send_message_async(init_prompt)
    # ---------------------------------------------

    content_parts = [message]

    if file:
        try:
            image_data = await file.read()
            content_parts.append({
                "mime_type": file.content_type,
                "data": image_data
            })
        except Exception as e:
            raise HTTPException(status_code=400, detail="Could not read image file.")

    try:
        # --- CHANGED: Added await/async for better performance ---
        response = await chat_session.send_message_async(content_parts)
        
        # --- ADDED: Save updated history to DB ---
        save_db_history(user_id, chat_session.history)
        
        return {"tutor_response": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")

from fastapi.responses import FileResponse

@app.get("/")
async def serve_home():
    return FileResponse("index.html")

# Run: uvicorn main:app --reload