from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
import uvicorn
from anthropic import Anthropic
import os
from datetime import datetime
from dotenv import load_dotenv
import requests
import json
import sqlite3

# Load environment variables from .env file
load_dotenv()

# Database setup
DB_PATH = "date_summaries.db"

def init_database():
    """Initialize the SQLite database and create the table if it doesn't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS date_summaries (
            uid TEXT PRIMARY KEY,
            summary TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_previous_summary(uid):
    """Retrieve the previous date summary for a user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT summary FROM date_summaries WHERE uid = ?", (uid,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def save_summary(uid, summary):
    """Save or replace the date summary for a user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO date_summaries (uid, summary, created_at)
        VALUES (?, ?, ?)
    """, (uid, summary, datetime.now()))
    conn.commit()
    conn.close()

# Initialize database on startup
init_database()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Claude API client
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

class DateObject:
    def __init__(self, date_id):
        self.date_id = date_id
        self.start_time = datetime.now()
        self.accumulated_transcript = ""
        self.is_active = True
        self.count = 0
        self.end_time = None
        self.previous_warnings = []  # Store previous warnings to avoid repetition

    def add_transcript(self, text):
        """Add text to accumulated transcript"""
        if self.is_active:
            self.accumulated_transcript += " " + text

    def add_warning(self, warning_message, reason):
        """Add a warning to the history"""
        self.previous_warnings.append({
            "message": warning_message,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })

    def finalize(self):
        """Mark this date as ended"""
        self.is_active = False
        self.end_time = datetime.now()

class User:
    def __init__(self, uid):
        self.uid = uid
        self.dates = {}  # Dictionary of date_id -> DateObject
        self.current_date_id = None
        self.date_counter = 0
        self.code_word = "peanuts"  # Default code word

# Dictionary to store user objects
users = {}

def analyze_date_with_claude(current_text, accumulated_transcript, previous_warnings=None):
    """
    Calls Claude API to analyze the date progress and determine if intervention is needed.
    Returns a dict with 'should_notify' (bool) and 'message' (str) if notification needed.
    """
    previous_warnings_text = ""
    if previous_warnings and len(previous_warnings) > 0:
        previous_warnings_text = "\n\nPrevious warnings already sent (DO NOT repeat similar warnings):\n"
        for warning in previous_warnings:
            previous_warnings_text += f"- {warning['reason']}: {warning['message']}\n"

    prompt = f"""You are monitoring a date conversation. Analyze the following transcript and determine if the person is discussing something really wrong that needs urgent changing.

SPECIAL RULE: If they are talking about computer science topics, this is considered a really wrong topic that urgently needs to be changed.

IMPORTANT: You have already sent the warnings listed below. DO NOT send similar or duplicate warnings. Only notify if there is a NEW issue that hasn't been warned about yet.{previous_warnings_text}

Current segment: {current_text}

Full accumulated date transcript so far:
{accumulated_transcript}

Respond ONLY with valid JSON, no other text. Use this exact format:
{{
    "should_notify": true,
    "reason": "brief reason if notification needed",
    "message": "the warning message to send to user if notification needed"
}}

Be strict about computer science topics - any mention of programming, algorithms, data structures, etc. should trigger a notification. However, do NOT send duplicate warnings for issues you've already warned about."""

    try:
        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Parse Claude's response
        import json
        import re
        response_text = message.content[0].text

        # Try to extract JSON from the response
        # Look for JSON object pattern
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            result = json.loads(json_str)
        else:
            # If no JSON found, try parsing the whole response
            result = json.loads(response_text)

        return result
    except Exception as e:
        print(f"Error calling Claude API: {e}")
        print(f"Response text was: {response_text if 'response_text' in locals() else 'N/A'}")
        return {"should_notify": False}

