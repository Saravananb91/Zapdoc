def exact_match(gt, pred, field):
    """
    Returns True if field matches exactly
    """
    return gt.get(field) == pred.get(field)
