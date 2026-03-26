from test_case.numeric_metrics import numeric_match

def summary_accuracy(gt_sum, pred_sum):
    if not gt_sum or not pred_sum:
        return 0.0

    checks = [
        numeric_match(gt_sum["net_total"], pred_sum["net_total"]),
        numeric_match(gt_sum["vat_total"], pred_sum["vat_total"]),
        numeric_match(gt_sum["gross_total"], pred_sum["gross_total"]),
    ]

    return sum(checks) / 3
