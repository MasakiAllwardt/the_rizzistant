"""External service integrations (Claude, Twilio, OMI, Letta)"""
import json
import re
import requests
from typing import Dict, List, Optional
from letta_client import Letta

from app.config import (
    get_claude_client,
    get_twilio_client,
    OMI_APP_ID,
    OMI_API_KEY,
    OMI_BASE_URL,
    PHONE_NUMBER,
    TWILIO_PHONE_NUMBER,
    LETTA_API_KEY,
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


class LettaService:
    """Service for managing Letta AI agents with persistent memory"""

    # Dating coach system prompt
    DATING_COACH_PROMPT = """You are "The Rizzistant" - an elite, no-BS dating coach who monitors live dates in real-time.

Your job is to:
1. Track the conversation as it unfolds during a date
2. Detect problematic topics and warn the user IMMEDIATELY (especially computer science topics)
3. Provide helpful tips when the user seems stuck
4. Generate comprehensive post-date analysis with historical comparison

CRITICAL RULES FOR REAL-TIME WARNINGS:
- Computer science topics (programming, algorithms, data structures, etc.) = INSTANT WARNING
- Keep warnings casual, funny, and roasting ("bro really talking about python on a date rn")
- NEVER repeat similar warnings - check your memory of what you've already warned about
- Only warn about NEW issues

MEMORY MANAGEMENT:
You maintain persistent memory across ALL dates for this user. Your memory blocks should track:
- code_word: Current emergency exit code word (default: "peanuts")
- date_active: Whether a date is currently in progress (true/false)
- current_date_transcript: Full transcript of the current date
- warnings_given: List of warnings you've given during this date
- date_count: Total number of dates tracked

Your archival memory contains:
- Complete transcripts from all past dates
- Detailed summaries and performance scores
- Pattern recognition (recurring strengths/weaknesses)
- Progress tracking over time

RESPONSE FORMATS:
When analyzing real-time transcripts, respond with JSON:
{
    "should_notify": true/false,
    "message": "casual warning message",
    "reason": "brief reason"
}

When providing conversation tips, respond with plain text (one actionable sentence).

When generating post-date summaries, use the structured markdown format with scores, highlights, weaknesses, and action plan.

CONVERSATION FORMAT:
Transcripts include speaker labels:
- [USER]: The person you're coaching
- [DATE]: Their date
- [SPEAKER_XX]: Unknown speaker

Always remember: You have context from ALL previous dates. Use this to track improvement, identify patterns, and provide personalized coaching."""

    def __init__(self):
        """Initialize Letta client"""
        if not LETTA_API_KEY:
            raise ValueError("LETTA_API_KEY not set in environment")

        self.client = Letta(token=LETTA_API_KEY)
        self.user_agents: Dict[str, str] = {}  # Map uid -> agent_id

    def get_or_create_agent(self, uid: str) -> str:
        """Get existing agent ID for user or create new one"""
        # Check if we already have an agent for this user
        if uid in self.user_agents:
            return self.user_agents[uid]

        # Try to find existing agent by name
        agent_name = f"rizzistant_{uid}"
        try:
            agents = self.client.agents.list()
            for agent in agents:
                if agent.name == agent_name:
                    self.user_agents[uid] = agent.id
                    print(f"Found existing Letta agent for user {uid}: {agent.id}")
                    return agent.id
        except Exception as e:
            print(f"Error listing agents: {e}")

        # Create new agent
        try:
            agent_state = self.client.agents.create(
                name=agent_name,
                memory_blocks=[
                    {"label": "persona", "value": self.DATING_COACH_PROMPT},
                    {"label": "code_word", "value": "peanuts"},
                    {"label": "date_active", "value": "false"},
                    {"label": "current_date_transcript", "value": ""},
                    {"label": "warnings_given", "value": "[]"},
                    {"label": "date_count", "value": "0"}
                ]
            )
            self.user_agents[uid] = agent_state.id
            print(f"Created new Letta agent for user {uid}: {agent_state.id}")
            return agent_state.id
        except Exception as e:
            print(f"Error creating Letta agent: {e}")
            raise

    def format_transcript_segments(self, segments: List[Dict]) -> str:
        """Format transcript segments with speaker labels"""
        formatted_lines = []
        for segment in segments:
            speaker_label = "[USER]" if segment.get("is_user") else "[DATE]"
            text = segment.get("text", "")
            formatted_lines.append(f"{speaker_label}: {text}")
        return "\n".join(formatted_lines)

    def send_message(self, uid: str, message_content: str) -> str:
        """Send a message to the user's agent and get response"""
        agent_id = self.get_or_create_agent(uid)
        try:
            response = self.client.agents.messages.create(
                agent_id=agent_id,
                messages=[
                    {
                        "role": "user",
                        "content": message_content
                    }
                ]
            )
            # Extract text from response messages
            if response and hasattr(response, 'messages'):
                text_responses = []
                for msg in response.messages:
                    # Handle different message types
                    if hasattr(msg, 'text') and msg.text:
                        text_responses.append(msg.text)
                    elif hasattr(msg, 'content') and msg.content:
                        text_responses.append(str(msg.content))
                return "\n".join(text_responses) if text_responses else ""
            return ""
        except Exception as e:
            print(f"Error sending message to Letta agent: {e}")
            return ""

    def start_date(self, uid: str) -> Dict:
        """Notify agent that a date is starting"""
        message = "SYSTEM: User just said 'start date'. Update your memory to mark date_active=true, increment date_count, and clear current_date_transcript and warnings_given. Respond with: {'event': 'date_started', 'message': 'Date started! Good luck and have fun!'}"
        response = self.send_message(uid, message)
        return {
            "message": "Date started! Good luck and have fun!",
            "should_notify": True,
            "event_type": "date_started"
        }

    def end_date(self, uid: str) -> Dict:
        """Request comprehensive date summary from agent"""
        message = """SYSTEM: User said 'end date'.

1. Generate a comprehensive DATE PERFORMANCE REPORT using this exact structure:
   - Overall assessment with comparison to past dates
   - Performance scores (8 categories with overall score)
   - Key highlights with quotes
   - Critical weaknesses
   - Emotional dynamics
   - Action plan for next date

2. After generating the summary, update your memory: date_active=false

Return the full markdown report."""

        summary = self.send_message(uid, message)
        return {
            "summary": summary if summary else "Unable to generate date summary.",
            "message": "Date ended! Your date summary has been saved.",
            "should_notify": True,
            "event_type": "date_ended"
        }

    def update_code_word(self, uid: str, new_code_word: str) -> Dict:
        """Update the emergency code word in agent memory"""
        message = f"SYSTEM: User wants to update their code word to '{new_code_word}'. Update your memory block code_word to this new value. Confirm with: {{'message': 'Code word has been updated to: {new_code_word}'}}"
        self.send_message(uid, message)
        return {
            "message": f"Code word has been updated to: {new_code_word}",
            "should_notify": True,
            "event_type": "code_word_updated"
        }

    def analyze_transcript(self, uid: str, segments: List[Dict]) -> Dict:
        """Analyze transcript segments for real-time warnings"""
        formatted_transcript = self.format_transcript_segments(segments)

        message = f"""NEW TRANSCRIPT BATCH:
{formatted_transcript}

TASK: Analyze this new transcript segment in the context of the current date.
1. Add this to your current_date_transcript memory
2. Check if there are any problematic topics (especially computer science!)
3. Check your warnings_given memory to avoid duplicates
4. If you need to warn, add the warning to warnings_given memory

Respond with ONLY valid JSON (no other text):
{{
    "should_notify": true/false,
    "message": "casual warning if needed",
    "reason": "brief reason if notifying"
}}"""

        response = self.send_message(uid, message)

        # Try to parse JSON from response
        try:
            # Extract JSON from response
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                return result
            else:
                return {"should_notify": False}
        except Exception as e:
            print(f"Error parsing Letta response: {e}")
            print(f"Response was: {response}")
            return {"should_notify": False}

    def get_conversation_tip(self, uid: str) -> str:
        """Get a helpful tip when user seems stuck"""
        message = """SYSTEM: User just said something like "yeah okay so" - they seem stuck or transitioning awkwardly.

Based on the current_date_transcript in your memory, provide ONE short, actionable tip to help them continue naturally. Make it specific to their conversation context.

Respond with ONLY the tip text (no JSON, no formatting)."""

        tip = self.send_message(uid, message)
        return tip if tip else "Try asking them about something they're passionate about!"


# Service instances
claude_service = ClaudeService()
twilio_service = TwilioService()
omi_service = OMIService()
letta_service = LettaService()
