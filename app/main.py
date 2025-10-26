"""FastAPI application and route handlers"""
import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_database
from app.services import letta_service, twilio_service, omi_service


# Initialize database on startup
init_database()

# Create FastAPI app
app = FastAPI(title="The Rizzistant", description="Real-time Dating Coach")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get('/')
def root():
    """Health check endpoint"""
    return {"message": "Rizz Meter API - Live Conversation Coaching"}


@app.post("/webhook")
def webhook(memory: dict, uid: str):
    """Webhook endpoint for receiving memories"""
    print(memory)
    print(uid)
    return {"message": "we got it"}


@app.post("/livetranscript")
def livetranscript(transcript: dict, uid: str):
    """
    Process live transcript segments from the user.
    Handles commands (start date, end date, code word) and analyzes conversation.
    Now powered by Letta AI for stateful, persistent memory across all dates.
    """
    segments = transcript.get("segments", [])
    print(f"Received {len(segments)} segments for user {uid}")

    if not segments:
        return {"message": "No segments received", "should_notify": False}

    # Check for commands in any segment
    for segment in segments:
        text = segment.get("text", "")
        text_lower = text.lower()

        # Check for "edit code word" command
        if "edit code word" in text_lower:
            parts = text_lower.split("edit code word")
            if len(parts) > 1 and parts[1].strip():
                remaining_text = parts[1].strip()
                words = remaining_text.split()
                if len(words) > 0:
                    new_code_word = words[0]
                    print(f"Updating code word for user {uid} to: {new_code_word}")
                    return letta_service.update_code_word(uid, new_code_word)

        # Check for "start date" command
        if "start date" in text_lower:
            print(f"Starting new date for user {uid}")
            return letta_service.start_date(uid)

        # Check for "end date" command
        if "end date" in text_lower:
            print(f"Ending date for user {uid}")
            result = letta_service.end_date(uid)
            summary = result.get("summary", "")

            # Send summary to OMI
            if summary:
                omi_service.create_memory(uid, summary)

            return result

        # Check for code word (emergency exit)
        # Note: We need to get the code word from Letta agent's memory
        # For now, check common code word "peanuts" - could enhance this
        if "peanuts" in text_lower or "code word" in text_lower:
            print(f"Potential code word detected for user {uid}")

            # Make emergency phone call
            twilio_service.make_emergency_call()

            # End the date and get summary
            result = letta_service.end_date(uid)
            summary = result.get("summary", "")

            # Send to OMI
            if summary:
                omi_service.create_memory(uid, summary)

            return {
                "message": "Emergency exit activated! Your date summary has been saved.",
                "should_notify": True,
                "event_type": "emergency_exit"
            }

    # No commands detected - analyze the conversation with Letta
    # Check for "yeah okay so" phrase (user seems stuck)
    concatenated_text = " ".join([s.get("text", "") for s in segments])
    text_normalized = re.sub(r'[^\w\s]', '', concatenated_text.lower())

    if "yeah okay so" in text_normalized:
        print(f"Detected 'yeah okay so' - getting conversation tip from Letta")
        tip = letta_service.get_conversation_tip(uid)
        return {
            "message": tip,
            "should_notify": True,
            "event_type": "conversation_tip"
        }

    # Regular conversation analysis - let Letta decide if warning is needed
    print(f"Analyzing transcript segments with Letta for user {uid}")
    analysis = letta_service.analyze_transcript(uid, segments)

    if analysis.get("should_notify", False):
        print(f"Letta recommends intervention: {analysis.get('reason', 'No reason provided')}")
        return {
            "message": analysis.get("message", "Please change the topic!"),
            "reason": analysis.get("reason", ""),
            "should_notify": True,
            "event_type": "warning"
        }

    # No intervention needed
    return {"message": "Transcript processed", "should_notify": False}
