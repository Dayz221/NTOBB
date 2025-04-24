from flask import Blueprint, jsonify, request
from app.middleware.isAdmin import isAdmin
from app.models import User, Building

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
