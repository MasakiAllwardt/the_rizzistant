"""External service integrations (Claude, Twilio, OMI)"""
import json
import re
import requests
from typing import Dict, List, Optional

from app.config import (
    get_claude_client,
    get_twilio_client,
    OMI_APP_ID,
    OMI_API_KEY,
    OMI_BASE_URL,
    PHONE_NUMBER,
    TWILIO_PHONE_NUMBER,
)
from app.prompts import (
    build_date_analysis_prompt,
    build_conversation_tip_prompt,
    build_date_summary_prompt,
)


class ClaudeService:
    """Service for interacting with Claude API"""

    def __init__(self):
        self.client = get_claude_client()
        self.model = "claude-3-5-haiku-20241022"

    def analyze_date(
        self,
        current_text: str,
        accumulated_transcript: str,
        previous_warnings: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Analyze the date progress and determine if intervention is needed.
        Returns a dict with 'should_notify' (bool) and 'message' (str) if notification needed.
        """
        prompt = build_date_analysis_prompt(
            current_text,
            accumulated_transcript,
            previous_warnings
        )

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text

            # Try to extract JSON from the response
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)
            else:
                result = json.loads(response_text)

            return result
        except Exception as e:
            print(f"Error calling Claude API: {e}")
            print(f"Response text was: {response_text if 'response_text' in locals() else 'N/A'}")
            return {"should_notify": False}

    def generate_conversation_tip(self, accumulated_transcript: str) -> str:
        """
        Generate a helpful conversation tip when the user seems stuck.
        Returns a string with a helpful tip to continue the conversation.
        """
        prompt = build_conversation_tip_prompt(accumulated_transcript)

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}]
            )

            tip = message.content[0].text.strip()
            return tip
        except Exception as e:
            print(f"Error calling Claude API for conversation tip: {e}")
            return "Try asking them about something they're passionate about!"

    def summarize_date(
        self,
        accumulated_transcript: str,
        previous_summary: Optional[str] = None
    ) -> str:
        """
        Summarize the date and provide tips for improvement.
        Returns a string summary with tips.
        """
        prompt = build_date_summary_prompt(accumulated_transcript, previous_summary)

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )

            summary = message.content[0].text
            return summary
        except Exception as e:
            print(f"Error calling Claude API for summary: {e}")
            return "Unable to generate date summary."


class TwilioService:
    """Service for making phone calls via Twilio"""

    def __init__(self):
        self.client = get_twilio_client()

    def make_emergency_call(self) -> bool:
        """Make an emergency phone call using Twilio when code word is detected"""
        try:
            if not PHONE_NUMBER or not TWILIO_PHONE_NUMBER:
                print("Error: PHONE_NUMBER or TWILIO_PHONE_NUMBER not set in environment")
                return False

            call = self.client.calls.create(
                to=PHONE_NUMBER,
                from_=TWILIO_PHONE_NUMBER,
                twiml='<Response><Say>You have an urgent phone call. This is your emergency exit.</Say></Response>'
            )

            print(f"Phone call initiated successfully. Call SID: {call.sid}")
            return True
        except Exception as e:
            print(f"Error making phone call: {e}")
            return False


class OMIService:
    """Service for creating memories in OMI"""

    def create_memory(self, user_id: str, summary: str) -> bool:
        """Create a memory in OMI using the Import API"""
        if not OMI_APP_ID or not OMI_API_KEY:
            print("Error: OMI_APP_ID or OMI_API_KEY not set in environment")
            return False

        url = f"{OMI_BASE_URL}/integrations/{OMI_APP_ID}/user/memories?uid={user_id}"

        headers = {
            "Authorization": f"Bearer {OMI_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "text": summary,
            "memories": [
                {
                    "content": summary,
                    "tags": ["date", "dating-coach", "summary"]
                }
            ]
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            print(f"Successfully created OMI memory for user {user_id}")
            return True
        except Exception as e:
            print(f"Error creating OMI memory: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return False


# Service instances
claude_service = ClaudeService()
twilio_service = TwilioService()
omi_service = OMIService()
