from flask import Blueprint, jsonify, request
from app.middleware.isAdmin import isAdmin
from app.models import User, Building
from app.config import U
import calendar
from datetime import datetime

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


@admin_bp.route('/users/<string:user_id>/detect_disbalance', methods=['GET'])
@isAdmin
def detect_disbalance(admin_user: User, user_id: str):
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