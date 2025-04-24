# app/poller.py
import threading
import time

from Communicator import Communicator
from app.models import User, Measure

API_URL = "https://dev.rightech.io/api/v1"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI2ODA5Yjc3YWJmYjNlMTc4MWNhNjA1MDEiLCJzdWIiOiI2ODA5YjZlOWJmYjNlMTc4MWNhNjA0ZmQiLCJncnAiOiI2ODA5YjZlOWJmYjNlMTc4MWNhNjA0ZmMiLCJvcmciOiI2ODA5YjZlOWJmYjNlMTc4MWNhNjA0ZmMiLCJsaWMiOiI1ZDNiNWZmMDBhMGE3ZjMwYjY5NWFmZTMiLCJ1c2ciOiJhcGkiLCJmdWxsIjpmYWxzZSwicmlnaHRzIjoxLjUsImlhdCI6MTc0NTQ2NzI1OCwiZXhwIjoxNzQ4MDM0MDAwfQ.jFio63vrm3LnnJtFW9eHSmPOmSnTsD2nsN7W1t38pUQ"

# повторите BUILDING_MAP из MQTT connector
BUILDING_MAP = {
    "building_one":   0,
    "building_two":   1,
    "building_four":  2,
}

# создаём один экземпляр Communicator
communicator = Communicator(API_URL, TOKEN)

def save_measure_to_user(target_ID: str, topic: str, payload: float, timestamp: int):
    building_id = BUILDING_MAP.get(target_ID)
    if building_id is None:
        return

    try:
        _, typedata, num = topic.split('/')
        flat_id = int(num) - 1
    except:
        return

    volume  = payload if "waterdata"  in typedata else 0.0
    current = payload if "currentdata" in typedata else 0.0


    users = User.objects(building_id=building_id, flat_id=flat_id)

    for user in users:
        m = Measure(timestamp=timestamp, volume=volume, current=current)
        user.update(push__measures=m)


def poll_states():
    topics = [
        "base/waterdata/1","base/waterdata/2","base/waterdata/3",
        "base/waterdata/4","base/waterdata/5",
        "base/currentdata/1","base/currentdata/2","base/currentdata/3",
        "base/currentdata/4","base/currentdata/5",
    ]
    while True:
        for target_ID in BUILDING_MAP:
            for topic in topics:
                try:
                    payload = communicator.read_state(target_ID, topic)
                    # print(target_ID, topic, payload)
                except Exception as e:
                    continue
                if payload is None:
                    continue

                ts = int(time.time())
                save_measure_to_user(target_ID, topic, float(payload), ts)
        time.sleep(10)

def start_polling():
    thread = threading.Thread(target=poll_states, daemon=True)
    thread.start()
