from pathlib import Path
from dotenv import load_dotenv
import os
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "meta-llama/llama-4-maverick-17b-128e-instruct")
GROQ_TEMPERATURE = float(os.getenv("GROQ_TEMPERATURE", "0.2"))
GROQ_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "4000"))
from groq import Groq
from youtube_transcript_api import YouTubeTranscriptApi
import json
from typing import List, Dict, Optional
import re
import time
from collections import deque
import requests

def setup_groq_client():
    """Setup Groq client with API key."""
    try:
        client = Groq(api_key=GROQ_API_KEY)
        print("Groq client initialized successfully!")
        return client
        
    except Exception as e:
        print(f"Error initializing Groq client: {e}")
        return None

def setup_directories():
    """Create required directories."""
    Path("data/output").mkdir(parents=True, exist_ok=True)
    Path("data/generated").mkdir(parents=True, exist_ok=True)
    Path("data/cleaned").mkdir(parents=True, exist_ok=True)

def extract_video_id(video_url: str) -> Optional[str]:
    """Extract video ID from different YouTube URL formats, including shorts."""
    try:
        if "youtu.be/" in video_url:
            return video_url.split("youtu.be/")[-1].split("?")[0]
        elif "watch?v=" in video_url:
            return video_url.split("watch?v=")[-1].split("&")[0]
        elif "/shorts/" in video_url:
            return video_url.split("/shorts/")[-1].split("?")[0].split("&")[0]
        else:
            print(f"Invalid YouTube URL format: {video_url}")
            return None
    except Exception as e:
        print(f"Error extracting video ID from {video_url}: {e}")
        return None

