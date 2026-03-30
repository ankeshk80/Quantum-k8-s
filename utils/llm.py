import os
import json
import re
import logging
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("k8s-whisperer")

class LLMUtil:
    def __init__(self, model="llama-3.3-70b-versatile"):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = model

    def query(self, system_prompt: str, user_prompt: str) -> str:
        """Query LLM and return raw content"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM Query Failed: {e}")
            return "{}"

    def safe_parse_json(self, text: str) -> dict:
        """Robustly提取 and parse JSON from LLM output"""
        if not text:
            return {}
            
        # Try finding JSON block
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            json_str = match.group()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # Try cleaning it up (sometimes markdown causes issues)
                try:
                    cleaned = re.sub(r"//.*", "", json_str) # Remove comments
                    return json.loads(cleaned)
                except:
                    logger.warning(f"Failed to parse extracted JSON: {json_str[:100]}...")
        
        logger.warning(f"No JSON found in LLM output: {text[:100]}...")
        return {}

llm_service = LLMUtil()
