import json

def load_ground_truth(gt_path):
    with open(gt_path, "r", encoding="utf-8") as f:
        return json.load(f)
