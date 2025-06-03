from flask import Flask, request, jsonify
from atproto import Client
from atproto.exceptions import AtProtocolError

import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# Google Sheets setup
SERVICE_ACCOUNT_FILE = 'elite-crossbar-461504-j0-1a24652891fd.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gs_client = gspread.authorize(creds)

spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1tl4vgQGSV5HO2m9C9BO76Ob4vNh9LGz1Qs_7Ql2VqPw/edit#gid=0'
sheet = gs_client.open_by_url(spreadsheet_url).worksheet('Sheet1')

client = Client()

def get_next_available_row(col_letter):
    col_values = sheet.col_values(ord(col_letter.upper()) - 64)
    return len(col_values) + 1

@app.route("/resolve", methods=["GET"])
def resolve():
    handle = request.args.get("handle")
    zendesk_link = request.args.get("zendesk", "")

    if not handle:
        return jsonify({"error": "Missing handle"}), 400

    # Add domain if missing
    if '.' not in handle:
        domain_type = request.args.get("domain_type")  # '1' for bsky, '2' for custom
        if domain_type == '1':
            handle += ".bsky.social"
        elif domain_type == '2':
            return jsonify({"error": "Custom domain not provided"}), 400
        else:
            return jsonify({"error": "Invalid domain type"}), 400

    try:
        response = client.com.atproto.identity.resolve_handle({'handle': handle})
        did = response['did']
        handle_with_at = handle if handle.startswith("@") else "@" + handle

        # Check for duplicates
        existing_dids = sheet.col_values(2)  # Column B
        existing_handles = sheet.col_values(3)  # Column C

        if did in existing_dids or handle_with_at in existing_handles:
            return jsonify({"warning": "Duplicate entry", "did": did, "handle": handle_with_at}), 409

        row = get_next_available_row('B')
        sheet.update(f'B{row}', [[did]])
        sheet.update(f'C{row}', [[handle_with_at]])
        if zendesk_link:
            sheet.update(f'L{row}', [[zendesk_link]])

        return jsonify({
            "success": True,
            "row": row,
            "did": did,
            "handle": handle_with_at,
            "zendesk_link": zendesk_link or None
        })

    except AtProtocolError:
        return jsonify({"error": f"User not found for handle: {handle}"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
