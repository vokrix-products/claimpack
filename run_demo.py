from processor import process_file


def main():
    test_bytes = (
        b"claim_number,customer_first_name,customer_last_name,customer_email,order_id,"
        b"invoice_number,product_sku,product_name,purchase_date,warranty_expiration_date,"
        b"claim_received_date,defect_description,failure_code,requested_action,document_type,"
        b"document_date,document_status,duplicate_claim_id\n"
        b"CLM-1001,Jane,Doe,jane.doe@example.com,ORD-9001,INV-5001,SKU-ACME-4K,"
        b"Acme 4K Action Camera,2024-01-15,2025-01-15,2024-06-01,"
        b"Unit overheats during charging,THERMAL,Replacement,claim_form,2024-06-01,complete,\n"
    )

    results = process_file(test_bytes)

    assert isinstance(results, list), "process_file must return a list"
    assert len(results) == 1, "expected one claim record"

    record = results[0]
    assert record["status"] == "Valid", record
    assert record["title"] == "Jane Doe", record
    assert record["due_date"] == "2025-01-15", record
    assert record["details"]["claim_number"] == "CLM-1001", record

    print("demo ok")
    print(record)


if __name__ == "__main__":
    main()
