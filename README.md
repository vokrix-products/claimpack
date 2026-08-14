# ClaimPack

ClaimPack is an extraction-only backend processor. Its archetype is the backend poller: it consumes uploaded claim documents and returns normalized claim records.

## What the poller expects as input

processor.process_file(file_bytes: bytes) accepts PDF, Excel (.xlsx), CSV, or plain text (UTF-8) bytes. Heuristic CSV/key-value parsing runs first; DeepSeek (deepseek-v4-flash) extraction is the fallback when DEEPSEEK_API_KEY is set. Unreadable input returns a record with status Unreadable.

## Output contract

Each record: title (customer name, else claim number, else order id), status, details (all extracted fields), due_date (ISO-8601 or null).

## Statuses

Missing, Expired, Valid, Flagged, Awaiting_Customer, Duplicate, Unreadable.

Dashboard: https://claimpack.vokrix.co
Vercel: claimpack
Railway: 0bfefa63-83af-4af3-b467-9d54a3e078c2
