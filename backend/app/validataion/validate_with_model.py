import os
import csv
from app.ocr.pipeline import process_document

# -----------------------------
# VALIDATION UTILITIES
# -----------------------------

def is_present(val):
    return val not in (None, "", [], {})

def safe_sum(values):
    return round(sum(v for v in values if isinstance(v, (int, float))), 2)


def completeness_check(structured):
    fields = [
        structured.get("invoice_no"),
        structured.get("date_of_issue"),
        structured.get("seller", {}).get("name"),
        structured.get("client", {}).get("name"),
        structured.get("items"),
        structured.get("summary"),
    ]
    present = sum(1 for f in fields if is_present(f))
    return round(present / len(fields) * 100, 2)


def consistency_check(structured, tol=0.05):
    items = structured.get("items", [])
    summary = structured.get("summary")

    if not items or not summary:
        return "SKIPPED"

    net_items = safe_sum([i.get("net_amount") for i in items])
    gross_items = safe_sum([i.get("gross_amount") for i in items])

    net_ok = abs(net_items - summary.get("net_total", 0)) <= tol
    gross_ok = abs(gross_items - summary.get("gross_total", 0)) <= tol

    return "PASS" if net_ok and gross_ok else "FAIL"


def sanity_check(structured):
    issues = []

    if structured.get("invoice_no") and not str(structured["invoice_no"]).isdigit():
        issues.append("INVALID_INVOICE_NO")

    for item in structured.get("items", []):
        if item.get("qty") is not None and item["qty"] <= 0:
            issues.append("INVALID_QTY")
        if item.get("gross_amount") is not None and item["gross_amount"] <= 0:
            issues.append("INVALID_AMOUNT")

    return issues


# -----------------------------
# MAIN RUNNER (MODEL CONNECTED)
# -----------------------------

def validate_invoices_with_model(image_folder, output_csv):
    rows = []

    for fname in os.listdir(image_folder):
        if not fname.lower().endswith((".jpg", ".png", ".jpeg", ".pdf")):
            continue

        file_path = os.path.join(image_folder, fname)
        print(f"Processing: {fname}")

        # 🔥 CALL YOUR OCR MODEL HERE
        result = process_document(file_path)

        # Assume single-page invoices
        page = result["pages"][0]
        structured = page["ocr"]["structured_data"]

        completeness = completeness_check(structured)
        consistency = consistency_check(structured)
        sanity = sanity_check(structured)

        flagged = (
            completeness < 70
            or consistency == "FAIL"
            or len(sanity) > 0
        )

        rows.append({
            "invoice_file": fname,
            "invoice_no": structured.get("invoice_no"),
            "completeness_%": completeness,
            "consistency": consistency,
            "sanity_issues": "|".join(sanity) if sanity else "",
            "flagged_for_review": flagged
        })

    # Write CSV report
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print("Validation finished")
    print(f"Total invoices: {len(rows)}")
    print(f"Flagged for review: {sum(1 for r in rows if r['flagged_for_review'])}")


# -----------------------------
# ENTRY POINT
# -----------------------------

if __name__ == "__main__":
    validate_invoices_with_model(
        image_folder=r"E:\demo projects\zuberaa\imagess",      # folder with 50 bills
        output_csv="ocr_validation_report.csv"
    )
