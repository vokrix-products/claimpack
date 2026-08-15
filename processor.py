"""ClaimPack processor.

Converts uploaded PDF, Excel, CSV and plain text bytes into normalized claim records.
"""

import csv
import io
import json
import os
import re
from datetime import date, datetime

import openpyxl
import pdfplumber
from openai import OpenAI

STATUS_VALUES = [
    "Missing",
    "Expired",
    "Valid",
    "Flagged",
    "Awaiting_Customer",
    "Duplicate",
    "Unreadable",
]

EXTRACTED_FIELDS = [
    "claim_number",
    "customer_name",
    "customer_first_name",
    "customer_last_name",
    "customer_email",
    "order_id",
    "invoice_number",
    "product_sku",
    "product_name",
    "purchase_date",
    "warranty_expiration_date",
    "claim_received_date",
    "defect_description",
    "failure_code",
    "requested_action",
    "document_type",
    "document_date",
    "document_status",
    "duplicate_claim_id",
    "status",
    "due_date",
    "claim_amount",
]

REQUIRED_FIELDS_FOR_VALID = [
    "claim_number",
    "customer_first_name",
    "customer_last_name",
    "customer_email",
    "order_id",
    "invoice_number",
    "product_sku",
    "product_name",
    "purchase_date",
    "warranty_expiration_date",
    "claim_received_date",
    "defect_description",
    "requested_action",
    "document_type",
]

MODEL_NAME = "deepseek-v4-flash"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

FIELD_ALIASES = {
    "claim_number": ["claim_number", "claimnumber", "claim_no", "claimno", "claim_num", "claimid", "claim_id"],
    "customer_name": ["customer_name", "customername", "customer", "name", "full_name", "fullname"],
    "customer_first_name": ["customer_first_name", "first_name", "firstname", "customerfirstname", "customer_firstname"],
    "customer_last_name": ["customer_last_name", "last_name", "lastname", "customerlastname", "customer_lastname"],
    "customer_email": ["customer_email", "email", "email_address", "customeremail"],
    "order_id": ["order_id", "orderid", "order_number", "orderno", "order_num"],
    "invoice_number": ["invoice_number", "invoicenumber", "invoice_no", "invoiceno", "invoice_num", "invoice"],
    "product_sku": ["product_sku", "sku", "productsku", "item_sku"],
    "product_name": ["product_name", "productname", "product", "item_name"],
    "purchase_date": ["purchase_date", "purchasedate", "date_of_purchase"],
    "warranty_expiration_date": ["warranty_expiration_date", "warrantyexpirationdate", "warranty_expiration", "warranty_end", "warranty_end_date", "expiration_date"],
    "claim_received_date": ["claim_received_date", "claimreceiveddate", "claim_date", "date_received", "received_date"],
    "defect_description": ["defect_description", "defectdescription", "defect", "description", "issue"],
    "failure_code": ["failure_code", "failurecode", "error_code", "fault_code"],
    "requested_action": ["requested_action", "requestedaction", "action_requested", "request"],
    "document_type": ["document_type", "documenttype", "doc_type"],
    "document_date": ["document_date", "documentdate", "doc_date"],
    "document_status": ["document_status", "documentstatus", "doc_status"],
    "duplicate_claim_id": ["duplicate_claim_id", "duplicateclaimid", "duplicate_claim", "duplicate_id"],
    "status": ["status", "claim_status", "claimstatus", "record_status"],
    "due_date": ["due_date", "duedate", "due", "deadline"],
    "claim_amount": ["claim_amount", "claimamount", "amount", "claim_value", "claimvalue", "total", "value"],
}

_ALIAS_TO_FIELD = {}
for _field, _aliases in FIELD_ALIASES.items():
    for _alias in _aliases:
        normalized_alias = re.sub(r"[^a-z0-9]+", "_", _alias.strip().lower()).strip("_")
        _ALIAS_TO_FIELD[normalized_alias] = _field


