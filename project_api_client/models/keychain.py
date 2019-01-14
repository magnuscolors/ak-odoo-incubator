# -*- coding: utf-8 -*-
# Copyright 2016 Akretion (http://www.akretion.com)
# Benoit Guillot <benoit.guillot@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models


class KeychainAccount(models.Model):
    _inherit = 'keychain.account'

    namespace = fields.Selection(
        selection_add=[('support', 'Support')])

    def _support_init_data(self):
        return {}

    def _support_validate_data(self, data):
        return True
