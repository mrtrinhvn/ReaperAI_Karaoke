import realtime_vocal_ai
from realtime_vocal_ai import generate_eq_adjustments
import collections

bands = {
    "Sub": {"energy": 0.0, "target": 0.1},
    "Bass": {"energy": 0.8, "target": 0.2},
    "Mud": {"energy": 0.05, "target": 0.25},
    "Presence": {"energy": 0.1, "target": 0.2},
    "Bright": {"energy": 0.05, "target": 0.2},
    "Body": {"energy": 0.1, "target": 0.25},
}

for i in range(10):
    realtime_vocal_ai.history.append({"rms_db": -33.2, "bands": bands})

try:
    res = generate_eq_adjustments(bands, -33.2, 1.0)
    print("SUCCESS")
except Exception as e:
    print(f"CRASH: {type(e).__name__}: {e}")
