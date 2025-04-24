from flask import Blueprint, jsonify, request
from app.middleware.isAdmin import isAdmin
from app.models import User, Building
from app.config import U
import calendar
from datetime import datetime, timezone, timedelta
from app.mqtt_connector import BUILDING_MAP, communicator
from config import CURRENT_BOUND

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/users', methods=['GET'])
@isAdmin
def list_all_users(admin_user: User):
    users = User.objects().select_related()
    result = []
    for u in users:
        user_data = {
            'id': str(u.id),
            'email': u.email,
            'building_id': u.building_id,
            'flat_id': u.flat_id,
            'is_blocked': u.is_blocked,
            'pump_broken': u.pump_broken,
            'button_state': u.button_state,
            'permissions': u.permissions,
        }
        result.append(user_data)
    return jsonify({'users': result}), 200

@admin_bp.route('/buildings', methods=['GET'])
@isAdmin
def list_all_buildings(admin_user: User):
    buildings = Building.objects()
    result = []
    for b in buildings:
        building_data = {
            'id': str(b.id),
            'building_id': b.building_id,
            'water_bound': b.water_bound,
            'pump_states': b.pump_states,
            'mode3_enabled': b.mode3_enabled
        }
        result.append(building_data)
    return jsonify({'buildings': result}), 200


# Используем короткий ID: 0-2
@admin_bp.route('/buildings/<int:building_id>/water_bound', methods=['POST'])
@isAdmin
def set_water_bound(admin_user: User, building_id: int):
    data = request.get_json() or {}

    top_level = data.get('top_level')

    if top_level is None:
        return jsonify({'msg': 'Параметр top_level обязателен'}), 400

    try:
        top_level = int(top_level)
    except (ValueError, TypeError):
        return jsonify({'msg': 'top_level должен быть целым числом'}), 400

    building = Building.objects(building_id=building_id).first()
    if not building:
        return jsonify({'msg': 'Дом не найден'}), 404

    building.water_bound = top_level
    building.save()
    return jsonify({'msg': 'OK'}), 200


@admin_bp.route('/users/<string:user_id>/block', methods=['POST'])
@isAdmin
def block_user(admin_user: User, user_id: str):
    user = User.objects(id=user_id).first()
    if not user:
        return jsonify({'message': 'Пользователь не найден'}), 404

    user.is_blocked = True
    user.button_state = False

    building = Building.objects(building_id=user.building_id).first()

    communicator.send_command(building, f"SwitchOff_{user.flat_id + 1}")
    user.save()
    return jsonify({'message': 'Пользователь заблокирован'}), 200


@admin_bp.route('/users/<string:user_id>/unblock', methods=['POST'])
@isAdmin
def unblock_user(admin_user: User, user_id: str):
    user = User.objects(id=user_id).first()
    if not user:
        return jsonify({'message': 'Пользователь не найден'}), 404

    user.is_blocked = False
    user.save()
    return jsonify({'message': 'Пользователь разблокирован'}), 200


@admin_bp.route('/users/<string:user_id>/break', methods=['POST'])
@isAdmin
def block_user(admin_user: User, user_id: str):
    user = User.objects(id=user_id).first()
    if not user:
        return jsonify({'message': 'Пользователь не найден'}), 404

    user.pump_broken = True
    user.button_state = False
    user.save()
    return jsonify({'message': 'Насос сломан'}), 200


@admin_bp.route('/users/<string:user_id>/repair', methods=['POST'])
@isAdmin
def unblock_user(admin_user: User, user_id: str):
    user = User.objects(id=user_id).first()
    if not user:
        return jsonify({'message': 'Пользователь не найден'}), 404

    user.pump_broken = False
    user.save()
    return jsonify({'message': 'Насос починен'}), 200



@admin_bp.route('/users/<string:user_id>/block-status', methods=['GET'])
@isAdmin
def block_info(admin_user: User, user_id: str):
    user = User.objects(id=user_id).first()
    if not user:
        return jsonify({'message': 'Пользователь не найден'}), 404

    return jsonify({'is_blocked': user.is_blocked}), 200


