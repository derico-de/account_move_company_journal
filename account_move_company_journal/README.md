# Account Move: Journal follows company on draft moves

When the **company** of a draft `account.move` (invoice, bill, entry) is
changed while several companies are active — in the form or via quick edit
in the list — the **journal** of the previous company was kept. Saving then
failed the core company consistency check with:

> Invalid operation: "Draft Invoice" belongs to company "..." while "Journal"
> (journal_id: '...') belongs to another company.

The core onchange `_inverse_company_id` only reschedules `journal_id` on
already saved records; on new records the foreign journal survived until the
save constraint fired.

This module resets the journal to a suitable journal of the new company in
that case — in the form onchange, on `write` and on `create` — so changing
the company on a draft move just works.

## Installation

OCA-style layout: the addon lives in the subfolder
`src/custom/account_move_company_journal/account_move_company_journal/`
and is symlinked into `custom/account_move_company_journal/`, which is on
the Odoo addons path (`odoo-dev.conf`). Update the apps list and install
`account_move_company_journal`.

## Tests

```sh
# with the dev postgres running (see AGENTS.md), from the odoo-setup root:
./odoo/odoo-bin -c odoo-dev.conf -d <test_db> -i account_move_company_journal --test-enable --stop-after-init
```
