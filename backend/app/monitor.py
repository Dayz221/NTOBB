import time
import smtplib
from datetime import datetime
import threading

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.models import User, Building

SMTP_SERVER    = "smtp.mail.ru"
SMTP_PORT      = 465
EMAIL_ADDRESS  = "clashnoch@mail.ru"
EMAIL_PASSWORD = "Spmysa3xt9q5wawpdRK5"

def send_email(to_email: str, subject: str, body: str):
    msg = MIMEMultipart()
    msg["From"]    = EMAIL_ADDRESS
    msg["To"]      = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
    print(f"[OK] Отправлено на {to_email} — {subject}")


def monitor_bounds(check_interval: int = 3600):
    alerted = set()

    while True:
        now_ts = datetime.now().timestamp()
        month_start_ts = datetime(datetime.now().year, datetime.now().month, 1).timestamp()

        for user in User.objects():
            bld = Building.objects(building_id=user.building_id).first()
            if not bld:
                continue

            measures = [m for m in user.measures if m.timestamp >= month_start_ts]
            total_water = sum(abs(m.volume) for m in measures)
            total_elec  = sum(abs(m.current) for m in measures)

            if total_water > bld.water_bound:
                key = (str(user.id), "water")
                if key not in alerted:
                    subj = "Внимание! Превышена месячная норма воды"
                    body = (
                        f"Здравствуйте, {user.email}!\n\n"
                        f"Ваш расход воды за месяц: {total_water:.2f} м³. "
                        f"Норма: {bld.water_bound} м³.\n"
                        "Пожалуйста, примите меры."
                    )
                    send_email(user.email, subj, body)
                    alerted.add(key)

            if total_elec > bld.electricity_bound:
                key = (str(user.id), "electricity")
                if key not in alerted:
                    subj = "Внимание! Превышена месячная норма электричества"
                    body = (
                        f"Здравствуйте, {user.email}!\n\n"
                        f"Ваш расход электричества за месяц: {total_elec:.2f} кВт·ч. "
                        f"Норма: {bld.electricity_bound} кВт·ч.\n"
                        "Пожалуйста, примите меры."
                    )
                    send_email(user.email, subj, body)
                    alerted.add(key)

        time.sleep(check_interval)


def start_monitoring(interval: int = 3600):
    t = threading.Thread(target=monitor_bounds, args=(interval,), daemon=True)
    t.start()
