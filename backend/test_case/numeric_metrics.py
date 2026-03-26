def numeric_match(gt_val, pred_val, tolerance=0.01):
    if gt_val is None or pred_val is None:
        return False
    return abs(gt_val - pred_val) <= tolerance
