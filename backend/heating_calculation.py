from datetime import datetime
from app import app
from flask import request, jsonify
from app.models import User
from app.middleware.isAuthorized import isAuthorized
from app.config import RATE_PER_CUBIC_METER

@app.route("/calc/price_evaluation", methods=["GET"])
@isAuthorized
def price_calculation(user: User):
    # Получаем параметры периода из query
    start_str = request.args.get("start")  # формат timestamp
    end_str = request.args.get("end")

    if not start_str or not end_str:
        return jsonify({"error": "Параметры start и end обязательны"}), 400

    try:
        start = datetime.fromtimestamp(float(start_str))
        end = datetime.fromtimestamp(float(end_str))
    except ValueError:
        return jsonify({"error": "Неверный формат timestamp. Используйте правильный формат"}), 400

    # Фильтруем записи в указанном интервале
    filtered_measures = [
        m for m in user.measures
        if start <= datetime.fromisoformat(m["timestamp"]) <= end
    ]

    # Подсчитываем общий объём потреблённой воды
    total_volume = sum(m.get("water_volume", 0) for m in filtered_measures)

    # Считаем стоимость
    total_price = total_volume * RATE_PER_CUBIC_METER

    return jsonify({
        "total_volume": total_volume,
        "total_price": round(total_price, 2),
        "rate": RATE_PER_CUBIC_METER,
        "start": start.timestamp(),
        "end": end.timestamp()
    })
