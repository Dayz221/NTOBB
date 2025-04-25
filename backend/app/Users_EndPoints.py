# app/Users_EndPoints.py
import calendar
from flask import Blueprint, request, jsonify
from app.models import User, Building
from datetime import datetime, timezone, timedelta
from app.middleware.isAuthorized import isAuthorized
from app.config import SECRET
from Communicator import Communicator
from app.monitor import *

user_bp = Blueprint('user', __name__, url_prefix='/user')

API_URL = "https://dev.rightech.io/api/v1"
TOKEN   = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI2ODA5Yjc3YWJmYjNlMTc4MWNhNjA1MDEiLCJzdWIiOiI2ODA5YjZlOWJmYjNlMTc4MWNhNjA0ZmQiLCJncnAiOiI2ODA5YjZlOWJmYjNlMTc4MWNhNjA0ZmMiLCJvcmciOiI2ODA5YjZlOWJmYjNlMTc4MWNhNjA0ZmMiLCJsaWMiOiI1ZDNiNWZmMDBhMGE3ZjMwYjY5NWFmZTMiLCJ1c2ciOiJhcGkiLCJmdWxsIjpmYWxzZSwicmlnaHRzIjoxLjUsImlhdCI6MTc0NTQ2NzI1OCwiZXhwIjoxNzQ4MDM0MDAwfQ.jFio63vrm3LnnJtFW9eHSmPOmSnTsD2nsN7W1t38pUQ"

# Создаём Communicator для взаимодействия с MQTT/API
comm = Communicator(API_URL, TOKEN)

# Словарь для преобразования building_id в имя
BUILDING_NAME_BY_ID = {
    0: "680afe2820b46dbb6c1f66fa",
    1: "680afe3820b46dbb6c1f66fb",
    2: "680afe4c20b46dbb6c1f66fc",
}

@user_bp.route('/get_cur_data', methods=['GET'])
@isAuthorized
def get_cur_data(user: User):
    user.reload()
    if not user.measures:
        return jsonify({
            "message": "Нет данных о потреблении",
            "current": 0.0,
            "volume": 0.0,
            "timestamp": None
        }), 200

    latest = max(user.measures, key=lambda m: m.timestamp)

    return jsonify({
        "current": latest.current,
        "volume": latest.volume,
        "timestamp": latest.timestamp
    }), 200

@user_bp.route('/get_cur_current', methods=['GET'])
@isAuthorized
def get_cur_current(user: User):
    user.reload()
    if not user.measures:
        return jsonify({
            "message": "Нет данных о потреблении",
            "current": 0.0,
            "timestamp": None
        }), 200

    latest = max(user.measures, key=lambda m: m.timestamp)

    return jsonify({
        "current": latest.current,
        "timestamp": latest.timestamp
    }), 200

@user_bp.route('/get_cur_flow', methods=['GET'])
@isAuthorized
def get_cur_flow(user: User):
    user.reload()
    if not user.measures:
        return jsonify({
            "message": "Нет данных о потоке воды",
            "flow": 0.0,
            "timestamp": None
        }), 200

    latest = max(user.measures, key=lambda m: m.timestamp)
    return jsonify({
        "flow": latest.volume,
        "timestamp": latest.timestamp
    }), 200

@user_bp.route('/pump_state', methods=['GET'])
@isAuthorized
def get_pump_state(user: User):
    building_name = BUILDING_NAME_BY_ID.get(user.building_id)
    if not building_name:
        return jsonify({"message": "Неизвестный дом у пользователя"}), 400

    flat_no = user.flat_id + 1
    topic = f"base/pumpstate/{flat_no}"
    try:
        payload = comm.read_state(building_name, topic)
    except Exception:
        return jsonify({"message": "Не удалось получить состояние помпы"}), 500

    is_on = False
    if payload is not None:
        s = str(payload).lower()
        if s in ("1", "true", "on"):
            is_on = True

    return jsonify({"pump_on": is_on}), 200


def _bucket_start(dt: datetime, step: str) -> datetime:
    if step == "minute":
        return dt.replace(second=0, microsecond=0)
    if step == "hour":
        return dt.replace(minute=0, second=0, microsecond=0)
    if step == "day":
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    if step == "week":
        monday = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        return monday - timedelta(days=monday.weekday())
    if step == "month":
        return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    raise ValueError(f"Unknown step: {step}")

def _bucket_next(dt: datetime, step: str) -> datetime:
    if step == "minute":
        return dt + timedelta(minutes=1)
    if step == "hour":
        return dt + timedelta(hours=1)
    if step == "day":
        return dt + timedelta(days=1)
    if step == "week":
        return dt + timedelta(weeks=1)
    if step == "month":
        year, month = dt.year, dt.month
        if month == 12:
            return dt.replace(year=year+1, month=1)
        else:
            return dt.replace(month=month+1)
    raise ValueError(f"Unknown step: {step}")

def _bucket_title(dt: datetime, step: str) -> str:
    if step in ("minute", "hour"):
        return dt.strftime("%H:%M")
    if step == "day":
        return dt.strftime("%d.%m")
    if step == "week":
        start = _bucket_start(dt, "week")
        end = start + timedelta(days=6)
        return f"{start.strftime('%d.%m')}–{end.strftime('%d.%m')}"
    if step == "month":
        return dt.strftime("%m.%Y")
    return str(dt)

