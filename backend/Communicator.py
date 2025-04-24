import requests
import time, paho.mqtt.client as mqtt
import uuid

class Communicator:
    def __init__(self, api: str, token: str):
        self.api = api.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept":        "application/json",
            "Content-Type":  "application/json"
        }
        self.mqtt_host = "dev.rightech.io"
        self.mqtt_port = 1883

    def _http_get(self, path):
        url = f"{self.api}{path}"
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def _http_post(self, path, json_data=None):
        url = f"{self.api}{path}"
        r = requests.post(url, headers=self.headers, json=json_data)
        print(f"[HTTP POST] {url} → {r.status_code} {r.text}")
        r.raise_for_status()
        return r.json()

    def list_commands(self, target_ID: str) -> list[dict]:
        obj = self._http_get(f"/objects/{target_ID}")
        model_id = obj.get("model")
        if not model_id:
            raise RuntimeError(f"No model on object {target_ID}: {obj}")

        mdl = self._http_get(f"/models/{model_id}")

        for sect in mdl.get("data", {}).get("children", []):
            if sect.get("id") == "cmds":
                return sect.get("children", [])
        raise RuntimeError(f"No commands section in model {model_id}")

    def _flatten_commands(self, raw_cmds: list[dict]) -> dict[str, dict]:
        flat = {}
        def recurse(nodes):
            for node in nodes:
                if node.get("type") == "action":
                    flat[node["id"]] = node.get("params", {})
                for child in node.get("children", []):
                    recurse([child])
        recurse(raw_cmds)
        return flat

    def send_command(self, target_ID: str, cmd_id: str):
        raw = self.list_commands(target_ID)
        mapping = self._flatten_commands(raw)

        if cmd_id not in mapping:
            raise ValueError(f"Unknown command '{cmd_id}'. "
                             f"Available: {list(mapping)}")

        params = mapping[cmd_id]
        return self._http_post(f"/objects/{target_ID}/commands/{cmd_id}", json_data=params)

    def read_state(self, target_ID: str, topic: str):
        obj = self._http_get(f"/objects/{target_ID}")
        return obj.get("state", {}).get("payload")

    def write_state(self, target_ID: str, topic: str, value, timeout=1):
        client_id = f"{target_ID}_pub_{uuid.uuid4().hex[:8]}"
        cli = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311, clean_session=True)
        cli.connect(self.mqtt_host, self.mqtt_port, keepalive=30)
        cli.publish(topic, value, qos=1, retain=True)
        time.sleep(timeout)
        cli.disconnect()




############################## DEBUG ##############################
# API_URL = "https://dev.rightech.io/api/v1"
# TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI2ODA5Yjc3YWJmYjNlMTc4MWNhNjA1MDEiLCJzdWIiOiI2ODA5YjZlOWJmYjNlMTc4MWNhNjA0ZmQiLCJncnAiOiI2ODA5YjZlOWJmYjNlMTc4MWNhNjA0ZmMiLCJvcmciOiI2ODA5YjZlOWJmYjNlMTc4MWNhNjA0ZmMiLCJsaWMiOiI1ZDNiNWZmMDBhMGE3ZjMwYjY5NWFmZTMiLCJ1c2ciOiJhcGkiLCJmdWxsIjpmYWxzZSwicmlnaHRzIjoxLjUsImlhdCI6MTc0NTQ2NzI1OCwiZXhwIjoxNzQ4MDM0MDAwfQ.jFio63vrm3LnnJtFW9eHSmPOmSnTsD2nsN7W1t38pUQ"
# cmt = Communicator(API_URL, TOKEN)
#
# # cmt.write_state("building_one", "base/cmd/ON", 1)
# print(cmt.list_commands(target_ID="6809bdfebfb3e1781ca60503"))
# cmt.send_command("6809bdfebfb3e1781ca60503", "SwitchOn_1")
# cmt.send_command("6809bdfebfb3e1781ca60503", "SwitchOn_2")
# cmt.send_command("6809bdfebfb3e1781ca60503", "SwitchOn_3")
# cmt.send_command("6809bdfebfb3e1781ca60503", "SwitchOn_4")
# cmt.send_command("6809bdfebfb3e1781ca60503", "SwitchOn_5")
#
# time.sleep(2)
#
# cmt.send_command("6809bdfebfb3e1781ca60503", "SwitchOff_1")
# cmt.send_command("6809bdfebfb3e1781ca60503", "SwitchOff_2")
# cmt.send_command("6809bdfebfb3e1781ca60503", "SwitchOff_3")
# cmt.send_command("6809bdfebfb3e1781ca60503", "SwitchOff_4")
# cmt.send_command("6809bdfebfb3e1781ca60503", "SwitchOff_5")