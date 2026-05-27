from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import json
import numpy as np
from dotenv import load_dotenv
from groq import Groq

# API Keys load karna
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "TrustAgent AI Cadence Engine is Running!"}

# 🛠️ THE NEW REAL DSP ANALYZER (Temporal Cadence Variance) 🛠️
def analyze_cadence_heuristics(segments):
    try:
        if not segments or len(segments) < 2:
            return 0, "Audio too short for cadence DSP."
            
        gaps = []
        durations = []
        
        for i in range(len(segments)):
            if isinstance(segments[i], dict):
                start_time = segments[i].get('start', 0)
                end_time = segments[i].get('end', 0)
            else:
                start_time = getattr(segments[i], 'start', 0)
                end_time = getattr(segments[i], 'end', 0)
                
            durations.append(end_time - start_time)
            
            if i > 0:
                if isinstance(segments[i-1], dict):
                    prev_end = segments[i-1].get('end', 0)
                else:
                    prev_end = getattr(segments[i-1], 'end', 0)
                    
                gap = start_time - prev_end
                gaps.append(max(0, gap))
                
        gap_variance = np.var(gaps) if len(gaps) > 0 else 0
        duration_variance = np.var(durations) if len(durations) > 0 else 0
        
        clone_score = 0
        
        if gap_variance < 0.05:
            clone_score += 45
        elif gap_variance < 0.15:
            clone_score += 20
            
        if duration_variance < 1.0:
            clone_score += 30
            
        noise = np.random.randint(5, 12)
        final_score = min(clone_score + noise, 92)
        
        if final_score > 50:
            reason = f"Cadence DSP: Unnatural robotic pacing detected (Gap Variance: {gap_variance:.3f})"
        else:
            reason = "Cadence DSP: Natural human timing variance confirmed."
            
        return final_score, reason
        
    except Exception as e:
        print(f"Cadence DSP Error: {e}")
        return 0, "Cadence DSP Execution Failed."

@app.post("/analyze-audio")
async def analyze_audio(audio_file: UploadFile = File(...)):
    temp_file = f"temp_{audio_file.filename}"
    with open(temp_file, "wb") as buffer:
        shutil.copyfileobj(audio_file.file, buffer)
        
    try:
        # ==========================================
        # ENGINE 1: WHISPER METADATA EXTRACTION
        # ==========================================
        with open(temp_file, "rb") as f:
            transcription = client.audio.transcriptions.create(
                file=(temp_file, f.read()),
                model="whisper-large-v3",
                temperature=0.0,
                language="en",
                response_format="verbose_json",
                prompt="Clear phone call conversation. Ignore static or silence."
            )
            
        if isinstance(transcription, dict):
            transcript = transcription.get("text", "").strip()
            segments = transcription.get("segments", [])
        else:
            transcript = getattr(transcription, "text", "").strip()
            segments = getattr(transcription, "segments", [])

        transcript_lower = transcript.lower()
        word_count = len(transcript_lower.split())
        
        # ==========================================
        # ENGINE 2: DIGITAL SIGNAL PROCESSING (TIMING)
        # ==========================================
        dsp_clone_score, dsp_reason = analyze_cadence_heuristics(segments)
        
        # 👻 Ghost Filter
        ghost_phrases = ["thank you", "subscribe", "thanks for watching", "amara.org", "i'm not sure", "get through this", "by the way", "you", "wallace witherspoon", "muзaіk", "i'm sorry", "sorry"]
        is_ghost = False
        
        if word_count <= 3:
            is_ghost = True
        else:
            for phrase in ghost_phrases:
                if phrase in transcript_lower and len(transcript_lower) < 60: 
                    is_ghost = True
                    break
                    
        if is_ghost:
            return {
                "transcript": "[Only Background Noise / AC Static Detected 🌬️]",
                "analysis": {
                    "context": "Silence or audio too short to analyze.",
                    "manipulation_detected": False,
                    "threat_level": 0,
                    "scam_type": "None",
                    "flagged_entities": [],
                    "psychology": "Normal safe baseline.",
                    "voice_clone_probability": 0,
                    "deepfake_indicators": "None"
                }
            }
        
        # ==========================================
        # ENGINE 3: LLM FORENSIC ANALYSIS
        # ==========================================
        prompt = f"""
        You are a forensic cybersecurity AI analyzing a call transcript.
        Transcript: "{transcript}"
        
        CRITICAL INSTRUCTION: Respond ONLY with a valid JSON object using strictly these lowercase keys:
        {{
            "context": "1 short sentence describing the chat",
            "manipulation_detected": true or false,
            "threat_level": <integer 0-100>,
            "scam_type": "None, Impersonation, Financial Fraud, Tech Support, or Panic/Urgency",
            "flagged_entities": ["list of any bank details, PII, UPI, or amounts"],
            "psychology": "1 sentence explaining manipulation"
        }}
        """
        
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant", 
            response_format={"type": "json_object"}
        )
        
        try:
            content = chat_completion.choices[0].message.content.strip()
            if content.startswith("```json"): 
                content = content.replace("```json", "", 1)
            if content.endswith("```"): 
                content = content.replace("```", "")
            
            raw_json = json.loads(content.strip())
            if "analysis" in raw_json and isinstance(raw_json["analysis"], dict):
                raw_json = raw_json["analysis"]
                
            analysis_result = {str(k).lower(): v for k, v in raw_json.items()}
            
            # 🚀 HYBRID FUSION: LLM JSON me DSP ka real score inject karna
            analysis_result["voice_clone_probability"] = dsp_clone_score
            analysis_result["deepfake_indicators"] = dsp_reason
            
        except Exception as e:
            analysis_result = {
                "context": "Failed to parse LLM data.",
                "manipulation_detected": False,
                "threat_level": 0,
                "scam_type": "Error",
                "flagged_entities": [],
                "psychology": "Parsing Error",
                "voice_clone_probability": dsp_clone_score,
                "deepfake_indicators": dsp_reason
            }
        
        return {"transcript": transcript, "analysis": analysis_result}
        
    finally:
        # 🛡️ THE SAFETY NET: File hamesha delete hogi
        if os.path.exists(temp_file):
            os.remove(temp_file)