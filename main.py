import os
import json
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class ScamAnalysis(BaseModel):
    threat_level: int
    scam_type: str
    voice_clone_probability: int
    psychology: str
    deepfake_indicators: str
    flagged_entities: list[str]
    leaked_info: str
    custom_mitigation: list[str]

@app.post("/analyze-audio")
async def analyze_audio(audio_file: UploadFile = File(...)):
    try:
        audio_bytes = await audio_file.read()
        
        transcription = client.audio.transcriptions.create(
            file=("chunk.wav", audio_bytes),
            model="whisper-large-v3",
            response_format="json",
            language="en"
        )
        transcript_text = transcription.text

        system_prompt = """You are a top-tier cybersecurity AI. Analyze this call transcript. 
        Output JSON matching exactly this schema:
        {
            "threat_level": int (0-100), 
            "scam_type": str (Categorize strictly, e.g., Vishing, Identity Theft, Extortion, Tech Support, Clean), 
            "voice_clone_probability": int (0-100), 
            "psychology": str, 
            "deepfake_indicators": str, 
            "flagged_entities": [str], 
            "leaked_info": str (What sensitive data or clues did the victim accidentally reveal? Be specific.), 
            "custom_mitigation": [str] (Array of 3-4 highly specific, actionable steps tailored exactly to what the victim leaked and the scam type)
        }"""

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcript_text}
            ],
            model="llama3-70b-8192",
            response_format={"type": "json_object"}
        )

        analysis = json.loads(chat_completion.choices[0].message.content)

        return {
            "transcript": transcript_text,
            "analysis": analysis
        }
    except Exception as e:
        return {"error": str(e)}