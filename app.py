from flask import Flask, request, render_template_string
from atproto import Client
from atproto.exceptions import AtProtocolError

app = Flask(__name__)
client = Client()

FORM_HTML = '''
  <h2>Enter Bluesky handle to get DID</h2>
  <form method="post">
    Handle: <input name="handle" required>
    <button type="submit">Get DID</button>
  </form>

  {% if error %}
    <p style="color: red;">{{ error }}</p>
  {% endif %}
  {% if did %}
    <p><strong>DID:</strong> {{ did }}</p>
  {% endif %}
'''

@app.route("/", methods=["GET", "POST"])
def index():
    did = None
    error = None
    if request.method == "POST":
        handle = request.form.get("handle")
        if handle:
            try:
                response = client.com.atproto.identity.resolve_handle({"handle": handle})
                did = response.get("did")
            except AtProtocolError:
                error = "User handle not found."
            except Exception as e:
                error = f"Error: {e}"
        else:
            error = "Please enter a handle."
    return render_template_string(FORM_HTML, did=did, error=error)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
