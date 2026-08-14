"""ClaimPack poller.

Polls the shared jobs table for pending claimpack process_upload jobs,
downloads the uploaded document from Supabase Storage, runs the claim
processor, writes normalized records into the records table, and marks
the job completed.
"""

import os
import time
from datetime import datetime, timezone

import requests
import processor

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
PRODUCT_ID = os.environ["PRODUCT_ID"]
POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "60"))
SUPABASE_REST = f"{SUPABASE_URL}/rest/v1"


def get_headers():
    return {
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "apikey": SUPABASE_SERVICE_KEY,
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }


def download_file(bucket, file_path):
    if file_path.startswith(bucket + "/"):
        file_path = file_path[len(bucket) + 1:]
    url = f"{SUPABASE_URL}/storage/v1/object/{bucket}/{file_path}"
    resp = requests.get(
        url,
        headers={"Authorization": f"Bearer {SUPABASE_SERVICE_KEY}", "apikey": SUPABASE_SERVICE_KEY},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.content


def update_job(job_id, payload):
    url = f"{SUPABASE_REST}/jobs?id=eq.{job_id}"
    resp = requests.patch(url, headers=get_headers(), json=payload, timeout=30)
    resp.raise_for_status()


def insert_records(rows):
    url = f"{SUPABASE_REST}/records"
    resp = requests.post(url, headers=get_headers(), json=rows, timeout=60)
    resp.raise_for_status()


def process_job(job):
    job_id = job.get("id")
    customer_id = job.get("customer_id")
    input_path = job.get("input_file_path") or ""
    try:
        if not input_path:
            raise ValueError("No input file path on job")
        file_bytes = download_file("uploads", input_path)
        records = processor.process_file(file_bytes)
        if not records:
            raise ValueError("No records extracted")

        rows = []
        for rec in records:
            row = {
                "product_id": PRODUCT_ID,
                "customer_id": customer_id,
                "title": rec.get("title") or "Unknown Claimant",
                "status": rec.get("status") or "Unreadable",
                "details": rec,
                "source_file_path": input_path,
            }
            if rec.get("due_date"):
                row["due_date"] = rec["due_date"]
            rows.append(row)

        insert_records(rows)
        update_job(job_id, {
            "status": "completed",
            "result_summary": f"Processed {len(rows)} records",
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })
        print(f"completed job {job_id}: {len(rows)} records")
    except Exception as exc:
        now = datetime.now(timezone.utc).isoformat()
        try:
            update_job(job_id, {
                "status": "failed",
                "result_summary": str(exc)[:500],
                "error_message": str(exc)[:500],
                "completed_at": now,
            })
        except Exception:
            pass
        print(f"failed job {job_id}: {exc}")


def poll():
    while True:
        try:
            params = {
                "select": "*",
                "status": "eq.pending",
                "product_id": f"eq.{PRODUCT_ID}",
                "order": "created_at.asc",
            }
            resp = requests.get(
                f"{SUPABASE_REST}/jobs",
                headers=get_headers(),
                params=params,
                timeout=30,
            )
            resp.raise_for_status()
            for job in resp.json():
                process_job(job)
        except Exception:
            pass
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    print(f"ClaimPack poller started (product_id={PRODUCT_ID})")
    poll()
