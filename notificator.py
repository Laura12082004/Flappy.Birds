import time
import os
from twilio.rest import Client

# Twilio
account_sid = 'AC864af3ad607edde33015baf42c453dcc'
auth_token = 'b43a7372e4adf912d1f1862933588c4a'
client = Client(account_sid, auth_token)

twilio_whatsapp_number = 'whatsapp:+14155238886'
your_whatsapp_number = 'whatsapp:+40771167158'

def send_reminder():
    message = client.messages.create(
        body="👋 Hei! Nu ai mai jucat Flappy Bird de 5 minute! Hai înapoi! 🐤🎮",
        from_=twilio_whatsapp_number,
        to=your_whatsapp_number
    )
    print("Mesaj trimis:", message.sid)

def check_last_played():
    if not os.path.exists("last_played.txt"):
        print("Fișierul last_played.txt nu există încă.")
        return

    with open("last_played.txt", "r") as f:
        try:
            last_time = float(f.read())
        except ValueError:
            print("Eroare la citirea timpului.")
            return

    now = time.time()
    time_passed = now - last_time
    if time_passed >= 300:  # 5 minute = 300 secunde
        print("Au trecut mai mult de 5 minute. Trimitem notificare.")
        send_reminder()
    else:
        print(f"Mai sunt {int((300 - time_passed) // 60)} minute până la notificare.")

# Verifică la fiecare 1 minut
while True:
    check_last_played()
    time.sleep(60)