@user_bp.route('/measures', methods=['POST'])
@isAuthorized
def get_user_measures(user: User):
    params    = request.get_json(force=True) or {}
    start_ts  = int(params.get("start_ts"))
    end_ts    = int(params.get("end_ts"))
    data_type = params.get("type", "both")
    step      = params.get("step", "hour")

    if start_ts > end_ts:
        return jsonify({"message": "Неверный диапазон start_ts/end_ts"}), 400
    if data_type not in ("water","electricity","both"):
        return jsonify({"message": "type должен быть water, electricity или both"}), 400
    if step not in ("minute","hour","day","week","month"):
        return jsonify({"message": "step должен быть minute, hour, day, week или month"}), 400

    user.reload()
    measures = [
        m for m in user.measures
        if start_ts <= m.timestamp <= end_ts
    ]

    start_dt = datetime.fromtimestamp(start_ts, tz=timezone.utc)
    end_dt   = datetime.fromtimestamp(end_ts, tz=timezone.utc)
    buckets = []
    cursor = _bucket_start(start_dt, step)
    while cursor <= end_dt:
        buckets.append(cursor)
        cursor = _bucket_next(cursor, step)
    buckets.append(cursor)

    total_volume = sum(abs(m.volume) for m in measures)
    total_current = sum(abs(m.current) for m in measures)

    out = []
    for i in range(len(buckets) - 1):
        b_start = buckets[i]
        b_end   = buckets[i+1]

        entry = {"time": _bucket_title(b_start, step)}

        vol = 0.0
        cur = 0.0
        for m in measures:
            if b_start.timestamp() <= m.timestamp < b_end.timestamp():
                vol += abs(m.volume)
                cur += abs(m.current)
        if data_type in ("water","both"):
            entry["volume"] = vol
        if data_type in ("electricity","both"):
            entry["current"] = cur
        out.append(entry)

    return jsonify({
        "total_volume":   total_volume,
        "total_current":  total_current,
        "measures":       out
    }), 200


@user_bp.route('/detect_disbalance_flow', methods=['GET'])
@isAuthorized
def detect_disbalance_flow_user(user: User):
    building = Building.objects(building_id=user.building_id).first()
    if not building:
        return jsonify({'message': 'Дом не найден'}), 404

    now = datetime.now(timezone.utc)
    start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

    days_in_month = calendar.monthrange(now.year, now.month)[1]
    days_passed   = (now.date() - start.date()).days + 1

    bound_per_day = building.water_bound / days_in_month

    volumes = [
        m.volume
        for m in user.measures
        if start.timestamp() <= m.timestamp <= now.timestamp()
    ]
    total_volume = sum(volumes)

    avg_per_day = total_volume / days_passed if days_passed > 0 else 0

    status = 'bad' if avg_per_day > bound_per_day else 'good'

    if (status == "bad"):
        subj = "Внимание! Превышена месячная норма расхода воды"
        body = (
            f"Здравствуйте, {user.email}!\n\n"
            f"Ваш расход воды за месяц: {total_volume:.2f} м³. "
            f"Норма: {building.water_bound} м³.\n"
            "Пожалуйста, примите меры."
        )
        send_email(user.email, subj, body)

    return jsonify({
        'message':           'OK',
        'total_volume':      round(total_volume, 3),
        'days_in_month':     days_in_month,
        'days_passed':       days_passed,
        'average_per_day':   round(avg_per_day, 3),
        'bound_per_day':     round(bound_per_day, 3),
        'status':            status
    }), 200


@user_bp.route('/detect_disbalance_current', methods=['GET'])
@isAuthorized
def detect_disbalance_current_user(user: User):
    building = Building.objects(building_id=user.building_id).first()
    if not building:
        return jsonify({'message': 'Дом не найден'}), 404

    now = datetime.now(timezone.utc)
    start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

    days_in_month = calendar.monthrange(now.year, now.month)[1]
    days_passed   = (now.date() - start.date()).days + 1

    bound_per_day = building.electricity_bound / days_in_month
    print(bound_per_day)

    volumes = [
        m.current
        for m in user.measures
        if start.timestamp() <= m.timestamp <= now.timestamp()
    ]
    total_volume = sum(volumes)

    avg_per_day = total_volume / days_passed if days_passed > 0 else 0

    status = 'bad' if avg_per_day > bound_per_day else 'good'

    if(status == "bad"):
        subj = "Внимание! Превышена месячная норма электричества"
        body = (
            f"Здравствуйте, {user.email}!\n\n"
            f"Ваш расход электричества за месяц: {total_volume:.2f} Вт·ч. "
            f"Норма: {building.electricity_bound} Вт·ч.\n"
            "Пожалуйста, примите меры."
        )
        send_email(user.email, subj, body)

    return jsonify({
        'message':           'OK',
        'total_volume':      round(total_volume, 3),
        'days_in_month':     days_in_month,
        'days_passed':       days_passed,
        'average_per_day':   round(avg_per_day, 3),
        'bound_per_day':     round(bound_per_day, 3),
        'status':            status
    }), 200
    
@user_bp.route('/get_priority', methods=['GET'])
def get_priority(user: User):
    building = Building.objects(building_id=user.building_id).first()
    if not building:
        return jsonify({'message': 'Дом не найден'}), 404

    now = datetime.now(timezone.utc)
    start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

    days_in_month = calendar.monthrange(now.year, now.month)[1]
    days_passed   = (now.date() - start.date()).days + 1

    bound_per_day = building.water_bound / days_in_month

    volumes = [
        m.volume
        for m in user.measures
        if start.timestamp() <= m.timestamp <= now.timestamp()
    ]
    total_volume = sum(volumes)

    avg_per_day = total_volume / days_passed if days_passed > 0 else 0

    if (avg_per_day < bound_per_day-50):
        user.priority = 1
    elif (bound_per_day-50 < avg_per_day < bound_per_day+50):
        user.priority = 2
    else:
        user.priority = 3
    user.save()

    return jsonify({
        'priority': user.priority
    }), 200
