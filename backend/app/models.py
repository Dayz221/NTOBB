from mongoengine import * 
import face_recognition


connect("NTO", host="localhost", port=27017)


class Measure(EmbeddedDocument):
    timestamp = IntField(required=True)
    volume = FloatField(required=True)
    current = FloatField(required=True)

class User(Document):
    email = StringField(required=True, unique=True)
    password = StringField(required=True)
    building_id = IntField(required=True, min_value=0, max_value=2)
    flat_id = IntField(required=True, min_value=0, max_value=4)
    measures = ListField(EmbeddedDocumentField(Measure))
    is_blocked = BooleanField(default=False)
    pump_broken = BooleanField(default=False)
    button_state = BooleanField(default=False)
    leak = BooleanField(default=False)
    paid = BooleanField(default=True)
    permissions = IntField(default=1)
    known_face_encoding = ListField(FloatField())

    def load_face_data(self, encodings):
        if not encodings:
            raise RuntimeError("Лицо не найдено на изображении")
        if len(encodings) > 1:
            raise RuntimeError("Найдено несколько лиц на изображении")
        self.known_face_encoding = [float(x) for x in encodings[0]]

    def check_face_encoding(self, encoding):
        face_locations = face_recognition.face_locations(encoding)
        face_encodings = face_recognition.face_encodings(encoding, face_locations, model='large')
        if not face_locations:
            return False

        for idx, ((top, right, bottom, left), face_encoding) in enumerate(zip(face_locations, face_encodings), 1):
            match = face_recognition.compare_faces([self.known_face_encoding], face_encoding, tolerance=0.5)[0]
            if match:
                return True

        return False

class Building(Document):
    water_bound = IntField(required=True)
    electricity_bound = IntField(required=True)
    building_id = IntField(required=True, unique=True, min_value=0)
    rightech_id = StringField(required=True, unique=True)
    pump_states = ListField(BooleanField(), default=lambda: [False] * 5, min_length=5, max_length=5)
    mode3_enabled = BooleanField(default=False)

################################### DEBUG ###################################
# if __name__ == "__main__":
#     user = User(email="rutuchenal37@gmail.com", password="1234", building_id=0, flat_id=4)
#     # user.load_face_data([1, 2, 3, 6])
#     user.save()