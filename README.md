Here is the corrected, professionally structured version of your `README.md`. I have fixed the formatting errors (like missing code block closures) and removed the "Push Code to GitHub" instructions, as those are for you, not for the people reading your repository.

You can copy and paste this directly into your `README.md` file.

```markdown
# Voice-to-Text CRM Assistant (React PWA + Python Backend)

A voice-first Progressive Web Application (PWA) that records customer interactions, transcribes English speech to text, and extracts structured CRM data (JSON) using AI.

**Live Demo:** [https://frontend-gules-nine-95.vercel.app](https://frontend-gules-nine-95.vercel.app)  
**APK Download:** https://drive.google.com/file/d/1Tb_PhjlBCRC40PEJBfHt2d6LDEaeaAhe/view?usp=sharing [Available in GitHub Releases]

## 🚀 Key Features
- **Voice Recording:** Browser-based audio capture (Mobile & Desktop).
- **AI Transcription:** Converts speech to text using OpenAI Whisper.
- **Data Extraction:** Extracts structured fields (Name, Phone, Address, Summary) into JSON.
- **Android APK:** Wrapped as a Trusted Web Activity (TWA) using Bubblewrap (No React Native used).
- **Evaluation Dashboard:** Verifies extraction accuracy with Human-in-the-Loop (HITL) support.

## 🛠 Tech Stack
- **Frontend:** React, Vite, Tailwind CSS.
- **Backend:** Python FastAPI, Uvicorn.
- **PWA/Mobile:** Vite PWA Plugin, Google Bubblewrap (CLI).
- **Deployment:** Vercel (Frontend), Ngrok (Backend Tunneling).

## 📂 Project Structure
```text
voice-crm-app/
├── backend/            # FastAPI Server (Transcription & Extraction logic)
├── frontend/           # React PWA (UI & Recording logic)
├── mobile-build/       # Android Project & Generated APK
└── README.md

```

## 🔧 How to Run Locally

### 1. Backend Setup

The backend requires Python 3.8+ and an OpenAI API Key.

```bash
cd backend
python -m venv venv

# Activate venv:
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

pip install fastapi uvicorn python-multipart openai python-dotenv

# Run the server
uvicorn main:app --reload

```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev

```

## 📱 Generating the APK

The Android APK was generated using Google's Bubblewrap CLI to wrap the PWA.

```bash
cd mobile-build
npx @bubblewrap/cli build

```

```