def summarize_date_with_tips(accumulated_transcript, previous_summary=None):
    """
    Calls Claude API to summarize the date and provide tips.
    Returns a string summary with tips for improvement.
    If previous_summary is provided, includes comparison and improvement analysis.
    """
    previous_context = ""
    comparison_note = ""
    improvements_section = ""
    persistent_issues_section = ""

    if previous_summary:
        previous_context = f"""

    PREVIOUS DATE SUMMARY:
    {previous_summary}

    IMPORTANT: Compare this date to the previous one. Highlight specific improvements made,
    areas where the user applied previous advice, and new areas that need attention.
    Be concrete about what changed (better or worse) since the last date."""
        comparison_note = " Explicitly state how this date compares to the previous one (better/worse/similar and why)."
        improvements_section = "\n    - **Improvements from Last Date**: [List specific improvements observed]"
        persistent_issues_section = "\n    - **Persistent Issues**: [Note any problems that carried over from the previous date]"

    prompt = f"""You are an elite dating coach and conversational analyst. Provide a comprehensive, structured report on this date conversation. This is a REPORT ONLY - do not ask any follow-up questions or include prompts for the user to respond.{previous_context}

    Your analysis must follow this EXACT structure:

    # DATE PERFORMANCE REPORT

    ## OVERALL ASSESSMENT
    Provide a 2-3 sentence executive summary of the date's success. Include: chemistry level (strong/moderate/weak), conversational balance (balanced/one-sided), and overall vibe (engaged/surface-level/disconnected).{comparison_note}

    ## PERFORMANCE SCORES

    ### Overall Score: [X.X/10]

    ### Category Breakdown:
    - **Emotional Awareness (20%)**: [X/10] - [One sentence assessment]
    - **Conversational Flow (20%)**: [X/10] - [One sentence assessment]
    - **Authenticity & Presence (15%)**: [X/10] - [One sentence assessment]
    - **Curiosity & Engagement (15%)**: [X/10] - [One sentence assessment]
    - **Confidence (10%)**: [X/10] - [One sentence assessment]
    - **Listening & Responsiveness (10%)**: [X/10] - [One sentence assessment]
    - **Humor & Playfulness (5%)**: [X/10] - [One sentence assessment]
    - **Flirtation & Chemistry (5%)**: [X/10] - [One sentence assessment]

    ## KEY HIGHLIGHTS
    List 3-4 specific moments where you excelled. Include brief quotes from the transcript.
    - [Strength 1]: [Quote or paraphrase]
    - [Strength 2]: [Quote or paraphrase]
    - [Strength 3]: [Quote or paraphrase]{improvements_section}

    ## CRITICAL WEAKNESSES
    List 2-4 specific issues that hurt the connection. Be direct and specific.
    - [Weakness 1]: [Specific example]
    - [Weakness 2]: [Specific example]{persistent_issues_section}

    ## EMOTIONAL DYNAMICS
    Analyze the underlying emotional flow:
    - **Interest Level**: [Their apparent interest - high/moderate/low with evidence]
    - **Power Dynamic**: [Who led the conversation, energy balance]
    - **Tension Points**: [Moments of awkwardness, disconnection, or friction]
    - **Connection Moments**: [Moments of genuine rapport or chemistry]

    ## ACTION PLAN FOR NEXT DATE
    Provide 3 concrete, specific behavioral strategies. NO generic advice.
    1. **[Strategy 1]**: [Specific action with example]
    2. **[Strategy 2]**: [Specific action with example]
    3. **[Strategy 3]**: [Specific action with example]

    CRITICAL RULES:
    - This is a REPORT. Do not include questions for the user.
    - Do not ask "How did you feel about..." or any similar prompts
    - Be direct, honest, and specific with examples
    - Use actual quotes from the transcript when highlighting moments
    - Keep each section concise but informative
    - Focus on actionable insights, not platitudes

    Date transcript:
    {accumulated_transcript}"""

    try:
        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=2048,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        summary = message.content[0].text
        return summary
    except Exception as e:
        print(f"Error calling Claude API for summary: {e}")
        return "Unable to generate date summary."

