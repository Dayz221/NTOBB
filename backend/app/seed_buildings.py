from app.models import Building

def seed_buildings():
    data = [
        {"building_id": 0, "water_bound": 10, "electricity_bound" : 228, "rightech_id": "6809bdfebfb3e1781ca60503"},
        {"building_id": 1, "water_bound": 10, "electricity_bound" : 228, "rightech_id": "680a062c20b46dbb6c1f66d3"},
        {"building_id": 2, "water_bound": 10, "electricity_bound" : 228, "rightech_id": "680a065420b46dbb6c1f66d4"},
    ]
    for item in data:
        Building.objects(building_id=item["building_id"]).upsert_one(
            set__water_bound=item["water_bound"],
            set__rightech_id=item["rightech_id"]
        )
