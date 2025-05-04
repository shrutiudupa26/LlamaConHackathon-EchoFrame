from pathlib import Path
from groq import Groq
from youtube_transcript_api import YouTubeTranscriptApi
from config import GROQ_API_KEY, GROQ_MODEL, GROQ_TEMPERATURE, GROQ_MAX_TOKENS
import json
from typing import List, Dict, Optional

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
    """Extract video ID from different YouTube URL formats."""
    try:
        if "youtu.be/" in video_url:
            return video_url.split("youtu.be/")[-1].split("?")[0]
        elif "watch?v=" in video_url:
            return video_url.split("watch?v=")[-1].split("&")[0]
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
        # Process the transcript in exactly 4 chunks total
        total_segments = len(transcript_data)
        chunk_size = (total_segments + 3) // 4  # Round up to ensure we cover all segments
        all_descriptions = []
        
        for i in range(0, total_segments, chunk_size):
            chunk = transcript_data[i:i+chunk_size]
            print(f"\nProcessing chunk {i//chunk_size + 1} of 4")
            
            # Prepare the prompt for visual description generation
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
                    max_tokens=4000
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
            print(f"\nError: Total number of descriptions ({len(all_descriptions)}) does not match total number of transcript segments ({len(transcript_data)})")
            return None
        
    except Exception as e:
        print(f"\nError during visual description generation: {e}")
        import traceback
        traceback.print_exc()
        return None

def process_single_video(video_url: str, client) -> Optional[Dict]:
    """Process a single YouTube video and return the analysis data."""
    try:
        video_id = extract_video_id(video_url)
        if not video_id:
            return None
            
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