@admin_bp.route('/users/<string:user_id>/get_period_statistics', methods=['POST'])
@isAdmin
def get_period_statistics(admin_user: User, user_id: str):
    data = request.get_json(silent=True) or {}

    start_ts = data.get('start_time')
    end_ts   = data.get('end_time')
    if start_ts is None:
        return jsonify({'message': 'Параметр start_time обязателен'}), 400
    if end_ts is None:
        return jsonify({'message': 'Параметр end_time обязателен'}), 400

    try:
        start_ts = int(start_ts)
    except (ValueError, TypeError):
        return jsonify({'message': 'start_time должен быть целым числом'}), 400
    try:
        end_ts = int(end_ts)
    except (ValueError, TypeError):
        return jsonify({'message': 'end_time должен быть целым числом'}), 400

    if start_ts > end_ts:
        return jsonify({'message': 'start_time не может быть больше end_time'}), 400

    # Ищем пользователя по _id
    user = User.objects(id=user_id).first()
    if not user:
        return jsonify({'message': 'Пользователь не найден'}), 404

    # Фильтруем замеры по периоду
    filtered = [
        m for m in user.measures
        if start_ts <= m.timestamp <= end_ts
    ]
    if not filtered:
        return jsonify({'message': 'Нет данных за указанный период'}), 404

    # Суммируем расход воды и электричества
    total_water       = sum(abs(m.volume)  for m in filtered)
    total_electricity = sum(abs(m.current) for m in filtered)

    return jsonify({
        'message': 'OK',
        'water_consumption':       total_water,
        'electricity_consumption': total_electricity
    }), 200


@admin_bp.route('/users/<string:user_id>/leak', methods=['GET'])
@isAdmin
def check_user_leak(admin_user: User, user_id: str):
    user = User.objects(id=user_id).first()
    if not user:
        return jsonify({'message': 'Пользователь не найден'}), 404

    if not user.measures:
        return jsonify({'message': 'Нет данных о расходе воды'}), 404

    # берём самый последний замер по времени
    last = max(user.measures, key=lambda m: m.timestamp)
    leak = last.volume > 0 and not user.button_state

    return jsonify({
        'user_id':       str(user.id),
        'leak_detected': leak,
        'last_volume':   last.volume,
        'pump_on':       user.button_state
    }), 200


@admin_bp.route('/buildings/<int:building_id>/leaks', methods=['GET'])
@isAdmin
def check_building_leaks(admin_user: User, building_id: int):
    users = User.objects(building_id=building_id)
    if not users:
        return jsonify({'message': 'Пользователи не найдены в этом доме'}), 404

    leaks = []
    for user in users:
        if not user.measures:
            continue
        last = max(user.measures, key=lambda m: m.timestamp)
        if last.volume > 0 and not user.button_state:
            leaks.append({
                'user_id':     str(user.id),
                'flat_id':     user.flat_id,
                'last_volume': last.volume,
                'pump_on':     user.button_state
            })

    return jsonify({
        'building_id':    building_id,
        'leaks_detected': len(leaks),
        'users_with_leak': leaks
    }), 200


@admin_bp.route('/users/<string:user_id>/detect_disbalance_flow', methods=['GET'])
@isAdmin
def detect_disbalance_flow(admin_user: User, user_id: str):
    target = User.objects(id=user_id).first()
    if not target:
        return jsonify({'message': 'Пользователь не найден'}), 404

    building = Building.objects(building_id=target.building_id).first()
    if not building:
        return jsonify({'message': 'Дом не найден'}), 404

    now = datetime.now()
    start = datetime(now.year, now.month, 1)
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    days_passed   = (now.date() - start.date()).days + 1

    bound_per_day = building.water_bound / days_in_month

    volumes = [
        m.volume
        for m in target.measures
        if start <= datetime.fromtimestamp(m.timestamp) <= now
    ]
    total_volume = sum(volumes)

    avg_per_day = total_volume / days_passed if days_passed > 0 else 0

    status = 'bad' if avg_per_day > bound_per_day else 'good'

    return jsonify({
        'message':             'OK',
        'total_volume':        round(total_volume, 3),
        'days_in_month':       days_in_month,
        'days_passed':         days_passed,
        'average_per_day':     round(avg_per_day, 3),
        'bound_per_day':       round(bound_per_day, 3),
        'status':              status
    }), 200


