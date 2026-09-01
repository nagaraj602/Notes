import re
import logging
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import google.generativeai as genai
from app.config import GEMINI_API_KEY, PROMPT_CLASS_NOTES, PROMPT_QA

logger = logging.getLogger("YouTubeService")

class YouTubeService:
  @staticmethod
  def extract_video_id(url_or_id: str) -> str:
      """Extracts YouTube 11-character video ID from any YouTube URL format."""
      url_or_id = url_or_id.strip()
      if len(url_or_id) == 11 and not ("/" in url_or_id or "." in url_or_id):
          return url_or_id
          
      parsed = urlparse(url_or_id)
      if parsed.hostname in ("youtu.be", "www.youtu.be"):
          return parsed.path.lstrip("/")
      if parsed.hostname in ("youtube.com", "[www.youtube.com](https://www.youtube.com)", "m.youtube.com"):
          if parsed.path == "/watch":
              return parse_qs(parsed.query).get("v", [""])[0]
          elif parsed.path.startswith(("/embed/", "/v/", "/shorts/")):
              return parsed.path.split("/")[2]
              
      match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url_or_id)
      if match:
          return match.group(1)
      raise ValueError("Invalid YouTube URL or Video ID provided.")

  @staticmethod
  def get_transcript(video_id: str) -> str:
      """Fetches raw subtitles/transcript for a YouTube video in English, Hindi, or auto-generated."""
      try:
          transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
          # Try manual english, generated english, or any available transcript
          try:
              transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB'])
          except Exception:
              try:
                  transcript = transcript_list.find_generated_transcript(['en', 'en-US', 'en-GB'])
              except Exception:
                  transcript = next(iter(transcript_list))
                  
          data = transcript.fetch()
          formatter = TextFormatter()
          return formatter.format_transcript(data)
      except Exception as e:
          logger.error(f"Failed to fetch YouTube transcript: {e}")
          raise RuntimeError(f"Could not retrieve transcript from YouTube: {str(e)}")

  @staticmethod
  def generate_ai_notes(transcript: str, mode: str = "class_notes", custom_prompt: str = "", api_key: str = None) -> str:
      """Processes the transcript with Google Gemini using the specified prompt."""
      key = api_key or GEMINI_API_KEY
      if not key:
          raise ValueError("Gemini API Key is missing. Please set GEMINI_API_KEY in environment or Settings tab.")
          
      genai.configure(api_key=key)
      
      if mode == "qa":
          system_prompt = PROMPT_QA
      elif mode == "custom" and custom_prompt:
          system_prompt = custom_prompt
      else:
          system_prompt = PROMPT_CLASS_NOTES
          
      model = genai.GenerativeModel("gemini-1.5-flash")
      
      full_prompt = (
          f"SYSTEM INSTRUCTION:\n{system_prompt}\n\n"
          f"---\nTRANSCRIPT CONTENT:\n{transcript}\n---\n\n"
          f"Please output clean, well-formatted Markdown."
      )
      
      response = model.generate_content(full_prompt)
      return response.text