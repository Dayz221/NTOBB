from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# регистрируем Blueprints
from app.Users_EndPoints   import user_bp
from app.autentification   import auth_bp    # если вы тоже переведёте auth в Blueprint
from app.mqtt_connector    import mqtt_bp    # аналогично для MQTT
from app.PDFs              import pdf_bp

app.register_blueprint(user_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(mqtt_bp)
app.register_blueprint(pdf_bp)

# старт фонового опроса
from app.poller import start_polling
start_polling()

@app.route("/", methods=["GET"])
def greeting():
    return jsonify({"message": "Бэкэнд команды Techno Forces"})
