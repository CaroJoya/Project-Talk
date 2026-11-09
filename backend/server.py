import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai

# 1. Load environment variables
load_dotenv()

# 2. Setup Gemini Client
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

# 3. Setup FastAPI
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Smart Path Resolver
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
folder_path = os.path.join(BASE_DIR, "projects")

@app.get("/api/projects")
def get_projects():
    if not os.path.exists(folder_path):
        return {"projects": []}
    
    files = [f.replace(".txt", "") for f in os.listdir(folder_path) if f.endswith(".txt")]
    files.sort()
    return {"projects": files}

class ChatRequest(BaseModel):
    question: str
    project: str

@app.post("/api/chat")
def chat(request: ChatRequest):
    if not client:
        print("ERROR: Gemini client not initialized. API key missing.")
        return {"answer": "Error: GEMINI_API_KEY is not set in the environment variables."}

    file_path = os.path.join(folder_path, f"{request.project}.txt")
    
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            project_info = f.read()
    else:
        return {"answer": f"Sorry, I couldn't find the notes for the '{request.project}' project."}

    prompt = f"""
    You are a helpful portfolio assistant for a developer. 
    The user is asking about their specific project: {request.project}.
    
    Answer ONLY using the project info provided below. 
    If the answer is not in the info, say "I don't have that detail in my project notes."
    Keep answers short (2-4 sentences), friendly, and professional.

    PROJECT INFO:
    {project_info}

    Visitor's question: {request.question}
    """
    
    try:
        # Using the stable 3.6-flash model
        response = client.models.generate_content(
            model='gemini-3.6-flash', 
            contents=prompt
        )
        return {"answer": response.text}
    except Exception as e:
        # THIS IS THE MAGIC LINE: It prints the exact error to Vercel's logs
        print(f"--- GEMINI API ERROR ---")
        print(f"Error type: {type(e).__name__}")
        print(f"Error details: {str(e)}")
        print(f"------------------------")
        return {"answer": f"Oops, my brain is tired right now. Error: {str(e)}"}