from app import app
from app.poller import start_polling
from app.monitor import start_monitoring

if __name__ == "__main__":
    # start_polling()

    start_monitoring(interval=30)
    app.run(debug=True, host="localhost", port="5000")