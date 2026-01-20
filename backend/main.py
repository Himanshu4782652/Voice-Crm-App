import os
import json
import datetime
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# --- CONFIGURATION ---
# Set to True to save money/time during dev. Set False to use real OpenAI API.
USE_MOCK_AI = True 
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Allow frontend to communicate with backend (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATABASE (Simple In-Memory List for Demo) ---
# In a real app, this would be SQLite or PostgreSQL
interactions_db = []

# --- DATA MODELS (JSON STRUCTURE) ---
class CustomerDetails(BaseModel):
    full_name: str
    phone: str
    address: str
    city: str
    locality: str

class InteractionMetadata(BaseModel):
    summary: str
    created_at: str

class CRMData(BaseModel):
    customer: CustomerDetails
    interaction: InteractionMetadata

# --- HELPER FUNCTIONS ---

def mock_transcription():
    return "I spoke with customer Amit Verma today. His phone number is nine nine eight eight seven seven six six five five. He stays at 45 Park Street, Salt Lake, Kolkata. We discussed the demo and next steps."

def mock_extraction():
    return {
        "customer": {
            "full_name": "Amit Verma",
            "phone": "9988776655",
            "address": "45 Park Street",
            "city": "Kolkata",
            "locality": "Salt Lake"
        },
        "interaction": {
            "summary": "Discussed demo and next steps",
            "created_at": datetime.datetime.now().isoformat()
        }
    }

async def process_with_openai(audio_file_path):
    """
    Uses OpenAI Whisper for STT and GPT-4o-mini for Extraction.
    """
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)

    # 1. Transcribe (Speech to Text)
    with open(audio_file_path, "rb") as audio:
        transcription = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio
        )
    text = transcription.text

    # 2. Extract (Text to JSON)
    prompt = f"""
    Extract the following fields from the text below into a JSON format:
    - full_name
    - phone (digits only)
    - address
    - city
    - locality
    - summary (short interaction summary)
    
    Text: "{text}"
    
    Return ONLY raw JSON. No markdown formatting.
    """
    
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    
    json_str = completion.choices[0].message.content.strip()
    # Clean up potential markdown code blocks if the LLM adds them
    if json_str.startswith("```json"):
        json_str = json_str[7:-3]
        
    data = json.loads(json_str)
    
    # Add timestamp
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
    return text, result

# --- API ENDPOINTS ---

@app.get("/")
def home():
    return {"message": "Voice CRM Backend is Running"}

@app.post("/process-audio")
async def process_audio(file: UploadFile = File(...)):
    """
    Receives audio file -> Transcribes -> Extracts Data -> Returns JSON
    """
    try:
        # Save temp file
        temp_filename = f"temp_{file.filename}"
        with open(temp_filename, "wb") as buffer:
            buffer.write(await file.read())

        if USE_MOCK_AI:
            # Simulate processing delay
            import time
            time.sleep(1)
            transcribed_text = mock_transcription()
            structured_data = mock_extraction()
        else:
            if not OPENAI_API_KEY:
                raise HTTPException(status_code=500, detail="OpenAI API Key not set")
            transcribed_text, structured_data = await process_with_openai(temp_filename)

        # Cleanup temp file
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

        # Save to local "database" for the dashboard
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
        return HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard-data")
def get_dashboard_data():
    """
    Returns all past interactions for the Evaluation Dashboard
    """
    return interactions_db