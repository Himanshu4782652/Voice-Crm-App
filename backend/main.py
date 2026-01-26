import os
import json
import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# --- GROQ (OPEN SOURCE MODELS) ---
from groq import Groq

load_dotenv()
app = FastAPI()

# --- CONFIGURATION ---
# Paste your Groq key here directly or in .env
GROQ_API_KEY = os.getenv("GROQ_API_KEY") 
client = Groq(api_key=GROQ_API_KEY)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

interactions_db = []

# --- OPEN SOURCE PROCESSING (WHISPER + GEMMA/LLAMA) ---
async def process_with_opensource(audio_file_path):
    try:
        # 1. Transcribe Audio using Open Source Whisper Large V3
        with open(audio_file_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(audio_file_path, file.read()),
                model="whisper-large-v3",
                response_format="text"
            )
        
        # 2. Extract JSON using Open Source Llama 3 (or Gemma 2)
        prompt = f"""
        Extract the following fields from this transcript into a JSON object:
        - full_name
        - phone (digits only)
        - address
        - city
        - locality
        - summary (short interaction summary)
        
        Transcript: "{transcription}"
        
        Respond ONLY with valid JSON. No markdown tags.
        """
        
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",  # <-- NEW UPGRADED MODEL
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        data = json.loads(chat_completion.choices[0].message.content)
        
        result = {
            "customer": {
                "full_name": data.get("full_name", ""),
                "phone": data.get("phone", ""),
                "address": data.get("address", ""),
                "city": data.get("city", ""),
                "locality": data.get("locality", "")
            },
            "interaction": {
                "summary": data.get("summary", ""),
                "created_at": datetime.datetime.now().isoformat()
            }
        }
        return transcription, result
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise e

# --- API ENDPOINTS ---

@app.post("/process-audio")
async def process_audio(file: UploadFile = File(...)):
    temp_filename = f"temp_{file.filename}"
    try:
        with open(temp_filename, "wb") as buffer:
            buffer.write(await file.read())

        # Process with Open Source Models
        transcribed_text, structured_data = await process_with_opensource(temp_filename)

        record = {
            "id": len(interactions_db) + 1,
            "text": transcribed_text,
            "data": structured_data,
            "timestamp": datetime.datetime.now().isoformat()
        }
        interactions_db.append(record)

        return {
            "status": "success",
            "transcription": transcribed_text,
            "extracted_data": structured_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

@app.get("/dashboard-data")
def get_dashboard_data():
    return interactions_db