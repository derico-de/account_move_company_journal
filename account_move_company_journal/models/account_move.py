from odoo import api, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _default_journal_of_company(self, company):
        """Journal of ``company`` suitable for the move type (core default lookup)."""
        self.ensure_one()
        journal_types = self._get_valid_journal_types()
        domain = [
            *self.env['account.journal']._check_company_domain(company),
            ('type', 'in', journal_types),
        ]
        journal = self.env['account.journal'].search(domain, limit=1)
        if not journal:
            raise UserError(self.env['account.journal']._build_no_journal_error_msg(
                company.display_name, journal_types,
            ))
        return journal

    @api.onchange('company_id')
    def _inverse_company_id(self):
        super()._inverse_company_id()
        # The core onchange only reschedules journal_id on saved records. On new
        # records the journal of the previous company is kept and saving then
        # fails the company consistency check. Reset it here as well.
        for move in self:
            if (
                move.state == 'draft'
                and move.journal_id
                and move.journal_id.company_id != move.company_id
            ):
                try:
                    move.journal_id = move._search_default_journal()
                except UserError:
                    # No suitable journal in the new company; keep the old one, the
                    # save then raises a clear "no journal found" error.
                    pass

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            journal = self.env['account.journal'].browse(vals.get('journal_id'))
            if 'company_id' in vals and journal:
                company = self.env['res.company'].browse(vals['company_id'])
                if journal.company_id != company:
                    probe = self.new({key: vals[key] for key in (
                        'move_type', 'origin_payment_id', 'statement_line_id',
                    ) if key in vals})
                    vals['journal_id'] = probe._default_journal_of_company(company).id
        return super().create(vals_list)

    def write(self, vals):
        company_id = vals.get('company_id')
        if company_id:
            company = self.env['res.company'].browse(company_id)
            journal_val = vals.get('journal_id')
            vals_journal = self.env['account.journal'].browse(journal_val) \
                if isinstance(journal_val, int) else self.env['account.journal']

            def journal_mismatch(move):
                journal = vals_journal if journal_val else move.journal_id
                return move.state == 'draft' and journal and journal.company_id != company

            to_fix = self.filtered(journal_mismatch)
            if to_fix:
                rest = self - to_fix
                if rest:
                    super(AccountMove, rest).write(vals)
                for move in to_fix:
                    move_vals = dict(vals)
                    move_vals['journal_id'] = move._default_journal_of_company(company).id
                    super(AccountMove, move).write(move_vals)
                return True
        return super().write(vals)
