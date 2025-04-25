import threading
from flask import current_app
import smtplib, time, calendar
from datetime import datetime, timezone

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


def monitor_bounds():
    while True:
        for user in User.objects:
            try:
                # --- всё, что должно быть внутри try, с отступом 4 пробела ---
                bld = Building.objects(building_id=user.building_id).first()
                if not bld or bld.water_bound is None:
                    continue

                now = datetime.now(timezone.utc)
                start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
                days_in_month = calendar.monthrange(now.year, now.month)[1]

                # подсчёт объёма за месяц
                total_volume = sum(
                    m.volume
                    for m in user.measures
                    if start.timestamp() <= m.timestamp <= now.timestamp()
                )
                avg_per_day = total_volume / ((now.day) or 1)

                bound_per_day = bld.water_bound / days_in_month

                if avg_per_day > bound_per_day:
                    subj = "Превышен месячный лимит воды"
                    body = (
                        f"Пользователь {user.email} "
                        f"средне {avg_per_day:.2f} м³/день при лимите {bound_per_day:.2f}."
                    )
                    send_email(user.email, subj, body)

            except Exception as ex:
                # обрабатываем любое исключение, чтобы поток не умирал
                print(f"Ошибка в monitor_bounds для {user.email}: {ex}")

        # ждем час перед следующей проверкой
        time.sleep(3600)


def start_monitoring(interval: int = 3600):
    t = threading.Thread(target=monitor_bounds, args=(interval,), daemon=True)
    t.start()
