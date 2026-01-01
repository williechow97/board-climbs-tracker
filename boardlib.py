import requests
import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

load_dotenv()

# Your BoardLib API details
BOARDLIB_API_URL = "https://api.boardlib.com/v1/climbs"  # Replace with correct endpoint if needed
USER_ID = "specific_user_id"  # Replace with the user ID whose climbs you want to track

# Google Sheets API setup
SHEET_ID = os.getenv('SHEET_ID')  # Sheet ID where you want to update the climbs
RANGE_NAME = 'Climbs!A1'  # The range in your Google Sheet to write to

def get_boardlib_data():
    """Fetch climb data from BoardLib for a specific user"""
    params = {'user_id': USER_ID}
    response = requests.get(BOARDLIB_API_URL, params=params)
    response.raise_for_status()
    return response.json()

def update_google_sheet(data):
    """Update Google Sheets with new climb data"""
    creds = None
    try:
        creds = Credentials.from_service_account_file(
            'credentials.json',  # Path to your credentials.json
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        service = build('sheets', 'v4', credentials=creds)
        
        values = []
        for climb in data['climbs']:
            values.append([climb['date'], climb['route_name'], climb['grade']])

        body = {
            'values': values
        }

        service.spreadsheets().values().append(
            spreadsheetId=SHEET_ID,
            range=RANGE_NAME,
            valueInputOption="RAW",
            body=body
        ).execute()

    except HttpError as err:
        print(f"An error occurred: {err}")

def main():
    try:
        climbs_data = get_boardlib_data()
        update_google_sheet(climbs_data)
        print("Google Sheets updated successfully with new climbs!")
    except Exception as e:
        print(f"Error: {e}")
