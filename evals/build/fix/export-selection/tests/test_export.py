import unittest
from export_rows import export_rows


class ExportTests(unittest.TestCase):
    def test_selected_invoice(self):
        invoice = {'id': 'A'}
        self.assertEqual(export_rows([invoice], {'A'}), [invoice])
