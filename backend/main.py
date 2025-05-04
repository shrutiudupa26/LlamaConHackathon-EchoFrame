import os
from fastapi import FastAPI, Request, Form
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import uuid
from generate_podcast import process_and_merge_podcasts
from multilingual import test_translations
import requests
from pydub import AudioSegment
from groq import Groq


# Load environment variables
load_dotenv()

# Set up Groq client API key and base URL
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
print(f"GROQ_API_KEY: {os.getenv('GROQ_API_KEY')}")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set in environment")

MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"
TAVUS_API_KEY = os.getenv("TAVUS_API_KEY")
TAVUS_API_URL = "https://tavusapi.com/v2/conversations"

# FastAPI app setup
app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====== MODELS ======
class PromptRequest(BaseModel):
    question: str

class TranslationRequest(BaseModel):
    text: str
    languages: list[str]

# ====== ROUTES ======

@app.get("/")
def root():
    return {"message": "API is working"}

@app.post("/ask")
def ask_question(data: PromptRequest):
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": data.question}]
            }
        )
        res_json = response.json()
        return {"response": res_json['choices'][0]['message']['content']}
    except Exception as e:
        return {"error": str(e)}

@app.post("/translate")
def translate(req: TranslationRequest):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    translations = {}
    for lang in req.languages:
        prompt = f"Translate the following English text to {lang}:\n{req.text}"
        payload = {
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}]
        }
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            translations[lang] = content
        else:
            translations[lang] = f"Error: {response.status_code}"

    return {"translations": translations}

@app.post("/start-conversation")
def start_conversation():
    payload = {
        "replica_id": "r6ae5b6efc9d",
        "persona_id": "p1d6a2085bce",
        "callback_url": "https://yourwebsite.com/webhook",
        "conversation_name": "A Meeting with Hassaan",
        "conversational_context": (
            "You are about to talk to Hassaan, one of the cofounders of Tavus. "
            "He loves to talk about AI, startups, and racing cars."
        ),
        "custom_greeting": "Hey there Hassaan, long time no see!",
        "properties": {
            "max_call_duration": 3600,
            "participant_left_timeout": 60,
            "participant_absent_timeout": 300,
            "enable_recording": False,
            "enable_closed_captions": True,
            "apply_greenscreen": True,
            "language": "english",
        }
    }

    headers = {
        "Content-Type": "application/json",
        "x-api-key": TAVUS_API_KEY
    }

    response = requests.post(TAVUS_API_URL, json=payload, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.status_code, "message": response.text}

@app.post("/generate-podcast")
def generate_podcast():
    try:
        result = process_and_merge_podcasts()
        return JSONResponse(content={"message": "Podcast created", "result": result})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
@app.post("/test-translations")
def run_translation():
    result = test_translations()
    return JSONResponse(content=result)

@app.post("/generate-audio")
def generate_audio(request: Request, filename: str = Form(...)):
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    TTS_MODEL = "playai-tts"
    VOICE = "Aaliyah-PlayAI"
    url = "https://api.groq.com/openai/v1/audio/speech"

    try:
        with open(filename, 'r', encoding='utf-8') as file:
            podcast_text = file.read()

        if len(podcast_text) <= 9999:
            chunks = [podcast_text]
        else:
            # Split at sentence boundaries (or fallback to 9000-character chunks)
            import re
            sentences = re.split(r'(?<=[.!?])\s+', podcast_text)
            chunks, current = [], ""
            for sentence in sentences:
                if len(current) + len(sentence) < 9000:
                    current += sentence + " "
                else:
                    chunks.append(current.strip())
                    current = sentence + " "
            if current:
                chunks.append(current.strip())

        # Store each audio part
        audio_segments = []
        for i, chunk in enumerate(chunks):
            payload = {
                "model": TTS_MODEL,
                "input": chunk,
                "voice": VOICE,
                "response_format": "mp3"
            }

            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }

            response = requests.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                return JSONResponse(status_code=response.status_code, content={"error": response.text})

            # Save temp MP3
            temp_file = f"chunk_{uuid.uuid4().hex}.mp3"
            with open(temp_file, "wb") as f:
                f.write(response.content)

            audio_segments.append(AudioSegment.from_mp3(temp_file))
            os.remove(temp_file)

        # Combine all segments
        final_audio = sum(audio_segments)
        output_path = f"combined_{uuid.uuid4().hex}.mp3"
        final_audio.export(output_path, format="mp3")

        return FileResponse(output_path, media_type="audio/mpeg", filename="full_podcast.mp3")

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@app.post("/generate-audio-groq")
def generate_audio_groq(filename: str = Form(...)):
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

        # Read the text from the specified file
        with open(filename, 'r') as file:
            podcast_text = file.read()

        # Groq TTS parameters
        model = "playai-tts"
        voice = "Fritz-PlayAI"
        response_format = "wav"
        speech_file_path = f"speech_{os.path.basename(filename).split('.')[0]}.wav"

        # Generate the audio
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=podcast_text,
            response_format=response_format
        )

        response.write_to_file(speech_file_path)

        return FileResponse(speech_file_path, media_type="audio/wav", filename=speech_file_path)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})