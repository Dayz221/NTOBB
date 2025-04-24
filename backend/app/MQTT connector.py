import threading
import time

from flask import Flask, request, jsonify, render_template
from app.middleware.isAuthorized import isAuthorized
from paho.mqtt.client import Client as MQTTClient

from app.models import User, Measure
from Communicator import Communicator
from app import app

API_URL = "https://dev.rightech.io/api/v1"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI2ODA5Yjc3YWJmYjNlMTc4MWNhNjA1MDEiLCJzdWIiOiI2ODA5YjZlOWJmYjNlMTc4MWNhNjA0ZmQiLCJncnAiOiI2ODA5YjZlOWJmYjNlMTc4MWNhNjA0ZmMiLCJvcmciOiI2ODA5YjZlOWJmYjNlMTc4MWNhNjA0ZmMiLCJsaWMiOiI1ZDNiNWZmMDBhMGE3ZjMwYjY5NWFmZTMiLCJ1c2ciOiJhcGkiLCJmdWxsIjpmYWxzZSwicmlnaHRzIjoxLjUsImlhdCI6MTc0NTQ2NzI1OCwiZXhwIjoxNzQ4MDM0MDAwfQ.jFio63vrm3LnnJtFW9eHSmPOmSnTsD2nsN7W1t38pUQ"
communicator = Communicator(API_URL, TOKEN)

BUILDING_MAP = {
    "building_one":   0,
    "building_two":   1,
    "building_four": 2,
}


def save_measure_to_user(target_ID: str, topic: str, payload: float, timestamp: int):
    # find building_id
    building_id = BUILDING_MAP.get(target_ID)
    if building_id is None:
        app.logger.warning(f"Unknown target_ID: {target_ID}")
        return

    # get flat_id from topic base/<type>data/{n}
    try:
        _, typedata, num = topic.split('/')
        flat_id = int(num) - 1
    except Exception as e:
        app.logger.error(f"Bad topic format: {topic} ({e})")
        return

    # get a measure type
    volume  = payload if "waterdata"  in typedata else 0.0
    current = payload if "currentdata" in typedata else 0.0

    # find user
    user = User.objects(building_id=building_id, flat_id=flat_id).first()
    if not user:
        app.logger.warning(f"No user for building={building_id}, flat={flat_id}")
        return

    # add
    m = Measure(timestamp=timestamp, volume=volume, current=current)
    user.update(push__measures=m)
    app.logger.debug(f"Pushed Measure to {user.email}: {m}")


def poll_states():
    target_IDs = list(BUILDING_MAP.keys())
    topics = [
        "base/waterdata/1","base/waterdata/2","base/waterdata/3",
        "base/waterdata/4","base/waterdata/5",
        "base/currentdata/1","base/currentdata/2","base/currentdata/3",
        "base/currentdata/4","base/currentdata/5",
    ]

    while True:
        for target_ID in target_IDs:
            for topic in topics:
                payload = communicator.read_state(target_ID, topic)
                if payload is not None:
                    ts = int(time.time())
                    app.logger.info(f"Read {payload} @ {ts} from {topic} @ {target_ID}")
                    save_measure_to_user(target_ID, topic, float(payload), ts)
        time.sleep(10)






if __name__ == "__main__":
    th = threading.Thread(target=poll_states, daemon=True)
    th.start()
    app.run(host="0.0.0.0", port=5000, debug=True)
