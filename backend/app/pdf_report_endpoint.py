from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from flask import Blueprint, request, jsonify
from datetime import datetime
import io
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader

from app.models import User
from app.config import RATE_PER_CUBIC_METER
from app.middleware.isAdmin import isAdmin
from app.middleware.isAuthorized import isAuthorized

pdf_bp = Blueprint('pdf_admin', __name__, url_prefix='/pdf')

@pdf_bp.route('/generate_report/<string:user_id>', methods=['POST'])
@isAdmin
# admin_user: текущий администратор, user_id: ID целевого пользователя
# Возвращает PDF-отчет по расходу воды и потреблению электричества

def generate_pdf_report(admin_user: User, user_id: str):
    # Парсим входные параметры
    data = request.get_json(silent=True) or {}
    start_ts = data.get('start_time')
    end_ts = data.get('end_time')

    if not start_ts or not end_ts:
        return jsonify({'message': 'Параметры start_time и end_time обязательны'}), 400

    try:
        start_ts = int(start_ts)
        end_ts = int(end_ts)
    except (ValueError, TypeError):
        return jsonify({'message': 'start_time и end_time должны быть целыми числами'}), 400

    if start_ts > end_ts:
        return jsonify({'message': 'start_time не может быть больше end_time'}), 400

    # Ищем пользователя по ID
    user = User.objects(id=user_id).first()
    if not user:
        return jsonify({'message': 'Пользователь не найден'}), 404

    user.leak = False

    # Фильтруем замеры
    filtered = [m for m in user.measures if start_ts <= m.timestamp <= end_ts]
    if not filtered:
        return jsonify({'message': 'Нет данных за указанный период'}), 404

    # Суммируем объем и ток
    total_water = sum(abs(m.volume) for m in filtered)
    total_electricity = sum(abs(m.current) for m in filtered)

    # Расчет стоимости
    water_price = total_water * RATE_PER_CUBIC_METER
    electricity_rate = 5.0  # руб. за кВт·ч (пример)
    electricity_price = total_electricity * electricity_rate
    total_cost = water_price + electricity_price

    # Генерация графика
    timestamps = [datetime.fromtimestamp(m.timestamp) for m in filtered]
    water_volumes = [m.volume for m in filtered]
    electricity_currents = [m.current for m in filtered]

    plt.figure(figsize=(10, 5))
    plt.plot(timestamps, water_volumes, label='Расход воды')
    plt.plot(timestamps, electricity_currents, label='Потребление тока')
    plt.xlabel('Время')
    plt.ylabel('Значение')
    plt.title('График потребления воды и тока')
    plt.legend()
    plt.grid()

    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)
    plt.close()

    # Создание PDF
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter

    c.setFont("arial", 16)
    c.drawString(50, height - 50, "Отчёт по потреблению ресурсов")

    c.setFont("arial", 12)
    c.drawString(50, height - 70, f"Пользователь ID: {user_id}")
    c.drawString(50, height - 90, f"Период: {datetime.fromtimestamp(start_ts)} - {datetime.fromtimestamp(end_ts)}")

    c.drawImage(ImageReader(img_buffer), 50, height - 300, width=500, height=200)

    c.drawString(50, height - 320, f"Общий расход воды: {total_water:.2f} м³")
    c.drawString(50, height - 340, f"Стоимость воды: {water_price:.2f} руб.")
    c.drawString(50, height - 360, f"Общее потребление тока: {total_electricity:.2f} кВт·ч")
    c.drawString(50, height - 380, f"Стоимость электричества: {electricity_price:.2f} руб.")
    c.drawString(50, height - 400, f"Итоговая стоимость: {total_cost:.2f} руб.")

    c.save()
    pdf_buffer.seek(0)

    return pdf_buffer.getvalue(), 200, {'Content-Type': 'application/pdf'}




@pdf_bp.route('/generate_report/<string:user_id>', methods=['POST'])
@isAdmin

def generate_pdf_report_(admin_user: User, user_id: str):
    return _build_and_send_report(user_id, admin_user.email if hasattr(admin_user, 'email') else user_id)

