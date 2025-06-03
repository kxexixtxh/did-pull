import tkinter as tk
from tkinter import messagebox
from atproto import Client
from atproto.exceptions import AtProtocolError

client = Client()


def resolve_handle():
    handle = entry.get()
    if not handle:
        messagebox.showwarning("Input Error", "Please enter a Bluesky handle.")
        return

    try:
        response = client.com.atproto.identity.resolve_handle({'handle': handle})
        did = response['did']

        profile = client.app.bsky.actor.get_profile({'actor': handle})
        display_name = profile.get('displayName', 'N/A')
        description = profile.get('description', 'No description')

        result_text = f"DID: {did}\nName: {display_name}\nBio: {description}"
        result_label.config(text=result_text)
    except AtProtocolError:
        messagebox.showerror("Error", f"Handle '{handle}' not found or invalid.")
    except Exception as e:
        messagebox.showerror("Error", f"Unexpected error: {e}")


# Create the main window
root = tk.Tk()
root.title("Bluesky DID Resolver")

# Handle input
tk.Label(root, text="Enter Bluesky handle (e.g. user.bsky.social):").pack(pady=5)
entry = tk.Entry(root, width=40)
entry.pack(pady=5)

# Resolve button
resolve_button = tk.Button(root, text="Get DID & Profile", command=resolve_handle)
resolve_button.pack(pady=10)

# Result display
result_label = tk.Label(root, text="", justify="left", font=("Arial", 12))
result_label.pack(pady=10)

root.mainloop()
