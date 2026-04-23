import resend
from dotenv import load_dotenv
import os

# This line loads .env file
load_dotenv()

resend.api_key = os.environ["RESEND_API_KEY"]

response = resend.Emails.send({
    "from": "onboarding@resend.dev",
    "to": ["zumihibet2@gmail.com"],
    "subject": "Test Email",
    "html": "<p>This is a test</p>"
})

print(response)