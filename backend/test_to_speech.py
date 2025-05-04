
# from dotenv import load_dotenv
# from elevenlabs.client import ElevenLabs
# from elevenlabs import play
# import os

# load_dotenv()

# client = ElevenLabs(
#   api_key=os.getenv("ELEVENLABS_API_KEY"),
# )
# # Read the podcast script
# with open('podcasts/full_podcast.txt', 'r') as file:
#     podcast_text = file.read()
# audio = client.text_to_speech.convert(
#     text=podcast_text,
#     voice_id="JBFqnCBsd6RMkjVDRZzb",
#     model_id="eleven_multilingual_v2",
#     output_format="mp3_44100_128",
# )

# play(audio)

import os
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
# Read the podcast script
with open('podcasts/full_podcast.txt', 'r') as file:
    podcast_text = file.read()
speech_file_path = "speech.wav" 
model = "playai-tts"
voice = "Fritz-PlayAI"
text = podcast_text
response_format = "wav"

response = client.audio.speech.create(
    model=model,
    voice=voice,
    input=text,
    response_format=response_format
)

response.write_to_file(speech_file_path)