# coding: utf-8
# © 2017 Benoît GUILLOT @ Akretion <benoit.guillot@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.osv import orm, fields
from tools.translate import _
import cStringIO
import csv
import base64
import logging

_logger = logging.getLogger(__name__)

HEADER = [
    'Nom', 'Adresse', 'Code postal', 'Ville', 'Pays', u'Facture',
    'Date de facture', 'Date de livraison', 'Date de paiement', 'Devise',
    'Taux TVA', 'Montant Net', 'Montant TVA']


class AccountVATExport(orm.TransientModel):
    _name = 'account.vat.export'
    _description = "Wizard to export VAT"

    _columns = {
        'period_ids': fields.many2many(
            'account.period',
            'period_export_rel',
            'export_id',
            'period_id',
            string='Periods',
            required=True),
        'country_id': fields.many2one(
            'res.country',
            string='Country',
            required=True),
        'invoice_file': fields.binary(string='Invoice File'),
        'refund_file': fields.binary(string='Refund File'),
        'invoice_name': fields.char(string='Invoice File Name'),
        'refund_name': fields.char(string='Refund File Name'),
        }

    def _get_invoice_datas(self, cr, uid, invoice_ids, context=None):
        file = cStringIO.StringIO()
        writer = csv.writer(file, delimiter=';')
        writer.writerow(HEADER)
        inv_obj = self.pool['account.invoice']
        for invoice in inv_obj.browse(cr, uid, invoice_ids, context=context):
            address = invoice.address_shipping_id
            payment_date = invoice.payment_ids and min([x.date for x in invoice.payment_ids]) or invoice.date_invoice
            tax_rate = invoice.invoice_line[0].invoice_line_tax_id and invoice.invoice_line[0].invoice_line_tax_id[0].amount or 0
            row = [
                address.name.encode('utf-8'),
                address.street.encode('utf-8'),
                address.zip.encode('utf-8'),
                address.city.encode('utf-8'),
                address.country_id.name,
                invoice.number,
                invoice.date_invoice,
                invoice.date_invoice,
                payment_date,
                invoice.currency_id.name,
                tax_rate,
                invoice.amount_untaxed,
                invoice.amount_tax,
            ]
            try:
                writer.writerow(row)
            except:
                raise orm.except_orm(
                    _('Encoding Error'),
                    _('Encoding problem with invoice %s the datas are %s' % (invoice.number, row)))
        datas = base64.encodestring(file.getvalue())
        return datas

    def export_vat(self, cr, uid, ids, context=None):
        _logger.info('Start VAT export')
        inv_obj = self.pool['account.invoice']
        wizard = self.browse(cr, uid, ids[0], context=context)

        invoice_name = 'export_tva_factures_%s' % wizard.country_id.name
        refund_name = 'export_tva_avoirs_%s' % wizard.country_id.name
        period_ids = []
        for period in wizard.period_ids:
            invoice_name += '_%s' % period.name
            refund_name += '_%s' % period.name
            period_ids.append(period.id)
        invoice_name += '.csv'
        refund_name += '.csv'

        invoice_ids = inv_obj.search(
            cr, uid, [
                ('period_id', 'in', period_ids),
                ('country_shipping_id', '=', wizard.country_id.id),
                ('state', 'in', ['open', 'paid']),
                ('type', '=', 'out_invoice')], context=context)
        invoice_datas = self._get_invoice_datas(
            cr, uid, invoice_ids, context=context)

        refund_ids = inv_obj.search(
            cr, uid, [
                ('period_id', 'in', period_ids),
                ('country_shipping_id', '=', wizard.country_id.id),
                ('state', 'in', ['open', 'paid']),
                ('type', '=', 'out_refund')], context=context)
        refund_datas = self._get_invoice_datas(
            cr, uid, refund_ids, context=context)
        self.write(cr, uid, ids, {
            'invoice_file': invoice_datas,
            'invoice_name': invoice_name,
            'refund_file': refund_datas,
            'refund_name': refund_name}, context=context)
        return {
            'name': 'Export',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.vat.export',
            'res_id': ids[0],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'nodestroy': True,
            'context': context
        }