def _normalize_header(value):
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def _alias_to_field(header):
    return _ALIAS_TO_FIELD.get(_normalize_header(header))


def _clean_value(value):
    """Strip markdown / formatting artifacts from extracted values.

    Test documents frequently use markdown-style emphasis around field
    values (e.g. "** WC-2024-08731", "**John**", "`ABC123`"). Normalize so
    no raw asterisks, backticks or bullets leak into record titles/details.
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return text

    # strip wrapping bold/italic/code markers: **x**, *x*, `x`
    text = re.sub(r"^\s*\*+\s*", "", text)
    text = re.sub(r"\s*\*+\s*$", "", text)
    text = re.sub(r"^`+|`+$", "", text)

    # remove any remaining asterisk runs inside the value
    text = re.sub(r"\*+", "", text)

    # remove markdown header markers and list bullets at the start
    text = re.sub(r"^\s*(#{1,6}\s*|[-•]\s*|>\s*)", "", text)

    return text.strip()


def _parse_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    text = str(value).strip()
    if not text:
        return None

    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%m-%d-%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _iso_date(value):
    parsed = _parse_date(value)
    return parsed.isoformat() if parsed else None


def _extract_text(file_bytes):
    if file_bytes.startswith(b"%PDF"):
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)
                if text.strip():
                    return text
        except Exception:
            pass

    try:
        workbook = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        lines = []
        for worksheet in workbook.worksheets:
            for row in worksheet.iter_rows(values_only=True):
                values = []
                for cell in row:
                    if cell is None:
                        values.append("")
                    else:
                        values.append(str(cell).replace("\t", " ").replace("\n", " "))
                lines.append("\t".join(values))
        text = "\n".join(lines)
        if text.strip():
            return text
    except Exception:
        pass

    try:
        return file_bytes.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _parse_key_value(text):
    record = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if ":" in line:
            key, value = line.split(":", 1)
        elif "=" in line:
            key, value = line.split("=", 1)
        else:
            continue

        field = _alias_to_field(key)
        if field:
            record[field] = _clean_value(value)

    if record:
        return [record]
    return []


def _parse_claims(text):
    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;|")
        rows = list(csv.reader(io.StringIO(text), dialect))
    except Exception:
        return _parse_key_value(text)

    if not rows:
        return []

    header = rows[0]
    mapped_header = [_alias_to_field(cell) for cell in header]

    if not any(mapped_header):
        return _parse_key_value(text)

    records = []
    for row in rows[1:]:
        if not row:
            continue

        record = {}
        for field, value in zip(mapped_header, row):
            if field:
                record[field] = _clean_value(value)

        if any(record.get(field) for field in record):
            records.append(record)

    if records:
        return records

    return _parse_key_value(text)


def _build_title(details):
    first_name = str(details.get("customer_first_name") or "").strip()
    last_name = str(details.get("customer_last_name") or "").strip()

    if first_name or last_name:
        return f"{first_name} {last_name}".strip()

    customer_name = str(details.get("customer_name") or "").strip()
    if customer_name:
        return customer_name

    return str(
        details.get("claim_number")
        or details.get("order_id")
        or "Unknown Claimant"
    ).strip()


def _derive_status(details):
    if details.get("duplicate_claim_id"):
        return "Duplicate"

    has_name = bool(
        str(details.get("customer_first_name") or "").strip()
        or str(details.get("customer_last_name") or "").strip()
        or str(details.get("customer_name") or "").strip()
    )
    missing_fields = [
        field
        for field in REQUIRED_FIELDS_FOR_VALID
        if field not in ("customer_first_name", "customer_last_name")
        and not str(details.get(field) or "").strip()
    ]
    if not has_name:
        missing_fields.extend(["customer_first_name", "customer_last_name"])
    if missing_fields:
        return "Missing"

    purchase_date = _parse_date(details.get("purchase_date"))
    claim_date = _parse_date(details.get("claim_received_date"))
    warranty_date = _parse_date(details.get("warranty_expiration_date"))

    if claim_date and warranty_date and claim_date > warranty_date:
        return "Expired"

    if purchase_date and claim_date and purchase_date > claim_date:
        return "Flagged"

    email = str(details.get("customer_email") or "")
    if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return "Flagged"

    document_status = str(details.get("document_status") or "").strip().lower()
    if document_status in [
        "awaiting_customer",
        "awaiting",
        "requested",
        "requested_customer",
        "pending_customer",
    ]:
        return "Awaiting_Customer"

    return "Valid"


def _build_record_from_flat(data):
    details = {}
    for field in EXTRACTED_FIELDS:
        if field in data:
            details[field] = _clean_value(data.get(field))

    title = _build_title(details)
    due_date = (
        _iso_date(details.get("due_date"))
        or _iso_date(details.get("warranty_expiration_date"))
        or _iso_date(details.get("claim_received_date"))
    )
    explicit_status = str(details.get("status") or "").strip()
    status = explicit_status if explicit_status in STATUS_VALUES else _derive_status(details)

    return {
        "title": title,
        "status": status,
        "details": details,
        "due_date": due_date,
    }


def _make_record_from_dict(data):
    if isinstance(data, dict) and "details" in data and "title" in data and "status" in data:
        details = data.get("details") or {}
        if isinstance(details, dict) and isinstance(details.get("details"), dict):
            # LLM sometimes returns a redundantly nested "details" object;
            # flatten it so extracted fields sit at the top level.
            inner = details.pop("details")
            details.update(inner)
        details.pop("title", None)
        details.pop("status", None)
        details.pop("due_date", None)

        title = _clean_value(data.get("title")) or _build_title(details)
        status = data.get("status")
        if status not in STATUS_VALUES:
            status = _derive_status(details)

        due_date = _iso_date(data.get("due_date")) or _iso_date(
            details.get("warranty_expiration_date")
        ) or _iso_date(details.get("claim_received_date"))

        return {
            "title": str(title),
            "status": status,
            "details": details,
            "due_date": due_date,
        }

    return _build_record_from_flat(data)


def _apply_duplicate_heuristics(records):
    seen_order_ids = set()
    seen_invoice_numbers = set()

    for record in records:
        details = record.get("details") or {}
        if record.get("status") == "Unreadable":
            continue

        order_id = str(details.get("order_id") or "").strip()
        invoice_number = str(details.get("invoice_number") or "").strip()

        is_duplicate = False

        if order_id:
            if order_id in seen_order_ids:
                is_duplicate = True
            else:
                seen_order_ids.add(order_id)

        if invoice_number:
            if invoice_number in seen_invoice_numbers:
                is_duplicate = True
            else:
                seen_invoice_numbers.add(invoice_number)

        if is_duplicate:
            record["status"] = "Duplicate"
            if not details.get("duplicate_claim_id"):
                details["duplicate_claim_id"] = "DUPLICATE_IN_FILE"
            record["details"] = details

    return records


def _build_unreadable_record(reason):
    return [
        {
            "title": "Unknown Claimant",
            "status": "Unreadable",
            "details": {"error": reason},
            "due_date": None,
        }
    ]


def process_file(file_bytes: bytes) -> list[dict]:
    if not isinstance(file_bytes, bytes):
        return _build_unreadable_record("process_file expects bytes")

    text = _extract_text(file_bytes)
    if not text.strip():
        return _build_unreadable_record("No text could be extracted from the file")

    parsed = _parse_claims(text)
    if not parsed:
        parsed = _extract_with_deepseek(text)

    if not parsed:
        return _build_unreadable_record("No claim fields could be parsed")

    records = [_make_record_from_dict(item) for item in parsed]
    return _apply_duplicate_heuristics(records)


__all__ = ["process_file", "STATUS_VALUES"]
