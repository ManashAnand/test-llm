from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=".env.local", override=True)

openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
async_openai_client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
