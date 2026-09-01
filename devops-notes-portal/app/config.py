import os

REPO_URL = os.getenv("REPO_URL", "[https://github.com/nagaraj602/Notes.git](https://github.com/nagaraj602/Notes.git)")
REPO_BRANCH = os.getenv("REPO_BRANCH", "main")
AUTO_SYNC_INTERVAL_MINUTES = int(os.getenv("AUTO_SYNC_INTERVAL_MINUTES", "5"))
NOTES_DIR = os.getenv("NOTES_DIR", "/app/data/notes") 
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Default prompt templates as requested
PROMPT_CLASS_NOTES = (
    "I have this transcript. Make it proper as it is looking like class teaching. "
    "It should be in correct thing. Not look like teaching or coversation. "
    "Don't assume anything. Don't add your own concpt. You should give what is there in transcript. "
    "Don't miss anything, don't shorten any explanation from transcript, "
    "Including each and every steps, file names, code etc."
) 

PROMPT_QA = (
    "I have the Qa transcript. Extract all question asked by instructor and if there are any "
    "suggestion/answer given by the instructor, include that. "
    "Don't miss any questions, even the sub questions to it. "
    "I repeat, don't miss any questions."
)