@pdf_bp.route('/generate_my_report', methods=['POST'])
@isAuthorized
# Эндпоинт для авторизованного пользователя: формирует собственный отчет
# user: текущий авторизованный пользователь

def generate_my_pdf_report(user: User):
    user_id = str(user.id)
    return _build_and_send_report(user_id, user.email)


def _build_and_send_report(user_id: str, user_label: str):
    # Парсим параметры из запроса

    # Регистрация шрифта Arial
    pdfmetrics.registerFont(TTFont('arial', 'path_to_your_font/arial.ttf'))

    # Теперь можно использовать Arial в drawString
    c.setFont("arial", 12)
    
    data = request.get_json(silent=True) or {}
    start_ts = data.get('start_ts')
    end_ts = data.get('end_ts')

    if not start_ts or not end_ts:
        return jsonify({'message': 'Параметры start_time и end_time обязательны'}), 400

    try:
        start_ts = int(start_ts)
        end_ts = int(end_ts)
    except (ValueError, TypeError):
        return jsonify({'message': 'start_time и end_time должны быть целыми числами'}), 400

    if start_ts > end_ts:
        return jsonify({'message': 'start_time не может быть больше end_time'}), 400

    # Ищем пользователя
    user = User.objects(id=user_id).first()
    if not user:
        return jsonify({'message': 'Пользователь не найден'}), 404

    # Фильтруем замеры
    filtered = [m for m in user.measures if start_ts <= m.timestamp <= end_ts]
    if not filtered:
        return jsonify({'message': 'Нет данных за указанный период'}), 404

    # Суммируем данные
    total_water = sum(abs(m.volume) for m in filtered)
    total_electricity = sum(abs(m.current) for m in filtered)

    # Расчет стоимости
    water_price = total_water * RATE_PER_CUBIC_METER
    electricity_rate = 5.0  # руб./кВт·ч
    electricity_price = total_electricity * electricity_rate

    # Генерация графика
    timestamps = [datetime.fromtimestamp(m.timestamp) for m in filtered]
    water_volumes = [m.volume for m in filtered]
    electricity_currents = [m.current for m in filtered]

    plt.figure(figsize=(10, 5))
    plt.plot(timestamps, water_volumes, label='Расход воды')
    plt.plot(timestamps, electricity_currents, label='Потребление тока')
    plt.xlabel('Время')
    plt.ylabel('Значение')
    plt.title('График потребления воды и тока')
    plt.legend()
    plt.grid()

    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)
    plt.close()

    # Создание PDF
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter

    c.setFont("Arial", 16)
    c.drawString(50, height - 50, "Отчёт по потреблению ресурсов")

    c.setFont("Arial", 12)
    c.drawString(50, height - 70, f"Пользователь: {user_label} (ID: {user_id})")
    c.drawString(50, height - 90, f"Период: {datetime.fromtimestamp(start_ts)} – {datetime.fromtimestamp(end_ts)}")

    c.drawImage(ImageReader(img_buffer), 50, height - 300, width=500, height=200)

    c.drawString(50, height - 320, f"Общий расход воды: {total_water:.2f} м³")
    c.drawString(50, height - 340, f"Стоимость воды: {water_price:.2f} руб.")
    c.drawString(50, height - 360, f"Общее потребление тока: {total_electricity:.2f} кВт·ч")
    c.drawString(50, height - 380, f"Стоимость электричества: {electricity_price:.2f} руб.")

    total_cost = water_price + electricity_price
    c.drawString(50, height - 400, f"Итоговая стоимость: {total_cost:.2f} руб.")

    c.save()
    pdf_buffer.seek(0)

    return pdf_buffer.getvalue(), 200, {'Content-Type': 'application/pdf'}


@pdf_bp.route('/payment/<int:user_id>', methods=['POST'])
@isAdmin
def payment (_user : User, user_id : int):
    user = User.objects(id=user_id).first()
    if not user:
        return jsonify({'message': 'Пользователь не найден'}), 404

    user.leak = True
    user.save()