@admin_bp.route('/users/<string:user_id>/detect_disbalance_current', methods=['GET'])
@isAdmin
def detect_disbalance_current(admin_user: User, user_id: str):
    target = User.objects(id=user_id).first()
    if not target:
        return jsonify({'message': 'Пользователь не найден'}), 404

    building = Building.objects(building_id=target.building_id).first()
    if not building:
        return jsonify({'message': 'Дом не найден'}), 404

    now = datetime.now()
    start = datetime(now.year, now.month, 1)
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    days_passed   = (now.date() - start.date()).days + 1

    bound_per_day = CURRENT_BOUND / days_in_month

    volumes = [
        m.current
        for m in target.measures
        if start <= datetime.fromtimestamp(m.timestamp) <= now
    ]
    total_volume = sum(volumes)

    avg_per_day = total_volume / days_passed if days_passed > 0 else 0

    status = 'bad' if avg_per_day > bound_per_day else 'good'

    return jsonify({
        'message':             'OK',
        'total_volume':        round(total_volume, 3),
        'days_in_month':       days_in_month,
        'days_passed':         days_passed,
        'average_per_day':     round(avg_per_day, 3),
        'bound_per_day':       round(bound_per_day, 3),
        'status':              status
    }), 200



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


@admin_bp.route('/users/<string:user_id>/measures', methods=['POST'])
@isAdmin
def get_user_measures_admin(admin_user: User, user_id: str):
    params = request.get_json(force=True) or {}
    # обязательные параметры
    try:
        start_ts = int(params.get("start_ts"))
    except (TypeError, ValueError):
        return jsonify({'message': 'start_ts обязателен и должен быть целым'}), 400
    try:
        end_ts = int(params.get("end_ts"))
    except (TypeError, ValueError):
        return jsonify({'message': 'end_ts обязателен и должен быть целым'}), 400

    if start_ts > end_ts:
        return jsonify({'message': 'start_ts не может быть больше end_ts'}), 400

    data_type = params.get("type", "both")
    if data_type not in ("water", "electricity", "both"):
        return jsonify({'message': 'type должен быть water, electricity или both'}), 400

    step = params.get("step", "hour")
    if step not in ("minute", "hour", "day", "week", "month"):
        return jsonify({'message': 'step должен быть minute, hour, day, week или month'}), 400

    # находим пользователя
    user = User.objects(id=user_id).first()
    if not user:
        return jsonify({'message': 'Пользователь не найден'}), 404
    user.reload()

    # фильтруем замеры по интервалу
    measures = [
        m for m in user.measures
        if start_ts <= m.timestamp <= end_ts
    ]

    # готовим корзины по шагу
    start_dt = datetime.fromtimestamp(start_ts, tz=timezone.utc)
    end_dt   = datetime.fromtimestamp(end_ts,   tz=timezone.utc)
    buckets = []
    cursor = _bucket_start(start_dt, step)
    while cursor <= end_dt:
        buckets.append(cursor)
        cursor = _bucket_next(cursor, step)
    buckets.append(cursor)

    # считаем итоги и разбивку
    total_volume  = sum(abs(m.volume)  for m in measures)
    total_current = sum(abs(m.current) for m in measures)
    out = []
    for i in range(len(buckets) - 1):
        b_start, b_end = buckets[i], buckets[i+1]
        entry = {"time": _bucket_title(b_start, step)}
        vol = cur = 0.0
        for m in measures:
            if b_start.timestamp() <= m.timestamp < b_end.timestamp():
                vol += abs(m.volume)
                cur += abs(m.current)
        if data_type in ("water", "both"):
            entry["volume"] = vol
        if data_type in ("electricity", "both"):
            entry["current"] = cur
        out.append(entry)

    return jsonify({
        "total_volume":   total_volume,
        "total_current":  total_current,
        "measures":       out
    }), 200


@admin_bp.route('/users/<string:user_id>/toggle_pump', methods=['POST'])
@isAdmin
def toggle_pump_admin(admin_user: User, user_id: str):
    data = request.get_json(force=True) or {}
    action = data.get('action')
    if action not in ('on', 'off'):
        return jsonify({'message': 'Укажите параметр "action": "on" или "off"'}), 400

    target = User.objects(id=user_id).first()
    if not target:
        return jsonify({'message': 'Пользователь не найден'}), 404

    building_name = BUILDING_MAP.get(target.building_id)
    if not building_name:
        return jsonify({'message': 'Неизвестный дом у пользователя'}), 500

    flat_no = target.flat_id + 1
    cmd     = f"Switch{'On' if action == 'on' else 'Off'}_{flat_no}"

    try:
        communicator.send_command(building_name, cmd)

        target.button_state = (action == 'on')
        target.save()

        return jsonify({
            'message': f"Насос успешно {'включён' if action == 'on' else 'выключен'}",
            'button_state': target.button_state
        }), 200

    except Exception:
        return jsonify({'message': 'Не удалось изменить состояние насоса'}), 500