def format_timestamp(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def extract_transcript(video_url: str) -> Optional[List[Dict]]:
    """Extract transcript from YouTube video and return formatted transcript data."""
    try:
        print(f"Extracting transcript from: {video_url}")
        
        video_id = extract_video_id(video_url)
        if not video_id:
            return None
        
        # Get transcript using youtube-transcript-api
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Format transcript with timestamps
        formatted_transcript = []
        for segment in transcript_list:
            formatted_segment = {
                "start_time": format_timestamp(segment['start']),
                "end_time": format_timestamp(segment['start'] + segment['duration']),
                "text": segment['text']
            }
            formatted_transcript.append(formatted_segment)
            
        print("Transcript successfully extracted!")
        return formatted_transcript
        
    except Exception as e:
        print(f"Error during transcript extraction: {e}")
        return None

def generate_visual_description(transcript_data: List[Dict], client) -> Optional[List[Dict]]:
    """Generate visual descriptions for the video using Groq."""
    try:
        # Token usage tracker
        token_window = deque()
        TOKEN_LIMIT_PER_MIN = 280000
        MAX_TOKENS_PER_REQUEST = 8192
        CONTEXT_WINDOW = 128000  # Llama 4 Maverick context window
        # Estimate tokens per transcript segment and prompt overhead
        tokens_per_segment = 40  # Adjust as needed
        prompt_overhead = 1000   # Estimated tokens for prompt instructions
        # Calculate how many segments fit in one request
        max_input_tokens = CONTEXT_WINDOW - MAX_TOKENS_PER_REQUEST - prompt_overhead
        segments_per_chunk = max_input_tokens // tokens_per_segment
        segments_per_chunk = min(segments_per_chunk, 50)  # Limit to 50 segments per chunk
        total_segments = len(transcript_data)
        num_chunks = max(1, (total_segments + segments_per_chunk - 1) // segments_per_chunk)
        chunk_size = (total_segments + num_chunks - 1) // num_chunks
        print(f"Dynamic chunking: {num_chunks} chunks, {chunk_size} segments per chunk (estimated)")
        all_descriptions = []
        
        for i in range(0, total_segments, chunk_size):
            chunk = transcript_data[i:i+chunk_size]
            print(f"\nProcessing chunk {i//chunk_size + 1} of {num_chunks}")
            # Estimate tokens for this request (input + output)
            prompt = f"""
            You are an AI assistant analyzing a video. Based on the following transcript segments, 
            generate detailed visual descriptions for each segment. Focus on what a person would see 
            (e.g., people, objects, actions, text on screen).

            Transcript segments:
            {json.dumps(chunk, indent=2)}

            Generate visual descriptions in the following exact JSON format:
            [
                {{
                    "start_time": "00:00:00",
                    "end_time": "00:00:05",
                    "description": "Detailed visual description here"
                }},
                ...
            ]

            Important instructions:
            1. Match the start_time and end_time exactly with the transcript segments
            2. Provide detailed visual descriptions
            3. Return ONLY the JSON array, nothing else
            4. Do not include any markdown formatting or code block markers
            5. Ensure the JSON is valid and properly formatted
            6. Use double quotes for all property names and string values
            7. Do not include any explanatory text before or after the JSON
            8. Make sure the JSON is complete and properly closed with a closing bracket
            """
            estimated_tokens = int(len(prompt) / 2) + MAX_TOKENS_PER_REQUEST
            # Throttle if needed
            now = time.time()
            # Remove tokens older than 60 seconds
            while token_window and now - token_window[0][0] > 60:
                token_window.popleft()
            used_tokens = sum(t[1] for t in token_window)
            if used_tokens + estimated_tokens > TOKEN_LIMIT_PER_MIN:
                wait_time = 60 - (now - token_window[0][0])
                print(f"[Token Limit] Waiting {wait_time:.1f} seconds to stay under 280,000 tokens/minute...")
                time.sleep(wait_time)
            # After waiting, record this request
            token_window.append((time.time(), estimated_tokens))
            
            print("Sending prompt to Groq API...")
            try:
                # Call Groq API with appropriate max_tokens
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    model=GROQ_MODEL,
                    temperature=GROQ_TEMPERATURE,
                    max_tokens=MAX_TOKENS_PER_REQUEST
                )
            except Exception as e:
                print(f"Groq API Error: {e}")
                if hasattr(e, 'response'):
                    print(f"API Response: {e.response}")
                return None
            
            # Get the response content
            response_content = chat_completion.choices[0].message.content
            print("Received response from Groq API")
            print("Raw response length:", len(response_content))
            print("First 500 characters of response:")
            print(response_content[:500])
            print("Last 100 characters of response:")
            print(response_content[-100:])
            
            # Clean the response to ensure it's valid JSON
            response_content = response_content.replace("```json", "").replace("```", "").strip()

            # Fix missing commas between fields in objects
            response_content = re.sub(r'("start_time":\s*"[^"]+")\s+("end_time":)', r'\1, \2', response_content)
            response_content = re.sub(r'("end_time":\s*"[^"]+")\s+("description":)', r'\1, \2', response_content)

            # Ensure the response is properly closed
            if not response_content.endswith(']'):
                print("Warning: Response does not end with closing bracket")
                # Try to find the last complete JSON object
                last_bracket = response_content.rfind(']')
                if last_bracket != -1:
                    response_content = response_content[:last_bracket + 1]
                    print("Truncated response to last complete JSON object")
                else:
                    print("Could not find complete JSON object")
                    return None
            
            # Parse the visual descriptions
            try:
                print("Attempting to parse JSON response...")
                visual_descriptions = json.loads(response_content)
                
                # Validate the structure
                if not isinstance(visual_descriptions, list):
                    print("Error: Response is not a list")
                    print("Response type:", type(visual_descriptions))
                    return None
                    
                print(f"Successfully parsed {len(visual_descriptions)} visual description segments")
                
                # Validate each item
                for i, item in enumerate(visual_descriptions):
                    if not all(key in item for key in ["start_time", "end_time", "description"]):
                        print(f"Error: Missing required fields in segment {i}")
                        print("Segment content:", item)
                        return None
                        
                all_descriptions.extend(visual_descriptions)
                
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON response: {e}")
                print("Error location:", e.pos)
                print("Response content around error:")
                start = max(0, e.pos - 50)
                end = min(len(response_content), e.pos + 50)
                print(response_content[start:end])
                return None
            except ValueError as e:
                print(f"Error validating response structure: {e}")
                return None
        
        if len(all_descriptions) == len(transcript_data):
            return all_descriptions
        else:
            diff = abs(len(all_descriptions) - len(transcript_data))
            if diff <= 3:
                print(f"Warning: {diff} segments missing/extra. Proceeding with available descriptions.")
                return all_descriptions
            print(f"\nError: Total number of descriptions ({len(all_descriptions)}) does not match total number of transcript segments ({len(transcript_data)})")
            return None
        
    except Exception as e:
        print(f"\nError during visual description generation: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_video_title(video_id: str) -> Optional[str]:
    """Fetch the title of a YouTube video using the oEmbed endpoint."""
    try:
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        response = requests.get(oembed_url)
        if response.status_code == 200:
            return response.json()['title']
        return None
    except Exception as e:
        print(f"Error fetching video title: {e}")
        return None

def process_single_video(video_url: str, client) -> Optional[Dict]:
    """Process a single YouTube video and return the analysis data."""
    try:
        video_id = extract_video_id(video_url)
        if not video_id:
            return None
            
        # Get video title
        video_title = get_video_title(video_id)
        if not video_title:
            video_title = "Untitled Video"
            
        # Extract transcript
        transcript_data = extract_transcript(video_url)
        if not transcript_data:
            return None
            
        # Generate visual descriptions
        visual_descriptions = generate_visual_description(transcript_data, client)
        if not visual_descriptions:
            return None
            
        # Combine all data
        video_analysis = {
            "video_id": video_id,
            "title": video_title,
            "url": video_url,
            "transcription": transcript_data,
            "visual_description": visual_descriptions
        }
        
        # Save individual video analysis
        output_file = f"data/output/youtube_{video_id}_enhanced.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(video_analysis, f, indent=2)
        print(f"Saved individual analysis to: {output_file}")
        
        return video_analysis
        
    except Exception as e:
        print(f"Error processing video {video_url}: {e}")
        return None

def clean_output_directory():
    """Remove all files from the output directory before processing."""
    try:
        output_dir = Path("data/output")
        if output_dir.exists():
            print("\nCleaning output directory...")
            for file in output_dir.glob("*"):
                try:
                    file.unlink()
                    print(f"Removed: {file}")
                except Exception as e:
                    print(f"Error removing {file}: {e}")
            print("Output directory cleaned successfully!")
        else:
            print("\nOutput directory does not exist, creating it...")
            output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Error cleaning output directory: {e}")

def process_multiple_videos(video_urls: List[str]):
    """Process multiple YouTube videos and combine their analyses."""
    try:
        # Setup Groq client
        client = setup_groq_client()
        if not client:
            print("Failed to initialize Groq client. Exiting...")
            return
            
        # Setup directories and clean output
        setup_directories()
        clean_output_directory()
        
        # Process each video
        all_analyses = []
        for url in video_urls:
            try:
                print(f"\nProcessing video: {url}")
                analysis = process_single_video(url, client)
                if analysis:
                    all_analyses.append(analysis)
                else:
                    print(f"Failed to process video: {url}")
            except Exception as e:
                print(f"Error processing video {url}: {e}")
                continue
        
        # Save combined analysis
        if all_analyses:
            combined_output = {
                "total_videos": len(all_analyses),
                "videos": all_analyses
            }
            
            output_file = "data/output/final.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(combined_output, f, indent=2)
            print(f"\nSaved combined analysis to: {output_file}")
            
    except Exception as e:
        print(f"Error in batch processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # List of YouTube video URLs to process
    video_urls = [
        "https://youtu.be/c9RY8RosGPo",
        "https://www.youtube.com/watch?v=IyQzCoiwE5E"
    ]
    
    process_multiple_videos(video_urls) 