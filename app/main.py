"""FastAPI application and route handlers"""
import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_database
from app.models import get_or_create_user, DateObject
from app.services import claude_service, twilio_service, omi_service, letta_service


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
    """
    # Get or create user
    user = get_or_create_user(uid)

    print(f"Received {len(transcript['segments'])} segments in this request")

    # First pass: check for start/end date commands and code word
    for segment in transcript["segments"]:
        text = segment["text"]
        text_lower = text.lower()

        # Check for "omi edit code word" command
        if "edit code word" in text_lower:
            parts = text_lower.split("edit code word")
            if len(parts) > 1 and parts[1].strip():
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

        # Check if code word is said (emergency exit)
        if user.code_word.lower() in text_lower:
            print(f"Code word '{user.code_word}' detected for user {uid}")

            # Make the emergency phone call
            twilio_service.make_emergency_call()

            # End the date if active
            if user.current_date_id and user.current_date_id in user.dates:
                current_date = user.dates[user.current_date_id]
                current_date.finalize()

                # Generate summary with tips using Letta
                if current_date.accumulated_transcript.strip():
                    # Use Letta agent to generate summary with full historical context
                    # Letta automatically has access to all previous dates via its memory
                    summary = letta_service.process_date_end(
                        uid,
                        current_date.accumulated_transcript
                    )
                    print(f"Generated date summary for user {uid} via Letta")

                    # Send to OMI for external memory storage
                    omi_service.create_memory(uid, summary)

                user.current_date_id = None

            return {
                "message": "Date ended! Your date summary has been saved.",
                "should_notify": True,
                "event_type": "date_ended"
            }

        # Check if "start date" is said
        if "start date" in text_lower:
            print(f"Starting new date for user {uid}")
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

                # Generate summary with tips using Letta
                if current_date.accumulated_transcript.strip():
                    # Use Letta agent to generate summary with full historical context
                    # Letta automatically has access to all previous dates via its memory
                    summary = letta_service.process_date_end(
                        uid,
                        current_date.accumulated_transcript
                    )
                    print(f"Generated date summary for user {uid} via Letta")

                    # Send to OMI for external memory storage
                    print(f"Sending summary to OMI: {summary}")
                    omi_service.create_memory(uid, summary)

                user.current_date_id = None

                return {
                    "message": "Date ended! Your date summary has been saved.",
                    "should_notify": True,
                    "event_type": "date_ended"
                }

    # If we're in an active date, analyze the conversation
    if user.current_date_id and user.current_date_id in user.dates:
        current_date = user.dates[user.current_date_id]

        if current_date.is_active:
            # Concatenate all segment texts
            concatenated_text = " ".join([segment["text"] for segment in transcript["segments"]])

            if concatenated_text.strip():
                current_date.count += 1
                print(f"got transcript batch {current_date.count}")

                # Add to accumulated transcript
                current_date.add_transcript(concatenated_text)

                # Check for "yeah okay so" phrase (user seems stuck)
                text_normalized = re.sub(r'[^\w\s]', '', concatenated_text.lower())
                if "yeah okay so" in text_normalized:
                    print(f"Detected 'yeah okay so' - generating conversation tip")
                    tip = claude_service.generate_conversation_tip(
                        current_date.accumulated_transcript
                    )
                    return {
                        "message": tip,
                        "should_notify": True,
                        "event_type": "conversation_tip"
                    }

                # Analyze conversation with Claude
                analysis = claude_service.analyze_date(
                    concatenated_text,
                    current_date.accumulated_transcript,
                    current_date.previous_warnings
                )
                print(f"analyzed batch {current_date.count}")

                # If intervention is needed, send warning
                if analysis.get("should_notify", False):
                    warning_message = analysis.get("message", "Please change the topic!")
                    reason = analysis.get("reason", "")

                    # Save warning to prevent repetition
                    current_date.add_warning(warning_message, reason)

                    return {
                        "message": warning_message,
                        "reason": reason,
                        "should_notify": True
                    }

    # return {"message": "transcript processed", "should_notify": False}
