import realtime_vocal_ai
from realtime_vocal_ai import generate_eq_adjustments

bands = {
    "Sub": {"energy": 0.0, "target": 0.1},
    "Bass": {"energy": 0.0, "target": 0.2},
    "Mud": {"energy": 0.0, "target": 0.25},
    "Presence": {"energy": 0.0, "target": 0.2},
    "Bright": {"energy": 0.0, "target": 0.2},
    "Body": {"energy": 0.0, "target": 0.25},
}

for i in range(10):
    realtime_vocal_ai.history.append({"rms_db": -55.0, "bands": bands})

try:
    res = generate_eq_adjustments(bands, -55.0, 1.0)
    print("SUCCESS")
except Exception as e:
    import traceback
    traceback.print_exc()
