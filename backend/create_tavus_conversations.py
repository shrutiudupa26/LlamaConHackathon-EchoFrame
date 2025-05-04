import requests
import json
import os

# === CONFIGURATION ===
TAVUS_API_KEY = os.getenv('TAVUS_API_KEY')  # Get API key from environment variable
if not TAVUS_API_KEY:
    raise ValueError("TAVUS_API_KEY environment variable is not set")

TAVUS_API_URL = os.getenv('TAVUS_API_URL')  # Get Url from environment variable
if not TAVUS_API_URL:
    raise ValueError("TAVUS_API_KEY environment variable is not set")
PERSONA_ID = os.getenv('PERSONA_ID')  # Get PersonaID from environment variable
if not PERSONA_ID:
    raise ValueError("PERSONA_ID environment variable is not set")
REPLICA_ID = os.getenv('REPLICA_ID')  # Get ReplicaID from environment variable
if not REPLICA_ID:
    raise ValueError("REPLICA_ID environment variable is not set")

def create_tavus_conversation(
    conversation_name: str = 'Sample Conversation',
    custom_greeting: str = 'Hello! Welcome to our conversation.',
    conversational_context: str = 'This is a sample context for the conversation.',
    max_call_duration: int = 3600,
    participant_left_timeout: int = 60,
    participant_absent_timeout: int = 300,
    enable_recording: bool = False,
    enable_closed_captions: bool = True,
    apply_greenscreen: bool = True,
    language: str = "english",
    recording_s3_bucket_name: str = "",
    recording_s3_bucket_region: str = "",
    aws_assume_role_arn: str = ""
):
    """
    Creates a conversation on the Tavus platform and returns the response data.

    Returns:
        dict: A dictionary with either success or error information.
    """
    
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': TAVUS_API_KEY
    }

    payload = {
        'replica_id': REPLICA_ID,
        'persona_id': PERSONA_ID,
        'conversation_name': conversation_name,
        'conversational_context': conversational_context,
        'custom_greeting': custom_greeting,
        'properties': {
            "max_call_duration": max_call_duration,
            "participant_left_timeout": participant_left_timeout,
            "participant_absent_timeout": participant_absent_timeout,
            "enable_recording": enable_recording,
            "enable_closed_captions": enable_closed_captions,
            "apply_greenscreen": apply_greenscreen,
            "language": language,
            "recording_s3_bucket_name": recording_s3_bucket_name,
            "recording_s3_bucket_region": recording_s3_bucket_region,
            "aws_assume_role_arn": aws_assume_role_arn
        }
    }

    try:
        response = requests.post(TAVUS_API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        data = response.json()
        return {
            "success": True,
            "conversation_id": data.get('conversation_id'),
            "conversation_url": data.get('conversation_url')
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "status_code": response.status_code if 'response' in locals() else None,
            "response_text": response.text if 'response' in locals() else None
        }

if __name__ == "__main__":
    result = create_tavus_conversation()
    print(json.dumps(result, indent=2))
