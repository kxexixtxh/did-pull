from atproto import Client                     # Import Bluesky API client
from atproto.exceptions import AtProtocolError # Import error type for handling API errors

import gspread                                  # Import library to work with Google Sheets
from google.oauth2.service_account import Credentials  # Import Google auth for service accounts

SERVICE_ACCOUNT_FILE = r'C:\Users\Keith\Documents\Projects\DID\elite-crossbar-461504-j0-1a24652891fd.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gs_client = gspread.authorize(creds)

spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1tl4vgQGSV5HO2m9C9BO76Ob4vNh9LGz1Qs_7Ql2VqPw/edit?gid=0#gid=0'
sheet = gs_client.open_by_url(spreadsheet_url).worksheet('Sheet1')

client = Client()

def get_next_available_row(col_letter):
    col_values = sheet.col_values(ord(col_letter.upper()) - 64)
    return len(col_values) + 1

def resolve_user():
    while True:
        raw_input = input("\nEnter the username or full handle (or 'q' to quit): ").lower().strip()

        if raw_input in ['q', 'quit', 'exit']:
            print("\nGoodbye!")
            break

        if not raw_input:
            print("No input provided. Please try again.")
            continue

        if '.' not in raw_input:
            print("\nYou entered a name without a domain.")
            domain_type = input("Is this a (1) bsky.social handle or (2) a custom domain? Enter 1 or 2: ").strip()

            if domain_type == '1':
                handle = f"{raw_input}.bsky.social"
            elif domain_type == '2':
                handle = input("Please enter the full custom domain handle (e.g., customdomain.xyz): ").strip()
                if not handle:
                    print("No domain entered. Try again.")
                    continue
            else:
                print("Invalid choice. Please enter 1 or 2.")
                continue
        else:
            handle = raw_input

        try:
            response = client.com.atproto.identity.resolve_handle({'handle': handle})
            did = response['did']

            handle_with_at = handle if handle.startswith("@") else "@" + handle
            zendesk_link = input("Enter Zendesk link (or leave blank if none): ").strip()

            # CONFIRMATION STEP
            print("\nPlease confirm the details:")
            print(f"DID: {did}")
            print(f"Handle: {handle_with_at}")
            print(f"Zendesk link: {zendesk_link if zendesk_link else '(none)'}")

            confirm = input("Are these details correct? (y/n): ").lower().strip()
            if confirm != 'y':
                print("Details not confirmed. Please enter details again.")
                continue

            # DUPLICATE CHECK
            existing_dids = sheet.col_values(2)  # Column B
            existing_handles = sheet.col_values(3)  # Column C

            if did in existing_dids:
                print(f"⚠️ DID '{did}' already exists in the sheet. Skipping entry.")
                continue

            if handle_with_at in existing_handles:
                print(f"⚠️ Handle '{handle_with_at}' already exists in the List of compromised/hacked accounts sheet. Skipping entry.")
                continue

            target_row = get_next_available_row('B')

            sheet.update(range_name=f'B{target_row}', values=[[did]])
            sheet.update(range_name=f'C{target_row}', values=[[handle_with_at]])
            if zendesk_link:
                sheet.update(range_name=f'L{target_row}', values=[[zendesk_link]])

            print(f"✅ Added to row {target_row} in Google Sheet.")

            another = input("\nSearch another account? (y = yes, n/q = no): ").lower().strip()
            if another not in ['y', 'yes', '']:
                print("\nGoodbye!")
                break

        except AtProtocolError:
            print(f"\n❌ Could not find a user with handle: '{handle}'. Please try again.")
        except Exception as e:
            print(f"\n⚠️ Unexpected error: {e}")

if __name__ == "__main__":
    resolve_user()
