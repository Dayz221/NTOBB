import requests
import time, paho.mqtt.client as mqtt

class Communicator:
    def __init__(self, api : str, token : str):
        self.api = api
        self.token = token
        self.headers =  {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        self.host = "dev.rightech.io"
        self.port = 1883

    def read_state(self, target_ID : str, topic : str):
        resp = requests.get(f"{self.api}/objects/{target_ID}", headers=self.headers)
        resp_json = resp.json()
        return resp_json.get("state") ['payload']

    def write_state(self, target_ID : str, topic : str, value, timeout = 1):
        cli = mqtt.Client(client_id=target_ID, protocol=mqtt.MQTTv311)
        cli.connect(self.host, self.port, keepalive=30)
        cli.publish(topic, value, qos=1, retain=True)
        time.sleep(timeout)
        cli.disconnect()

    def send_command(self, target_ID : str, command : str):
        data = {
            "target": target_ID,
            "state": 1,
        }
        resp = requests.post(f"{self.api}/objects/{target_ID}/commands/{command}", headers=self.headers,
                             json=data)
        return resp.json()


# TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI2ODA3MThlN2JmYjNlMTc4MWNhNjA0MzkiLCJzdWIiOiI2ODA3MTNiMWJmYjNlMTc4MWNhNjA0MzYiLCJncnAiOiI2ODA3MTNiMWJmYjNlMTc4MWNhNjA0MzUiLCJvcmciOiI2ODA3MTNiMWJmYjNlMTc4MWNhNjA0MzUiLCJsaWMiOiI1ZDNiNWZmMDBhMGE3ZjMwYjY5NWFmZTMiLCJ1c2ciOiJhcGkiLCJmdWxsIjpmYWxzZSwicmlnaHRzIjoxLjUsImlhdCI6MTc0NTI5NTU5MSwiZXhwIjoxNzQ3ODYxMjAwfQ.T22ktPLI0uhiRzwtccDVbV_82u8zLA80AnBgvccwkeg"
# cmt = Communicator("https://dev.rightech.io/api/v1", TOKEN)

# cmt.send_command("building_three", "SwitchOn_1")

print("Available commands:", cmt.list_commands("building_one"))