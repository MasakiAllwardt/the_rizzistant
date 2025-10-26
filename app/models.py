"""Data models for users and dates"""
from datetime import datetime
from typing import Dict, List, Optional


class DateObject:
    """Represents a single date session"""

    def __init__(self, date_id: str):
        self.date_id = date_id
        self.start_time = datetime.now()
        self.accumulated_transcript = ""
        self.is_active = True
        self.count = 0
        self.end_time = None
        self.previous_warnings: List[Dict] = []  # Store previous warnings to avoid repetition

    def add_transcript(self, text: str):
        """Add text to accumulated transcript"""
        if self.is_active:
            self.accumulated_transcript += " " + text

    def add_warning(self, warning_message: str, reason: str):
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
    """Represents a user with their date history"""

    def __init__(self, uid: str):
        self.uid = uid
        self.dates: Dict[str, DateObject] = {}  # Dictionary of date_id -> DateObject
        self.current_date_id: Optional[str] = None
        self.date_counter = 0
        self.code_word = "peanuts"  # Default code word
        self.phone_number: Optional[str] = None  # User's phone number


# In-memory storage for user objects
users: Dict[str, User] = {}


def get_or_create_user(uid: str) -> User:
    """Get existing user or create new one"""
    if uid not in users:
        users[uid] = User(uid)
    return users[uid]
