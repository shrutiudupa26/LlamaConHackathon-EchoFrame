import os
from groq import Groq
import re

def split_into_chunks(text, max_chars=2000):  # Reduced chunk size to stay well within token limits
    # Split text into sentences using raw string for regex
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) < max_chars:
            current_chunk += sentence + " "
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

# Read the podcast script
with open('podcasts/full_podcast.txt', 'r') as file:
    podcast_text = file.read()

# Initialize Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Split text into chunks and process each chunk
chunks = split_into_chunks(podcast_text)
print(f"Split text into {len(chunks)} chunks")

for i, chunk in enumerate(chunks, 1):
    print(f"\nProcessing chunk {i}/{len(chunks)}...")
    
    # Process each chunk
    completion = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "system",
                "content": "You are a text processor. Return the input text exactly as provided, without any modifications, summaries, or additional commentary."
            },
            {
                "role": "user",
                "content": chunk
            }
        ],
        temperature=0,
        max_tokens=4000,  # Fixed token limit well within model's capacity
        top_p=1,
        stream=True
    )
    
    # Save the processed text
    output_path = f"audio_output/chunk_{i}.txt"
    with open(output_path, 'w') as f:
        for part in completion:
            if part.choices[0].delta.content:
                f.write(part.choices[0].delta.content)
    print(f"Saved: {output_path}")

print("\nAll chunks processed successfully!")