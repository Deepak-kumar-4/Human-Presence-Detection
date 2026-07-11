import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

def send_sms():
    # Twilio credentials
    account_sid = os.environ["TWILIO_ACCOUNT_SID"]
    auth_token = os.environ["TWILIO_AUTH_TOKEN"]
    twilio_phone_number = os.environ["TWILIO_PHONE_NUMBER"]

    # List of recipient phone numbers in E.164 format
    recipient_phone_numbers = os.environ["SMS_RECIPIENTS"].split(",")

    # Initialize the Twilio Client
    client = Client(account_sid, auth_token)

    # Message to be sent
    message_body = "WARNING⚠️ \nHuman presence has been detected in the CCTV!"

    # Loop through the list of recipient numbers and send the message to each
    for recipient_phone_number in recipient_phone_numbers:
        try:
            message = client.messages.create(
                body=message_body,
                from_=twilio_phone_number,
                to=recipient_phone_number
            )
            print(f"Message sent successfully to {recipient_phone_number}. SID: {message.sid}")
        except Exception as e:
            print(f"Failed to send message to {recipient_phone_number}: {e}")
