import os
import json
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

@app.post("/analyze-audio")
async def analyze_audio(audio_file: UploadFile = File(...)):
    try:
        audio_bytes = await audio_file.read()
        
        # DYNAMIC FILENAME FIX: Now it accepts .mp4 or .webm properly from frontend
        transcription = client.audio.transcriptions.create(
            file=(audio_file.filename, audio_bytes),
            model="whisper-large-v3",
            response_format="json",
            language="en"
        )
        transcript_text = transcription.text

        system_prompt = """You are a cybersecurity AI. Analyze this call transcript. 
        If the transcript is empty, extremely short, or contains just background noise/silence, output a safe baseline JSON with Threat Level 0 and Type CLEAN.
        Otherwise, analyze the threat and output JSON matching exactly this schema:
        {
            "threat_level": int (0-100), 
            "scam_type": str, 
            "voice_clone_probability": int (0-100), 
            "psychology": str, 
            "deepfake_indicators": str, 
            "flagged_entities": [str], 
            "leaked_info": str, 
            "custom_mitigation": [str]
        }"""

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcript_text if transcript_text else "[Silence]"}
            ],
            model="llama3-70b-8192",
            response_format={"type": "json_object"}
        )

        try:
            analysis = json.loads(chat_completion.choices[0].message.content)
        except:
            analysis = {
                "threat_level": 50,
                "scam_type": "UNKNOWN",
                "voice_clone_probability": 0,
                "psychology": "Error parsing AI response.",
                "deepfake_indicators": "Unknown",
                "flagged_entities": [],
                "leaked_info": "Unknown",
                "custom_mitigation": ["Maintain caution."]
            }

        return {
            "transcript": transcript_text if transcript_text else "No speech detected.",
            "analysis": analysis
        }
    except Exception as e:
        return {"error": str(e)}
