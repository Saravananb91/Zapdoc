import os
from test_case.load_gt import load_ground_truth
from test_case.run_pipeline import run_model
from test_case.field_metrics import exact_match
from test_case.item_metrics import item_accuracy
from test_case.summary_metrics import summary_accuracy

# BASE = r"C:\Users\HP Victus 16\ocr pipeline\backend\test_case"
IMAGES = r"C:\Users\HP Victus 16\ocr pipeline\backend\test_case\images"
PDFS = r"C:\Users\HP Victus 16\ocr pipeline\backend\test_case\pdfs"
GT_DIR = r"C:\Users\HP Victus 16\ocr pipeline\backend\test_case\ground_truth"

total = 0
invoice_ok = 0
item_scores = []
summary_scores = []

for folder in [IMAGES, PDFS]:
    if not os.path.exists(folder):
        continue

    for file in os.listdir(folder):
        file_path = os.path.join(folder, file)
        name = os.path.splitext(file)[0]
        gt_path = os.path.join(GT_DIR, name + ".json")

        if not os.path.exists(gt_path):
            print(f"GT missing for {file}")
            continue

        gt = load_ground_truth(gt_path)
        pred = run_model(file_path)

        total += 1

        # Invoice number test
        if exact_match(gt, pred, "invoice_no"):
            invoice_ok += 1

        # Item accuracy
        item_scores.append(
            item_accuracy(gt.get("items", []), pred.get("items", []))
        )

        # Summary accuracy
        summary_scores.append(
            summary_accuracy(gt.get("summary"), pred.get("summary"))
        )

import pprint
pprint.pprint(result["pages"][0])
exit()

print("\n===== TEST REPORT =====")
print("Total documents:", total)
print("Invoice No Accuracy:", invoice_ok / total)
print("Item Accuracy:", sum(item_scores) / len(item_scores))
print("Summary Accuracy:", sum(summary_scores) / len(summary_scores))
