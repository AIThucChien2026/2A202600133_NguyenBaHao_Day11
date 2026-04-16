import os
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()

# Model configuration
MODEL_LLM = "gemini-3.1-flash-lite-preview"

# Gemini API Key configuration
def setup_api_key():
    # Support multiple common naming conventions
    api_key = (
        os.getenv("API_GEMINI")
        or os.getenv("GOOGLE_API_KEY")
        or os.getenv("GEMINI_API_KEY")
    )
    
    if not api_key:
        raise ValueError(
            "API Key (API_GEMINI or GOOGLE_API_KEY) not found in environment variables. Please check your .env file."
        )

    os.environ["GOOGLE_API_KEY"] = api_key
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "0"
    print(f"API key loaded successfully (Starts with: {api_key[:5]}...)")


# Banking topics
ALLOWED_TOPICS = [
    "banking",
    "account",
    "transaction",
    "transfer",
    "loan",
    "interest",
    "savings",
    "credit",
    "deposit",
    "withdrawal",
    "balance",
    "payment",
    "tai khoan",
    "giao dich",
    "tiet kiem",
    "lai suat",
    "chuyen tien",
    "the tin dung",
    "so du",
    "vay",
    "ngan bank",
    "atm",
]

BLOCKED_TOPICS = [
    "hack",
    "exploit",
    "weapon",
    "drug",
    "illegal",
    "violence",
    "gambling",
]
