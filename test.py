import realtime_vocal_ai
from realtime_vocal_ai import generate_eq_adjustments
import json

bands = {
    "Sub": {"energy": 0.5, "target": 0.1},
    "Mud": {"energy": 0.05, "target": 0.25},
    "Presence": {"energy": 0.1, "target": 0.2},
    "Bright": {"energy": 0.1, "target": 0.2},
    "Body": {"energy": 0.2, "target": 0.25},
}
res = generate_eq_adjustments(bands, -14.1, 1.0)
print("SUCCESS!")
