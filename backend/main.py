import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI  # ✅ This line is required
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()


# Set API key and base URL
# Set your Groq API key
client = OpenAI(
    api_key=os.getenv("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"),  # 🔐 This is where your key is used
    base_url="https://api.groq.com/openai/v1"  # 🔁 For Groq compatibility
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Or ["*"] for all origins (not recommended for prod)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)
TAVUS_API_KEY = "1052c21a83f64a099888575d43b503f7"
TAVUS_API_URL = "https://tavusapi.com/v2/conversations"


# ✅ Make sure this is defined BEFORE using it
class PromptRequest(BaseModel):
    question: str
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
            "recording_s3_bucket_name": "",
            "recording_s3_bucket_region": "",
            "aws_assume_role_arn": ""
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

@app.post("/ask")
async def ask_question(data: PromptRequest):
    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            messages=[
                {"role": "user", "content": data.question}
            ]
        )
        return {"response": response.choices[0].message.content}
    except Exception as e:
        return {"error": str(e)}
