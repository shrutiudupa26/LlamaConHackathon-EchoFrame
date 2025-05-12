import os
import io
import sounddevice as sd
import soundfile as sf
from pathlib import Path
import shutil
import tempfile
from fastapi import FastAPI, Request, Form, Response, BackgroundTasks
from starlette.responses import PlainTextResponse
from fastapi.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import uuid
from generate_podcast import process_and_merge_podcasts
from multilingual import test_translations
from create_tavus_conversations import create_tavus_conversation
import requests
import numpy as np
from groq import Groq
from fastapi import Body
from generate_video_metadata import process_multiple_videos
import json

# Set up Groq client API key and base URL
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
print(f"GROQ_API_KEY: {os.getenv('GROQ_API_KEY') and 'is set' or 'not set'}")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set in environment")

MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"
TAVUS_API_KEY = os.getenv("TAVUS_API_KEY")
TAVUS_API_URL = "https://tavusapi.com/v2/conversations"
TAVUS_REPLICA_ID = os.getenv("TAVUS_REPLICA_ID")
TAVUS_PERSONA_ID = os.getenv("TAVUS_PERSONA_ID")

# FastAPI app setup with metadata for documentation
app = FastAPI(
    title="EchoFrame API",
    description="""
    EchoFrame API provides endpoints for video processing, translation, and conversation management.
    
    Key features:
    * Process and analyze YouTube videos
    * Generate podcast-style summaries
    * Translate content to multiple languages
    * Manage video conversations
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

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
    
    class Config:
        schema_extra = {
            "example": {
                "question": "What are the main topics covered in the video?"
            }
        }

class TranslationRequest(BaseModel):
    languages: list[str]
    
    class Config:
        schema_extra = {
            "example": {
                "languages": ["es", "de", "hi"]
            }
        }

class SingleTranslationRequest(BaseModel):
    language: str
    
    class Config:
        schema_extra = {
            "example": {
                "language": "es"
            }
        }

class ConversationRequest(BaseModel):
    person: str
    language: str
    
    class Config:
        schema_extra = {
            "example": {
                "person": "John Doe",
                "language": "English"
            }
        }

class ConversationMessage(BaseModel):
    conversation_id: str
    message: str
    
    class Config:
        schema_extra = {
            "example": {
                "conversation_id": "abc123",
                "message": "Hello, how can I help you today?"
            }
        }

# ====== ROUTES ======

@app.get("/", tags=["Health Check"])
def root():
    """
    Health check endpoint to verify the API is running.
    """
    return {"message": "API is working"}

@app.post("/ask", tags=["Video Analysis"])
def ask_question(data: PromptRequest):
    """
    Ask questions about the processed video content.
    
    The response will be generated based on the video's transcript and visual descriptions.
    """
    try:
        # Check if final.json exists
        if not os.path.exists("data/output/final.json"):
            return {"error": "No video data available. Please process videos first."}

        # Load context from final.json
        with open("data/output/final.json", "r", encoding="utf-8") as f:
            context = f.read()

        LLAMA_API_KEY = os.getenv("LLAMA_API_KEY")
        if not LLAMA_API_KEY:
            return {"error": "LLAMA_API_KEY not configured"}

        llama_api_url = "https://api.llama.com/v1/chat/completions"
        system_prompt = (
            "You are an expert assistant. The following is structured data about a video (including transcript and visual descriptions). "
            "Use this data to answer any questions the user asks about the video. Here is the data:\n"
            f"{context}"
        )
        prompt_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": data.question}
        ]
        
        response = requests.post(
            llama_api_url,
            headers={
                "Authorization": f"Bearer {LLAMA_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "Llama-4-Maverick-17B-128E-Instruct-FP8",
                "messages": prompt_messages,
                "max_tokens": 900000
            }
        )

        if response.status_code != 200:
            error_message = "API call failed"
            try:
                error_json = response.json()
                if isinstance(error_json, dict):
                    error_message = error_json.get('error', {}).get('message', error_message)
            except:
                error_message = response.text
            return {"error": f"API call failed: {error_message}"}

        res_json = response.json()
        
        # Handle different possible response formats
        if 'completion_message' in res_json:
            content = res_json['completion_message']['content']['text']
        elif 'choices' in res_json and len(res_json['choices']) > 0:
            content = res_json['choices'][0]['message']['content']
        else:
            return {"error": "Unexpected API response format"}

        return {"response": content}

    except FileNotFoundError:
        return {"error": "Required data files not found"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON in data files"}
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}

@app.post("/translate", tags=["Translation"])
async def translate(req: TranslationRequest):
    """
    Translate the podcast content to specified languages.
    
    Supported languages:
    - English (en)
    - Spanish (es)
    - German (de)
    - Hindi (hi)
    """
    try:
        # Load the summarization from the podcast file
        podcast_file = Path("podcasts/full_podcast.txt")
        if not podcast_file.exists():
            return JSONResponse(
                status_code=404,
                content={"error": "No summarization available. Process videos first."}
            )
            
        with open(podcast_file, "r", encoding="utf-8") as f:
            text_to_translate = f.read()

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        translations = {}
        for lang in req.languages:
            prompt = f"""
            Translate the following English text to {lang}. Maintain the same tone and style, 
            and ensure all technical terms and proper nouns are accurately preserved:

            {text_to_translate}
            """
            
            payload = {
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,  # Lower temperature for more accurate translations
                "max_tokens": 4000  # Adjust based on your needs
            }
            
            try:
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions", 
                    headers=headers, 
                    json=payload
                )
                
                if response.status_code == 200:
                    content = response.json()["choices"][0]["message"]["content"]
                    translations[lang] = content
                else:
                    translations[lang] = f"Translation error: {response.status_code}"
                    print(f"Translation error for {lang}: {response.text}")
            except Exception as e:
                translations[lang] = f"Translation error: {str(e)}"
                print(f"Exception during translation to {lang}: {str(e)}")

        return {"translations": translations}
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Translation failed: {str(e)}"}
        )

@app.post("/start-conversation", tags=["Conversation"])
def start_conversation(request: ConversationRequest):
    """
    Start a new video conversation.
    
    Creates a new conversation with specified language and participant name.
    Returns a URL for the video conversation interface.
    """
    # Validate Tavus config
    if not all([TAVUS_REPLICA_ID, TAVUS_PERSONA_ID, TAVUS_API_KEY]):
        return JSONResponse(
            status_code=500,
            content={"error": "Missing required Tavus environment variables"}
        )

    # Load first 5 lines from each JSON file
    video_data = {}
    output_dir = Path("data/output")
    try:
        for json_file in output_dir.glob("*.json"):
            if json_file.name != "final.json":
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # For each key in the JSON, take only first 5 items if it's a list
                    limited_data = {}
                    for key, value in data.items():
                        if isinstance(value, list):
                            limited_data[key] = value[:5]
                        else:
                            limited_data[key] = value
                    video_data[json_file.name] = limited_data
                    print(f"First 5 lines from {json_file.name}:", json.dumps(limited_data, indent=2))
    except Exception as e:
        print(f"Error loading video JSONs: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to load video data: {str(e)}"}
        )

    payload = {
        "replica_id": TAVUS_REPLICA_ID,
        "persona_id": TAVUS_PERSONA_ID,
        "callback_url": "https://yourwebsite.com/webhook",
        "conversation_name": f"DIY Master Session with {request.person}",
        "conversational_context": (
            f"You are a DIY master assisting {request.person} with video tutorials in {video_data}. "
            f"Always refer the video using the title and not the video id."
            f"You need to summarize the steps to do the tasks if the user asks how to do the tasks described in the videos. "
            f"You need to pinpoint the exact timestamp in the video where the user can find the information they need."
        ),
        "custom_greeting": f"Hello {request.person}! I've analyzed the project videos in detail. What would you like to know?",
        "properties": {
            "language": request.language,
            "enable_recording": False,
            "enable_closed_captions": True
        }
    }

    # Call Tavus API
    headers = {"Content-Type": "application/json", "x-api-key": TAVUS_API_KEY}
    response = requests.post(TAVUS_API_URL, json=payload, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        error_message = response.text
        error_code = response.status_code
        
        try:
            # Try to parse the error message as JSON
            error_json = response.json()
            if "message" in error_json:
                error_message = error_json["message"]
            
            # Check for specific errors
            if "maximum concurrent conversations" in error_message:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": error_code,
                        "message": "You have reached the maximum number of concurrent conversations with Tavus. Please end some existing conversations before starting a new one.",
                        "details": error_message
                    }
                )
        except:
            # If we can't parse the JSON, just continue with the original error message
            pass
            
        return JSONResponse(
            status_code=error_code,
            content={"error": error_code, "message": error_message}
        )

@app.post("/generate-podcast", tags=["Podcast"])
def generate_podcast():
    """
    Generate a podcast script from processed video content.
    
    Creates a narrative summary of the video content in podcast format.
    """
    try:
        result = process_and_merge_podcasts()
        return JSONResponse(content={"message": "Podcast created", "result": result})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/test-translations", tags=["Translation"])
def run_translation(request: SingleTranslationRequest = Body(...)):
    """
    Test translation for a single language.
    
    This endpoint is used to test the translation functionality with a sample text.
    """
    result = test_translations(request.language)
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
                "response_format": "wav"  # Changed to wav format
            }

            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }

            response = requests.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                return JSONResponse(status_code=response.status_code, content={"error": response.text})

            # Save temp WAV
            temp_file = f"chunk_{uuid.uuid4().hex}.wav"
            with open(temp_file, "wb") as f:
                f.write(response.content)

            # Read the audio file
            data, samplerate = sf.read(temp_file)
            audio_segments.append((data, samplerate))
            os.remove(temp_file)

        # Combine all segments
        if audio_segments:
            # Ensure all segments have the same sample rate
            samplerate = audio_segments[0][1]
            combined_data = np.concatenate([segment[0] for segment in audio_segments])
            
            # Save the combined audio
            output_path = f"combined_{uuid.uuid4().hex}.wav"
            sf.write(output_path, combined_data, samplerate)

            return FileResponse(output_path, media_type="audio/wav", filename="full_podcast.wav")
        else:
            return JSONResponse(status_code=500, content={"error": "No audio segments were generated"})

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

@app.post("/create_tavus_conversation")
def run_translation():
    result = create_tavus_conversation()
    return JSONResponse(content=result)

@app.get("/generate-speech", tags=["Podcast"])
def generate_speech():
    """
    Convert the podcast text to speech.
    
    Generates an audio file from the podcast script using text-to-speech.
    """
    try:
        # Check if podcast text file exists
        podcast_file_path = Path("podcasts/full_podcast.txt")
        if not podcast_file_path.exists():
            return Response(
                content="Podcast text file not found. Please process videos first.",
                status_code=404
            )
        
        # Read the podcast text
        with open(podcast_file_path, 'r', encoding='utf-8') as file:
            podcast_text = file.read()
        
        # Initialize the Groq client with API key
        GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
        if not GROQ_API_KEY:
            return Response(
                content="GROQ_API_KEY environment variable not set",
                status_code=500
            )
        
        client = Groq(api_key=GROQ_API_KEY)
        
        try:
            # Generate speech with Groq API
            response = client.audio.speech.create(
                model="playai-tts",
                voice="Fritz-PlayAI",
                input=podcast_text,
                response_format="wav"
            )

            # Create a temporary file to save the audio
            temp_file = Path(f"temp_speech_{uuid.uuid4().hex}.wav")
            response.write_to_file(str(temp_file))
            
            # Read the file content
            with open(temp_file, "rb") as f:
                audio_content = f.read()
            
            # Delete the temporary file
            try:
                temp_file.unlink()
            except Exception as e:
                print(f"Warning: Could not delete temporary file {temp_file}: {e}")
            
            # Return the audio content
            return Response(
                content=audio_content,
                media_type="audio/wav",
                headers={
                    "Content-Disposition": "attachment; filename=podcast.wav"
                }
            )
            
        except Exception as groq_error:
            error_message = str(groq_error)
            print(f"Groq TTS Error: {error_message}")
            
            if "terms acceptance" in error_message.lower():
                return Response(
                    content="The Groq TTS model requires terms acceptance. Please have the organization admin accept the terms at https://console.groq.com/playground?model=playai-tts",
                    status_code=400
                )
            
            return Response(
                content=f"Error generating speech: {error_message}",
                status_code=500
            )
            
    except Exception as e:
        print(f"Error in generate_speech: {str(e)}")
        return Response(
            content=f"Error generating speech: {str(e)}",
            status_code=500
        )

@app.get("/podcast-text", response_class=PlainTextResponse, tags=["Podcast"])
async def get_podcast_text():
    """
    Get the generated podcast script text.
    
    Returns the current podcast script in plain text format.
    """
    final_json_path = Path("data/output/final.json")
    if not final_json_path.exists():
        return PlainTextResponse("No podcast data available yet. Process videos first.", status_code=404)
    
    file_path = Path("podcasts/full_podcast.txt")
    if not file_path.exists():
        return PlainTextResponse("Podcast text file not found", status_code=404)
    
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

@app.post("/clear-output-folder", tags=["System"])
async def clear_output_folder():
    """
    Clear the output folder of processed files.
    
    Use this to clean up temporary files and start fresh.
    """
    """Clear the output folder when the page is refreshed"""
    output_folder = Path("data/output")
    if output_folder.exists():
        for file_path in output_folder.glob("*"):
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                shutil.rmtree(file_path)
    
    return {"status": "success", "message": "Output folder cleared"}

@app.post("/auto-summarize")
async def auto_summarize():
    """Automatically generate a summarization using the LlamaAPI with final.json data"""
    try:
        final_json_path = Path("data/output/final.json")
        if not final_json_path.exists():
            return JSONResponse(
                status_code=404,
                content={"error": "final.json not found. Process videos first."}
            )
        
        # Load context from final.json
        with open(final_json_path, "r", encoding="utf-8") as f:
            context = f.read()

        # Get LlamaAPI key from environment variables
        LLAMA_API_KEY = os.getenv("LLAMA_API_KEY")
        if not LLAMA_API_KEY:
            return JSONResponse(
                status_code=500,
                content={"error": "LLAMA_API_KEY environment variable not set"}
            )
        
        # Define the API endpoint
        llama_api_url = "https://api.llama.com/v1/chat/completions"
        
        # Create the system prompt for summarization
        system_prompt = (
            "You are an expert assistant tasked with summarizing video content. "
            "The following is structured data about a video (including transcript and visual descriptions). "
            "Create a detailed summary of the video content based on this data. Here is the data:\n"
            f"{context}"
        )
        
        # Define the messages for the API request
        prompt_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Please provide a comprehensive summary of this video content."}
        ]
        
        # Make the API request
        response = requests.post(
            llama_api_url,
            headers={
                "Authorization": f"Bearer {LLAMA_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "Llama-4-Maverick-17B-128E-Instruct-FP8",
                "messages": prompt_messages,
                "max_tokens": 1024
            }
        )
        
        if response.status_code == 200:
            res_json = response.json()
            if 'completion_message' in res_json:
                summary = res_json['completion_message']['content']['text']
                
                # Save the summary to a file
                podcast_dir = Path("podcasts")
                podcast_dir.mkdir(exist_ok=True)
                
                with open("podcasts/full_podcast.txt", "w", encoding="utf-8") as f:
                    f.write(summary)
                
                return {"response": summary}
            else:
                return {"error": f"'completion_message' key not found in response: {res_json}"}
        else:
            # Log the entire response JSON
            try:
                error_json = response.json()
            except ValueError:
                error_json = response.text
            return {"error": f"API call failed with status code {response.status_code}: {error_json}"}
            
    except Exception as e:
        return {"error": str(e)}

@app.post("/process-videos", tags=["Video Analysis"])
async def process_videos(request: Request):
    """
    Process a list of YouTube videos.
    
    Analyzes the videos, generates transcripts, and creates visual descriptions.
    Also triggers automatic summarization.
    """
    data = await request.json()
    video_urls = data.get("videos", [])
    if not video_urls:
        return {"error": "No videos provided"}
    process_multiple_videos(video_urls)
    
    # Automatically trigger summarization after videos are processed
    summarization_result = await auto_summarize()
    return {"status": "Processing complete", "summarization": summarization_result}

@app.get("/check-files", tags=["System"])
async def check_files():
    """
    Check the status of processed files.
    
    Returns information about available files in the data and podcasts folders.
    """
    """Debug endpoint to check what files are available in the data folders"""
    output_folder = Path("data/output")
    podcasts_folder = Path("podcasts")
    
    output_files = []
    if output_folder.exists():
        output_files = [str(f.name) for f in output_folder.glob("*") if f.is_file()]
    
    podcast_files = []
    if podcasts_folder.exists():
        podcast_files = [str(f.name) for f in podcasts_folder.glob("*") if f.is_file()]
    
    final_json_exists = output_folder.joinpath("final.json").exists()
    podcast_text_exists = podcasts_folder.joinpath("full_podcast.txt").exists()
    
    return {
        "output_folder_exists": output_folder.exists(),
        "output_files": output_files,
        "final_json_exists": final_json_exists,
        "podcasts_folder_exists": podcasts_folder.exists(),
        "podcast_files": podcast_files,
        "podcast_text_exists": podcast_text_exists
    }

@app.post("/send-message", tags=["Conversation"])
def send_message(message: ConversationMessage):
    """
    Send a message in an existing conversation.
    
    Requires an active conversation ID and the message content.
    """
    try:
        # Endpoint for sending messages to an existing conversation
        url = f"{TAVUS_API_URL}/{message.conversation_id}/messages"
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": TAVUS_API_KEY
        }
        
        payload = {
            "message": message.message,
            "properties": {
                "enable_recording": False,
                "enable_closed_captions": True
            }
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            return response.json()
        else:
            error_message = response.text
            try:
                error_json = response.json()
                if "message" in error_json:
                    error_message = error_json["message"]
            except:
                pass
                
            return JSONResponse(
                status_code=response.status_code,
                content={"error": error_message}
            )
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to send message: {str(e)}"}
        )

@app.post("/end-conversation/{conversation_id}", tags=["Conversation"])
def end_conversation(conversation_id: str):
    """
    End an active video conversation.
    
    This will properly clean up and close the specified conversation.
    """
    try:
        # Call Tavus API to end the conversation
        url = f"{TAVUS_API_URL}/{conversation_id}/end"
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": TAVUS_API_KEY
        }
        
        response = requests.post(url, headers=headers)
        
        if response.status_code == 200:
            return {"success": True, "message": "Conversation ended successfully"}
        else:
            error_message = response.text
            try:
                error_json = response.json()
                if "message" in error_json:
                    error_message = error_json["message"]
            except:
                pass
                
            return JSONResponse(
                status_code=response.status_code,
                content={"error": error_message}
            )
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to end conversation: {str(e)}"}
        )

# Add documentation route
@app.get("/api-docs", response_class=HTMLResponse, tags=["Documentation"])
async def get_documentation():
    """
    Get API documentation in HTML format.
    
    Provides a human-readable overview of available endpoints and their usage.
    """
    return """
    <html>
        <head>
            <title>EchoFrame API Documentation</title>
            <meta http-equiv="refresh" content="0;url=/docs" />
        </head>
        <body>
            <p>Redirecting to API documentation...</p>
        </body>
    </html>
    """