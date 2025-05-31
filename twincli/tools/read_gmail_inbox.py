
# twincli/tools/read_gmail_inbox.py
"""
Reads emails from Gmail inbox using the Gmail API.

Category: communication
Created: 2025-05-30
"""

import json
import os
from typing import Optional, List

# --- IMPORTANT SETUP FOR GMAIL API ---
# This tool requires Google API Client Library for Python and OAuth 2.0 credentials.
# You need to:
# 1. Go to Google Cloud Console: https://console.developers.google.com/
# 2. Create a new project or select an existing one.
# 3. Enable the Gmail API for your project.
# 4. Go to "Credentials" -> "OAuth consent screen" and configure it.
# 5. Go to "Credentials" -> "Create Credentials" -> "OAuth client ID".
# 6. Select "Desktop app" and create the client ID.
# 7. Download the `credentials.json` file and place it in a known location (e.g., in your TwinCLI project root or a dedicated config folder).
# 8. The first time you run a Gmail API call, it will open a browser for authentication.
#    After successful authentication, a `token.json` file will be created in the same directory as `credentials.json`.
#    This `token.json` stores your access and refresh tokens and will be used for subsequent calls.
#
# Replace 'YOUR_CREDENTIALS_PATH' below with the actual path to your credentials.json file.
# Example: CREDENTIALS_FILE = os.path.join(os.path.expanduser('~'), '.twincli', 'gmail_credentials.json')
# For simplicity in this template, we assume it's in the current working directory or a specified path.
# You might want to make this configurable by the user or a TwinCLI setting.

# from google.oauth2.credentials import Credentials
# from google_auth_oauthlib.flow import InstalledAppFlow
# from google.auth.transport.requests import Request
# from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
# SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# def get_gmail_service(credentials_path: str = 'credentials.json'):
#     creds = None
#     token_path = os.path.join(os.path.dirname(credentials_path), 'token.json')
#     
#     if os.path.exists(token_path):
#         creds = Credentials.from_authorized_user_file(token_path, SCOPES)
#     
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
#             creds = flow.run_local_server(port=0)
#         with open(token_path, 'w') as token:
#             token.write(creds.to_json())
#     
#     return build('gmail', 'v1', credentials=creds)

def read_gmail_inbox(max_results: Optional[int] = 10, query: Optional[str] = None) -> str:
    """
    Reads emails from the Gmail inbox.
    
    Args:
        max_results: The maximum number of emails to retrieve. Defaults to 10.
        query: A Gmail API query string to filter emails (e.g., "is:unread from:example.com").
        
    Returns:
        A JSON string containing a list of email details (sender, subject, snippet) or an error message.
    """
    try:
        # Placeholder for actual Gmail API call.
        # Requires 'google-api-python-client' and 'google-auth-oauthlib' libraries.
        # You need to manually install these: pip install google-api-python-client google-auth-oauthlib

        # Example of how the logic would roughly look (commented out due to external library dependency):
        # service = get_gmail_service()
        # results = service.users().messages().list(userId='me', maxResults=max_results, q=query).execute()
        # messages = results.get('messages', [])
        #
        # emails = []
        # if messages:
        #     for message in messages:
        #         msg = service.users().messages().get(userId='me', id=message['id'], format='metadata').execute()
        #         headers = msg['payload']['headers']
        #         subject = next((header['value'] for header in headers if header['name'] == 'Subject'), 'No Subject')
        #         sender = next((header['value'] for header in headers if header['name'] == 'From'), 'Unknown Sender')
        #         snippet = msg.get('snippet', 'No snippet available.')
        #         emails.append({'id': message['id'], 'sender': sender, 'subject': subject, 'snippet': snippet})
        #
        # return json.dumps({"status": "success", "emails": emails})

        return json.dumps({
            "status": "warning",
            "message": "Gmail API functionality is a placeholder. You need to manually set up OAuth 2.0 and install required libraries (google-api-python-client, google-auth-oauthlib) to enable reading emails.",
            "details": {
                "max_results": max_results,
                "query": query if query else "None"
            }
        })

    except Exception as e:
        return json.dumps({"status": "error", "message": f"An unexpected error occurred: {e}"})

# Tool registration for TwinCLI
read_gmail_inbox_metadata = {
    "function": read_gmail_inbox,
    "name": "read_gmail_inbox",
    "description": "Reads emails from Gmail inbox. Requires external setup for OAuth 2.0 authentication and dependencies (google-api-python-client, google-auth-oauthlib).",
    "category": "communication",
    "parameters": {
        "type": "object",
        "properties": {
            "max_results": {
                "type": "integer",
                "description": "The maximum number of emails to retrieve. Defaults to 10."
            },
            "query": {
                "type": "string",
                "description": "A Gmail API query string to filter emails (e.g., 'is:unread from:example.com')."
            }
        },
        "required": []
    }
}
