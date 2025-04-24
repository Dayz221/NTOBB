from app import app
from app.poller import start_polling


if __name__ == "__main__":
    # запускаем фоновый опрос метрик
    # start_polling()

    # поднимаем веб-сервер
    app.run(debug=True, host="localhost", port="5000")
