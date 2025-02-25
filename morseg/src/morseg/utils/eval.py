def f_score(y, y_pred, boundary_symbol="+"):
    # check whether both inputs are lists
    if not (isinstance(y, list) and isinstance(y_pred, list)):
        raise ValueError("Type mismatch: Both reference and predicted words should be passed as lists, actually:"
                         f"\n    reference: {type(y)}\n    predicted: {type(y_pred)}")

    # check whether the same number of items are in both lists
    if len(y) != len(y_pred):
        raise ValueError(f"Dimension mismatch: Lists containing the predicted and reference segmentations"
                         f" should be of same length, actually: {len(y_pred)} predicted words, {len(y)} reference words")

    # keep track of true positives (tp), false positives (fp), and false negatives (fn)
    tp = 0
    fp = 0
    fn = 0

    # iterate over words, tying together predicted and actual segmentations
    for ref, pred in zip(y, y_pred):
        # words need to be represented as lists
        if not (isinstance(ref, list) and isinstance(pred, list)):
            raise ValueError("Type mismatch: Words should be represented as lists of segments, actually:"
                             f"\n    reference: {ref} {type(ref)}\n    predicted: {pred} {type(pred)}")

        # iterate over segments in the word
        ref_index = 0
        pred_index = 0
        while ref_index < len(ref) and pred_index < len(pred):
            ref_symbol = ref[ref_index]
            pred_symbol = pred[pred_index]

            # if both symbols match, consume them both
            if ref_symbol == pred_symbol:
                ref_index += 1
                pred_index += 1
                # if it is a boundary symbols, it is a true positive
                if ref_symbol == boundary_symbol:
                    tp += 1
            else:  # mismatch can only occur at boundaries (the actual segments are identical)
                if ref_symbol == boundary_symbol:
                    fn += 1
                    ref_index += 1
                elif pred_symbol == boundary_symbol:
                    fp += 1
                    pred_index += 1
                else:
                    raise ValueError(f"Mismatch between forms {ref} and {pred}: All segments other than the boundary "
                                     f"symbol need to be identical.")

    precision = tp / (tp + fp) if tp > 0 else 0.0
    recall = tp / (tp + fn) if tp > 0 else 0.0
    f1_score = 2 * ((precision * recall) / (precision + recall)) if (precision + recall) > 0 else 0.0

    return f1_score, precision, recall
