import unittest

from processor import process_file


VALID_CSV = (
    b"claim_number,customer_first_name,customer_last_name,customer_email,order_id,"
    b"invoice_number,product_sku,product_name,purchase_date,warranty_expiration_date,"
    b"claim_received_date,defect_description,failure_code,requested_action,document_type,"
    b"document_date,document_status,duplicate_claim_id\n"
    b"CLM-1001,Jane,Doe,jane.doe@example.com,ORD-9001,INV-5001,SKU-ACME-4K,"
    b"Acme 4K Action Camera,2024-01-15,2025-01-15,2024-06-01,"
    b"Unit overheats during charging,THERMAL,Replacement,claim_form,2024-06-01,complete,\n"
)


class ProcessorTests(unittest.TestCase):
    def test_valid_csv(self):
        records = process_file(VALID_CSV)
        self.assertIsInstance(records, list)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["status"], "Valid")
        self.assertEqual(records[0]["title"], "Jane Doe")
        self.assertEqual(records[0]["due_date"], "2025-01-15")
        self.assertEqual(records[0]["details"]["claim_number"], "CLM-1001")

    def test_missing_fields(self):
        data = b"claim_number,customer_first_name\nCLM-2002,Jane\n"
        records = process_file(data)
        self.assertEqual(records[0]["status"], "Missing")

    def test_unreadable_empty_input(self):
        records = process_file(b"")
        self.assertEqual(records[0]["status"], "Unreadable")

    def test_expired_warranty(self):
        data = (
            b"claim_number,customer_first_name,customer_last_name,customer_email,order_id,"
            b"invoice_number,product_sku,product_name,purchase_date,warranty_expiration_date,"
            b"claim_received_date,defect_description,failure_code,requested_action,document_type,"
            b"document_date,document_status,duplicate_claim_id\n"
            b"CLM-3003,Jane,Doe,jane.doe@example.com,ORD-9003,INV-5003,SKU-ACME-4K,"
            b"Acme 4K Action Camera,2024-01-15,2024-12-31,2025-01-10,"
            b"Unit overheats during charging,THERMAL,Replacement,claim_form,2025-01-10,complete,\n"
        )
        records = process_file(data)
        self.assertEqual(records[0]["status"], "Expired")


if __name__ == "__main__":
    unittest.main()
