#!/usr/bin/env python3
"""
Test script to verify Twilio API integration
Run this to make sure your Twilio credentials are set up correctly
"""

from twilio.rest import Client
from dotenv import load_dotenv
import os

def test_twilio_call():
    """Test making a phone call with Twilio"""
    
    # Load environment variables
    load_dotenv()
    
    # Get credentials from environment
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    twilio_phone_number = os.environ.get("TWILIO_PHONE_NUMBER")
    phone_number = os.environ.get("PHONE_NUMBER")
    
    # Check if all required environment variables are set
    print("🔍 Checking environment variables...")
    print(f"  TWILIO_ACCOUNT_SID: {'✓ Set' if account_sid else '✗ Not set'}")
    print(f"  TWILIO_AUTH_TOKEN: {'✓ Set' if auth_token else '✗ Not set'}")
    print(f"  TWILIO_PHONE_NUMBER: {twilio_phone_number if twilio_phone_number else '✗ Not set'}")
    print(f"  PHONE_NUMBER: {phone_number if phone_number else '✗ Not set'}")
    print()
    
    if not all([account_sid, auth_token, twilio_phone_number, phone_number]):
        print("❌ Error: Missing required environment variables in .env file")
        print("\nPlease add the following to your .env file:")
        print("  TWILIO_ACCOUNT_SID=your_account_sid")
        print("  TWILIO_AUTH_TOKEN=your_auth_token")
        print("  TWILIO_PHONE_NUMBER=+1234567890")
        print("  PHONE_NUMBER=+1234567890")
        return False
    
    try:
        # Initialize Twilio client
        print("📞 Initializing Twilio client...")
        client = Client(account_sid, auth_token)
        print("  ✓ Client initialized successfully\n")
        
        # Make a test call
        print(f"📱 Making test call from {twilio_phone_number} to {phone_number}...")
        print("  (This may take a few seconds...)\n")
        
        call = client.calls.create(
            to=phone_number,
            from_=twilio_phone_number,
            twiml='<Response><Say>This is a test call from your Rizzistant app. Your Twilio integration is working perfectly!</Say></Response>'
        )
        
        print(f"✅ SUCCESS! Phone call initiated successfully!")
        print(f"\nCall Details:")
        print(f"  Call SID: {call.sid}")
        print(f"  Status: {call.status}")
        print(f"  From: {twilio_phone_number}")
        print(f"  To: {phone_number}")
        print(f"\n🎉 Your phone should be ringing now!")
        print(f"\nYou can check the call status at:")
        print(f"  https://console.twilio.com/us1/monitor/logs/calls/{call.sid}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: Failed to make phone call")
        print(f"\nError details: {str(e)}")
        print("\nCommon issues:")
        print("  1. Invalid Twilio credentials (check Account SID and Auth Token)")
        print("  2. Invalid phone numbers (must be in E.164 format, e.g., +1234567890)")
        print("  3. Trial account limitations (can only call verified numbers)")
        print("  4. Insufficient Twilio account balance")
        print("\nCheck your Twilio console at: https://console.twilio.com")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("  TWILIO API INTEGRATION TEST")
    print("=" * 60)
    print()
    
    success = test_twilio_call()
    
    print("\n" + "=" * 60)
    if success:
        print("  ✅ ALL TESTS PASSED - Twilio is ready to use!")
    else:
        print("  ❌ TEST FAILED - Please fix the issues above")
    print("=" * 60)

