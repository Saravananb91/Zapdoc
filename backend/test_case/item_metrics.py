from test_case.numeric_metrics import numeric_match

def item_accuracy(gt_items, pred_items):
    if not gt_items:
        return 1.0  # nothing to compare

    matched = 0

    for gt in gt_items:
        for pr in pred_items:
            if gt["description"][:25].lower() in pr["description"].lower():
                if numeric_match(
                    gt["gross_amount"],
                    pr["gross_amount"]
                ):
                    matched += 1
                    break

    return matched / len(gt_items)
