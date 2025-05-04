import os
import json
import requests

# === CONFIGURATION ===

MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
DATA_FOLDER = "data"
OUTPUT_FOLDER = "podcasts"
MERGED_FILE = "full_podcast.txt"

# === FORMAT PODCAST PROMPT ===
def format_podcast_prompt(data):
    return f"""
Below is structured video content, including transcription and visual descriptions.

Please generate a podcast-style script narrating the content, combining what is said and what is seen into a coherent, spoken narration.

Use an engaging tone, introduce the topic, and guide the listener through the visuals and speech as if they're hearing a podcast.

Respond only with the podcast script.

```json
{json.dumps(data, indent=2)}
"""

# === CALL GROQ LLaMA API ===
def call_llama(json_data):
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')  # Get API key from environment variable
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY environment variable is not set")
    headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
    }

    system_prompt = (
        "You are a scriptwriter for podcasts. Your job is to take structured data and generate a spoken-style narrative, "
        "suitable for a podcast episode, under 10000 characters. Use natural, engaging language."
    )

    user_prompt = format_podcast_prompt(json_data)

    payload = {
        "model": MODEL,
        "temperature": 0.7,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload
    )

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise Exception(f"Groq API Error {response.status_code}: {response.text}")

# === MAIN FUNCTION ===
def process_and_merge_podcasts():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    all_scripts = []

    for filename in sorted(os.listdir(DATA_FOLDER)):
        if filename.endswith(".json"):
            filepath = os.path.join(DATA_FOLDER, filename)
            print(f"\n🎬 Processing: {filename}")

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    video_data = json.load(f)

                script = call_llama(video_data)

                episode_path = os.path.join(OUTPUT_FOLDER, filename.replace(".json", ".txt"))
                with open(episode_path, "w", encoding="utf-8") as out_file:
                    out_file.write(script)

                all_scripts.append(f"\n🎙️ Episode based on {filename}:\n\n{script}")
                print(f"✅ Saved: {episode_path}")

            except Exception as e:
                print(f"❌ Error processing {filename}: {e}")

    # Merge all episodes
    merged_path = os.path.join(OUTPUT_FOLDER, MERGED_FILE)
    with open(merged_path, "w", encoding="utf-8") as f:
        f.write("🎧 Full Podcast Episode\n\n")
        f.write("\n\n---\n\n".join(all_scripts))

    print(f"\n✅ Merged full podcast saved to: {merged_path}")

# === RUN ===
if __name__ == "__main__":
    process_and_merge_podcasts()