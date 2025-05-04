import os
from groq import Groq
import io
import sounddevice as sd
import soundfile as sf


# Initialize the Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


# Read the podcast text
with open('podcasts/full_podcast.txt', 'r') as file:
   podcast_text = file.read()


# Generate speech
response = client.audio.speech.create(
   model="playai-tts",
   voice="Fritz-PlayAI",
   input=podcast_text,
   response_format="wav"
)


# Read the audio binary into memory
audio_bytes = io.BytesIO(response.read())


# Decode and play the audio
data, samplerate = sf.read(audio_bytes)
sd.play(data, samplerate)
sd.wait()