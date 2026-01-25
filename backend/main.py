import os
import json
import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# --- NEW SDK IMPORT ---
from google import genai

load_dotenv()
app = FastAPI()

# --- CONFIGURATION ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 
client = genai.Client(api_key=GEMINI_API_KEY)

# Allow frontend to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

interactions_db = []

# --- GEMINI PROCESSING (NEW SDK) ---
async def process_with_gemini(audio_file_path):
    try:
        # 1. Upload the file using the new SDK
        audio_file = client.files.upload(file=audio_file_path)
        
        prompt = """
        Listen to this audio. 
        1. Transcribe the speech exactly.
        2. Extract the following fields into a JSON object:
           - full_name
           - phone (digits only)
           - address
           - city
           - locality
           - summary (short interaction summary)
        
        Output format:
        |TRANSCRIPTION_START|
        (Insert transcription here)
        |TRANSCRIPTION_END|
        |JSON_START|
        (Insert valid JSON here)
        |JSON_END|
        """
        
        # 2. Generate content using the new SDK syntax
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt, audio_file]
        )
        text_response = response.text
        
        # Parse the custom format
        transcription = text_response.split("|TRANSCRIPTION_START|")[1].split("|TRANSCRIPTION_END|")[0].strip()
        json_str = text_response.split("|JSON_START|")[1].split("|JSON_END|")[0].strip()
        
        if json_str.startswith("```json"):
            json_str = json_str[7:-3]
            
        data = json.loads(json_str)
        
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
        print(f"Gemini Error: {str(e)}")
        raise e

# --- API ENDPOINTS ---

@app.get("/")
def home():
    return {"message": "Voice CRM Backend (Upgraded SDK) is Running"}

@app.post("/process-audio")
async def process_audio(file: UploadFile = File(...)):
    temp_filename = f"temp_{file.filename}"
    try:
        with open(temp_filename, "wb") as buffer:
            buffer.write(await file.read())

        transcribed_text, structured_data = await process_with_gemini(temp_filename)

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