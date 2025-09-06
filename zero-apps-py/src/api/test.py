import logging

import os
from dotenv import load_dotenv  

import openai
import yt_dlp

load_dotenv()

# ----------------------------
# Setup logging
# ----------------------------
logging.basicConfig(
    level=logging.DEBUG,  # DEBUG level logs everything
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set. Please check your .env file or environment variables.")
else: 
    print(f"Got Key Works->OPENAI_API_KEY",{OPENAI_API_KEY})

url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

def download_audio(video_url: str, output_path: str = "audio.mp3"):
    logger.info(f"Downloading audio from {video_url}")
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])
    return output_path

def transcribe_audio(file_path: str):
    logger.info("Sending audio to Whisper for transcription")
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return transcript.text

audio_path = download_audio(url, "1.mp3")
transcript = transcribe_audio(audio_path)
print("Transcript:", transcript)