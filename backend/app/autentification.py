from flask import Blueprint, request, jsonify
from app.models import User
import bcrypt
import jwt
import face_recognition
import io, base64
from flask import Blueprint

from app.middleware.isAuthorized import isAuthorized
from app.config import SECRET
from Communicator import Communicator

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Вспомогательная функция для декодирования base64 image

app_auth_bp = Blueprint("app_auth_bp", __name__, url_prefix="/auth")

def decode_base64_image(data_url: str):
    if ',' in data_url:
        data_url = data_url.split(',', 1)[1]
    return base64.b64decode(data_url)

# Полуавторизация (по логину/паролю без распознавания)
@auth_bp.route('/semi_login', methods=['POST'])
def semi_login_handler():
    try:
        data = dict(request.get_json())
        login = data.get('login')
        password = data.get('password')

        user = User.objects.filter(email=login).first()
        if user is None or not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            return jsonify({'message': 'Неверные email или пароль!'}), 401

        return jsonify({'message': 'OK'}), 200
    except Exception as ex:
        print(ex)
        return jsonify({'message': 'Произошла неизвестная ошибка'}), 400

# Регистрация с распознаванием лица
@auth_bp.route('/register', methods=['POST'])
def register_handler():
    try:
        data = dict(request.get_json())
        login = data.get('additionalData', {}).get('login')
        password = data.get('additionalData', {}).get('password')
        building_id = data.get('additionalData', {}).get('building_id')
        flat_id = data.get('additionalData', {}).get('flat_id')
        image_b64 = data.get('image')

        if User.objects(email=login).first():
            return jsonify({'message': 'Пользователь с таким логином уже существует!'}), 400

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        img_bytes = decode_base64_image(image_b64)
        known_image = face_recognition.load_image_file(io.BytesIO(img_bytes))
        encodings = face_recognition.face_encodings(known_image, model='large')
        if not encodings:
            return jsonify({'message': 'Лицо не найдено'}), 400
        if len(encodings) > 1:
            return jsonify({'message': 'Найдено несколько лиц'}), 400
        known_encoding = [float(x) for x in encodings[0]]

        new_user = User(
            email=login,
            password=hashed_password,
            building_id=building_id,
            flat_id=flat_id,
            known_face_encoding=known_encoding
        )
        new_user.save()

        token = jwt.encode({'_id': str(new_user.id)}, key=SECRET, algorithm='HS256')
        return jsonify({'message': 'OK', 'token': token}), 200
    except Exception as ex:
        print(ex)
        return jsonify({'message': 'Произошла неизвестная ошибка'}), 400

# Полная авторизация с распознаванием лица
@auth_bp.route('/login', methods=['POST'])
def login_handler():
    try:
        data = dict(request.get_json())
        login = data.get('additionalData', {}).get('login')
        password = data.get('additionalData', {}).get('password')
        image_b64 = data.get('image')

        user = User.objects.filter(email=login).first()
        if user is None:
            return jsonify({'message': 'Неверные email или пароль!'}), 400

        img_bytes = decode_base64_image(image_b64)
        img = face_recognition.load_image_file(io.BytesIO(img_bytes))
        if not user.check_face_encoding(img):
            return jsonify({'message': 'Пользователь не опознан!'}), 400

        if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            token = jwt.encode({'_id': str(user.id)}, key=SECRET, algorithm='HS256')
            return jsonify({'message': 'OK', 'token': token}), 200
        return jsonify({'message': 'Неверные email или пароль!'}), 401
    except Exception as ex:
        print(ex)
        return jsonify({'message': 'Произошла неизвестная ошибка'}), 401

# Проверка токена и получение информации о текущем пользователе
@auth_bp.route('/me', methods=['GET'])
@isAuthorized
def me(user: User):
    return jsonify({
        'message': 'OK',
        'user': {
            'login': user.email,
            'permissions': user.permissions,
            'is_blocked': user.is_blocked,
            'pump_broken': user.pump_broken,
            'button_state': user.button_state
        }
    }), 200

@auth_bp.route('/allUsers', methods=['GET'])
@isAuthorized
def allUsers(user):
    try:
        users = User.objects.all()

        users_data = [
            {
                'login': user.email,
                'permissions': user.permissions,
                'is_blocked': user.is_blocked,
                'pump_broken': user.pump_broken,
                'button_state': user.button_state
            }
            for user in users
        ]

        return jsonify({
            'message': 'OK',
            'users': users_data
        }), 200

    except Exception as ex:
        print(ex)
        return jsonify({'message': 'Произошла неизвестная ошибка'}), 500