def create_omi_memory(user_id, summary):
    """
    Creates a memory in OMI using the Import API.
    """
    app_id = os.environ.get("OMI_APP_ID")
    api_key = os.environ.get("OMI_API_KEY")

    url = f"https://api.omi.me/v2/integrations/{app_id}/user/memories?uid={user_id}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "text": summary,  # Top-level text field required by API
        "memories": [
            {
                "content": summary,  # Use "content" instead of "text"
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

@app.post("/webhook")
def webhook(memory: dict, uid: str):
    print(memory)
    print(uid)
    return {"message": "we got it"}


@app.post("/livetranscript")
def livetranscript(transcript: dict, uid: str):
    # Create user object if not seen before
    if uid not in users:
        users[uid] = User(uid)

    user = users[uid]

    print(f"Received {len(transcript['segments'])} segments in this request")

    # First pass: check for start/end date commands and code word
    for segment in transcript["segments"]:
        text = segment["text"]
        text_lower = text.lower()

        # Check for "omi edit code word" command
        if "edit code word" in text_lower:
            # Extract the next word after "edit code word"
            parts = text_lower.split("edit code word")
            if len(parts) > 1 and parts[1].strip():
                # Get the next word after the phrase
                remaining_text = parts[1].strip()
                words = remaining_text.split()
                if len(words) > 0:
                    new_code_word = words[0]
                    user.code_word = new_code_word
                    print(f"Updated code word for user {uid} to: {new_code_word}")
                    return {
                        "message": f"Code word has been updated to: {new_code_word}",
                        "should_notify": True,
                        "event_type": "code_word_updated"
                    }

        # Check if code word is said
        if user.code_word.lower() in text_lower:
            print(f"Code word '{user.code_word}' detected for user {uid}")
            return {
                "message": "YOU HAVE A PHONE CALL",
                "should_notify": True,
                "event_type": "code_word_detected"
            }

        # Check if "start date" is said
        if "start date" in text_lower:
            print(f"Starting new date for user {uid}")
            # Create new date object
            user.date_counter += 1
            date_id = f"date_{user.date_counter}"
            user.dates[date_id] = DateObject(date_id)
            user.current_date_id = date_id

            return {
                "message": "Date started! Good luck and have fun!",
                "should_notify": True,
                "event_type": "date_started"
            }

        # Check if "end date" is said
        if "end date" in text_lower:
            print(f"Ending date for user {uid}")
            if user.current_date_id and user.current_date_id in user.dates:
                current_date = user.dates[user.current_date_id]
                current_date.finalize()

                # Generate summary with tips using Claude
                if current_date.accumulated_transcript.strip():
                    # Retrieve previous summary from database
                    previous_summary = get_previous_summary(uid)

                    # Generate new summary with comparison to previous date
                    summary = summarize_date_with_tips(
                        current_date.accumulated_transcript,
                        previous_summary=previous_summary
                    )
                    print(f"Generated date summary for user {uid}")

                    if previous_summary:
                        print(f"Compared with previous date and noted improvements")

                    # Save new summary to database (replaces previous one automatically)
                    save_summary(uid, summary)
                    print(f"Saved new summary to database for user {uid}")

                    # Create memory in OMI
                    create_omi_memory(uid, summary)

                user.current_date_id = None

                return {
                    "message": "Date ended! Your date summary has been saved.",
                    "should_notify": True,
                    "event_type": "date_ended"
                }

    # If we're in an active date, concatenate all segments and analyze once
    if user.current_date_id and user.current_date_id in user.dates:
        current_date = user.dates[user.current_date_id]

        if current_date.is_active:
            # Concatenate all segment texts
            concatenated_text = " ".join([segment["text"] for segment in transcript["segments"]])

            if concatenated_text.strip():
                current_date.count += 1
                # Add to accumulated transcript
                print(f"got transcript batch {current_date.count}")
                current_date.add_transcript(concatenated_text)

                # Analyze with Claude API once, passing previous warnings
                analysis = analyze_date_with_claude(
                    concatenated_text,
                    current_date.accumulated_transcript,
                    current_date.previous_warnings
                )
                print(f"analyzed batch {current_date.count}")

                # If Claude recommends notification, return warning and save it
                if analysis.get("should_notify", False):
                    warning_message = analysis.get("message", "Please change the topic!")
                    reason = analysis.get("reason", "")

                    # Save this warning to prevent repetition
                    current_date.add_warning(warning_message, reason)

                    return {
                        "message": warning_message,
                        "reason": reason,
                        "should_notify": True
                    }

    return {"message": "transcript processed", "should_notify": False}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
