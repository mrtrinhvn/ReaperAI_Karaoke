import realtime_vocal_ai
from realtime_vocal_ai import generate_eq_adjustments
bands = {
    "Sub": {"energy": 0.0, "target": 0.1},
    "Bass": {"energy": 0.8, "target": 0.2},
    "Mud": {"energy": 0.05, "target": 0.25},
    "Presence": {"energy": 0.1, "target": 0.2},
    "Bright": {"energy": 0.05, "target": 0.2},
    "Body": {"energy": 0.1, "target": 0.25},
}
res = generate_eq_adjustments(bands, -33.2, 1.0)
print(res)
