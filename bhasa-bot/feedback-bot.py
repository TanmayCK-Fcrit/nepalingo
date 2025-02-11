import http.client
import json
import os
from textwrap import dedent

from supabase import create_client, Client


DISCORD_WEBHOOK_ENDPOINT = os.getenv("DISCORD_WEBHOOK_ENDPOINT")

EMOJI_RATING_MAP = {
    1: "😟",
    2: "😐",
    3: "😊",
    4: "😃",
    5: "😍",
}


def main():
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    supabase: Client = create_client(url, key)

    # Get last feedback id that was sent to discord
    response = supabase.table("discord_bot_data").select("val").eq("key", "last_feedback_id_sent").limit(1).single().execute()
    last_feedback_id_sent = int(response.data["val"])
    print(last_feedback_id_sent)

    # Get all new feedback by that id
    new_feedback = supabase.table("feedback").select("*").gt("id", last_feedback_id_sent).execute()
    print(new_feedback )

    if (not new_feedback.data):
        print("No new feedback found")
        exit(1)

    conn = http.client.HTTPSConnection("discord.com")

    # Send all new messages to discord
    max_id = last_feedback_id_sent
    for row in new_feedback.data:
        message = dedent(f"""
            ```
            Star rating {"★ "*row["rating"]}{"★"*(5-row["rating"])}
            Emoji rating {EMOJI_RATING_MAP[row["emoji_rating"]]}
            {f'Comments: {row["comments"]}' if row["comments"] else ""}
            ```
            """)

        print(message)
        send_message(conn, message)
        max_id = max(max_id, row["id"])

    # Update last_feedback_id_sent to latest feedback that was sent to discord
    supabase.table("discord_bot_data").update({"val": max_id}).eq("key", "last_feedback_id_sent").execute()


def send_message(conn, message):
    payload = json.dumps({
        "content": message
    })
    headers = {
        'Content-Type': 'application/json',
    }
    conn.request("POST", DISCORD_WEBHOOK_ENDPOINT, payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))


if __name__ == "__main__":
    main()

