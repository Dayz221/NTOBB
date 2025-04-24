# app/mqtt_connector.py
from flask import Blueprint, request, jsonify, render_template, current_app
from app.middleware.isAuthorized import isAuthorized
from paho.mqtt.client import Client as MQTTClient
from app.models import User, Measure
from Communicator import Communicator
import time

mqtt_bp = Blueprint('mqtt', __name__)

# Настройки API и токена для Communicator
API_URL = "https://dev.rightech.io/api/v1"
TOKEN   = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI2ODA5Yjc3YWJmYjNlMTc4MWNhNjA1MDEiLCJzdWIiOiI2ODA5YjZlOWJmYjNlMTc4MWNhNjA0ZmQiLCJncnAiOiI2ODA5YjZlOWJmYjNlMTc4MWNhNjA0ZmMiLCJvcmciOiI2ODA5YjZlOWJmYjNlMTc4MWNhNjA0ZmMiLCJsaWMiOiI1ZDNiNWZmMDBhMGE3ZjMwYjY5NWFmZTMiLCJ1c2ciOiJhcGkiLCJmdWxsIjpmYWxzZSwicmlnaHRzIjoxLjUsImlhdCI6MTc0NTQ2NzI1OCwiZXhwIjoxNzQ4MDM0MDAwfQ.jFio63vrm3LnnJtFW9eHSmPOmSnTsD2nsN7W1t38pUQ"

communicator = Communicator(API_URL, TOKEN)
# Отображение названия дома по user.building_id
BUILDING_MAP = {
    0 : "6809bdfebfb3e1781ca60503",
    1 : "680a062c20b46dbb6c1f66d3",
    2 : "680a065420b46dbb6c1f66d4",
}

# Сохранение измерений пользователя

def save_measure_to_user(target_id: str, topic: str, payload: float, timestamp: int):
    building_id = BUILDING_MAP.get(target_id)
    if building_id is None:
        current_app.logger.warning(f"Unknown target_ID: {target_id}")
        return
    try:
        _, typedata, num = topic.split('/')
        flat_id = int(num) - 1
    except Exception as e:
        current_app.logger.error(f"Bad topic format: {topic} ({e})")
        return

    volume  = payload if "waterdata" in typedata else 0.0
    current = payload if "currentdata" in typedata else 0.0
    user = User.objects(building_id=building_id, flat_id=flat_id).first()
    if not user:
        current_app.logger.warning(f"No user for building={building_id}, flat={flat_id}")
        return

    m = Measure(timestamp=timestamp, volume=volume, current=current)
    user.update(push__measures=m)
    current_app.logger.debug(f"Pushed Measure to {user.email}: {m}")

# Эндпоинт для рендеринга главной страницы

@mqtt_bp.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# Эндпоинт для получения всех данных

@mqtt_bp.route('/data', methods=['GET'])
def get_data():
    out = []
    for u in User.objects():
        for m in u.measures:
            out.append({
                'email':     u.email,
                'building':  u.building_id,
                'flat':      u.flat_id,
                'timestamp': m.timestamp,
                'volume':    m.volume,
                'current':   m.current
            })
    return jsonify(out), 200

# Эндпоинт для переключения насоса

@mqtt_bp.route('/toggle', methods=['POST'])
@isAuthorized
def toggle_pump(user: User):
    data = request.get_json(force=True) or {}
    action = data.get('action')
    if action not in ('on', 'off'):
        return jsonify({'message': 'Укажите параметр "action": "on" или "off"'}), 400

    building_name = BUILDING_MAP.get(user.building_id)
    if building_name is None:
        return jsonify({'message': 'Неизвестный дом у пользователя'}), 500

    flat_no = user.flat_id + 1
    cmd = f"Switch{'On' if action=='on' else 'Off'}_{flat_no}"
    try:
        communicator.send_command(building_name, cmd)
        user.button_state = (action == 'on')
        user.save()
        current_app.logger.info(
            f"User {user.email}: set button_state={user.button_state} and sent '{cmd}' to {building_name}"
        )
        return jsonify({
            'message': f"Насос успешно {'включён' if action=='on' else 'выключен'}"
        }), 200
    except Exception:
        current_app.logger.exception("Ошибка при отправке команды насосу")
        return jsonify({'message': 'Не удалось изменить состояние насоса'}), 500
