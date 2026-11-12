from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import Form, tagged


@tagged('post_install', '-at_install')
class TestCompanyJournalReset(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_data_2 = cls.setup_other_company()
        cls.company_2 = cls.company_data_2['company']
        cls.company_1 = cls.company_data['company']
        cls.sale_journal_1 = cls.company_data['default_journal_sale']
        cls.sale_journal_2 = cls.company_data_2['default_journal_sale']

    def _create_invoice(self, company):
        return self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_a.id,
            'company_id': company.id,
            'invoice_line_ids': [Command.create({'name': 'line', 'price_unit': 100})],
        })

    def test_write_company_resets_journal(self):
        move = self._create_invoice(self.company_1)
        self.assertEqual(move.journal_id, self.sale_journal_1)
        move.write({'company_id': self.company_2.id})
        self.assertEqual(move.company_id, self.company_2)
        self.assertEqual(move.journal_id, self.sale_journal_2)

    def test_write_other_fields_keeps_journal(self):
        move = self._create_invoice(self.company_1)
        move.write({'ref': 'changed'})
        self.assertEqual(move.journal_id, self.sale_journal_1)

    def test_create_with_foreign_journal_uses_company_journal(self):
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_a.id,
            'company_id': self.company_2.id,
            'journal_id': self.sale_journal_1.id,
            'invoice_line_ids': [Command.create({'name': 'line', 'price_unit': 100})],
        })
        self.assertEqual(move.company_id, self.company_2)
        self.assertEqual(move.journal_id, self.sale_journal_2)

    def test_onchange_company_resets_journal_on_new_move(self):
        with Form(self.env['account.move']) as move_form:
            move_form.move_type = 'out_invoice'
            move_form.company_id = self.company_1
            self.assertEqual(move_form.journal_id, self.sale_journal_1)
            move_form.company_id = self.company_2
            self.assertEqual(move_form.journal_id, self.sale_journal_2)
        move = move_form.save()
        self.assertEqual(move.company_id, self.company_2)
        self.assertEqual(move.journal_id, self.sale_journal_2)
