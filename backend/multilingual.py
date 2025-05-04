import requests
import json
import os


# === CONFIGURATION ===

MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"



def test_translations():
    """
    Test translation of a single English text into multiple languages.
    """
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')  # Get API key from environment variable
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY environment variable is not set")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }

    # English text to translate
    english_text = "The rapid advancement of artificial intelligence is revolutionizing various industries, from healthcare to finance, by enabling more efficient data analysis and decision-making processes."

    # Target languages
    target_languages = [
        "Latin",
        "Hindi",
        "German",
        "Italian"
    ]

    print("Original English text:")
    print(english_text)
    print("\nTranslations:")

    for language in target_languages:
        translation_prompt = f"Translate the following English text to {language}:\n{english_text}"

        data = {
            "model": MODEL,
            "messages": [
                {"role": "user", "content": translation_prompt}
            ]
        }

        try:
            print(f"\n{language}:")
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)

            if response.status_code == 200:
                response_data = response.json()
                content = response_data['choices'][0]['message']['content']
                print(content)
            else:
                print(f"Error: {response.status_code}")
                print("Response:", response.text)

        except Exception as e:
            print(f"Error occurred: {str(e)}")

if __name__ == "__main__":
    print("Testing translations of English text to multiple languages...")
    test_translations()