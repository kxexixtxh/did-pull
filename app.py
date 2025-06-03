from flask import Flask, request, render_template_string
from atproto import Client
from atproto.exceptions import AtProtocolError
import gspread
from google.oauth2.service_account import Credentials

# Google Sheets setup
SERVICE_ACCOUNT_FILE = r'C:\Users\Keith\Documents\Projects\DID\elite-crossbar-461504-j0-1a24652891fd.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gs_client = gspread.authorize(creds)

spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1tl4vgQGSV5HO2m9C9BO76Ob4vNh9LGz1Qs_7Ql2VqPw/edit?gid=0#gid=0'
sheet = gs_client.open_by_url(spreadsheet_url).worksheet('Sheet1')

# Bluesky client
client = Client()

app = Flask(__name__)

FORM_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>DID Resolver</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      background: #f4f6f8;
      padding: 40px;
      display: flex;
      justify-content: center;
    }
    .container {
      background: white;
      padding: 25px 40px 40px 40px;
      border-radius: 8px;
      box-shadow: 0 4px 15px rgba(0,0,0,0.1);
      max-width: 480px;
      width: 100%;
    }
    h2 {
      margin-bottom: 20px;
      color: #2c3e50;
      text-align: center;
    }
    label {
      font-weight: bold;
      display: block;
      margin-top: 15px;
      margin-bottom: 5px;
      color: #34495e;
    }
    input[type="text"] {
      width: 100%;
      padding: 10px;
      border: 1.8px solid #ddd;
      border-radius: 5px;
      font-size: 1em;
      transition: border-color 0.3s ease;
    }
    input[type="text"]:focus {
      border-color: #2980b9;
      outline: none;
    }
    input[type="submit"] {
      margin-top: 25px;
      width: 100%;
      padding: 12px;
      font-size: 1.1em;
      background-color: #2980b9;
      border: none;
      border-radius: 6px;
      color: white;
      cursor: pointer;
      transition: background-color 0.3s ease;
    }
    input[type="submit"]:hover {
      background-color: #1c5980;
    }
    p {
      font-size: 1em;
      margin-top: 20px;
      text-align: center;
    }
    p.error {
      color: #e74c3c;
    }
    p.success {
      color: #27ae60;
    }
    p.warning {
      color: #f39c12;
    }
    .result {
      margin-top: 30px;
      background: #ecf0f1;
      padding: 20px;
      border-radius: 6px;
      color: #2c3e50;
      font-weight: 600;
    }
  </style>
</head>
<body>
  <div class="container">
    <h2>Bluesky DID Lookup</h2>
    <form method="POST">
      <label for="handle">Enter username or full handle:</label>
      <input type="text" id="handle" name="handle" value="{{request.form.get('handle', '')}}" required>

      <label for="zendesk">Zendesk link (optional):</label>
      <input type="text" id="zendesk" name="zendesk" value="{{request.form.get('zendesk', '')}}">

      <input type="submit" value="Resolve DID">
    </form>

    {% if error %}
      <p class="error">Error: {{ error }}</p>
    {% endif %}

    {% if did %}
      <div class="result">
        <p><strong>DID:</strong> {{ did }}</p>
        <p><strong>Handle:</strong> {{ handle_with_at }}</p>
        {% if added %}
          <p class="success">✅ Added to Google Sheet.</p>
        {% else %}
          <p class="warning">⚠️ Already exists in Google Sheet. Not added.</p>
        {% endif %}
      </div>
    {% endif %}
  </div>
</body>
</html>
"""

def get_next_available_row(col_letter):
    col_values = sheet.col_values(ord(col_letter.upper()) - 64)
    return len(col_values) + 1

@app.route("/", methods=["GET", "POST"])
def index():
    did = None
    error = None
    handle_with_at = None
    added = False

    if request.method == "POST":
        raw_handle = request.form.get("handle", "").strip().lower()
        zendesk_link = request.form.get("zendesk", "").strip()

        if not raw_handle:
            error = "Please enter a handle."
        else:
            if '.' not in raw_handle:
                handle = f"{raw_handle}.bsky.social"
            else:
                handle = raw_handle

            try:
                response = client.com.atproto.identity.resolve_handle({"handle": handle})
                did = response.did
                handle_with_at = handle if handle.startswith("@") else "@" + handle

                existing_dids = sheet.col_values(2)  # Column B
                existing_handles = sheet.col_values(3)  # Column C

                if did in existing_dids or handle_with_at in existing_handles:
                    added = False
                else:
                    target_row = get_next_available_row('B')
                    sheet.update(f'B{target_row}', [[did]])
                    sheet.update(f'C{target_row}', [[handle_with_at]])
                    if zendesk_link:
                        sheet.update(f'L{target_row}', [[zendesk_link]])
                    added = True

            except AtProtocolError:
                error = "User handle not found."
            except Exception as e:
                error = f"Unexpected error: {e}"

    return render_template_string(FORM_HTML, did=did, error=error, handle_with_at=handle_with_at, added=added, request=request)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
