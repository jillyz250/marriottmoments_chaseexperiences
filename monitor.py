import requests
import hashlib
import json
import os
import smtplib
from email.message import EmailMessage

SITES = [
    {
        "name": "Marriott Moments US",
        "url": "https://moments.marriottbonvoy.com/en-us",
        "state_file": "state_marriott.json",
    },
    {
        "name": "Chase Experiences",
        "url": "https://experiences.chase.com",
        "state_file": "state_chase.json",
    },
]


def fetch_page(url):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.text


def fingerprint(content):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def load_state(path):
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)


def save_state(path, value):
    with open(path, "w") as f:
        json.dump({"fingerprint": value}, f)


def send_email(site_name, site_url):
    msg = EmailMessage()
    msg["Subject"] = f"Change detected: {site_name}"
    msg["From"] = os.environ["EMAIL_FROM"]
    msg["To"] = os.environ["EMAIL_TO"]

    msg.set_content(
        f"A change was detected on:\n\n"
        f"{site_name}\n"
        f"{site_url}\n\n"
        f"Go check it."
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(
            os.environ["EMAIL_FROM"],
            os.environ["EMAIL_PASSWORD"],
        )
        server.send_message(msg)


def check_site(site):
    print(f"Checking {site['name']}")

    html = fetch_page(site["url"])
    current_fp = fingerprint(html)
    last_state = load_state(site["state_file"])

    if last_state is None:
        print("  First run. Saving state.")
        save_state(site["state_file"], current_fp)
        return False

    if current_fp != last_state["fingerprint"]:
        print("  CHANGE DETECTED")
        send_email(site["name"], site["url"])
        save_state(site["state_file"], current_fp)
        return True

    print("  No change.")
    return False


def main():
    for site in SITES:
        try:
            check_site(site)
        except Exception as e:
            print(f"Error checking {site['name']}: {e}")

    print("Run complete.")


if __name__ == "__main__":
    main()
