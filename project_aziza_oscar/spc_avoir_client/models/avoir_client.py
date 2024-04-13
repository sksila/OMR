# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime

class AvoirClient(models.Model):
    _name = 'oscar.avoir.client'
    _description = 'Avoir client'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "date desc"

    # region Default methods
    def _default_magasin(self):
        if self.env.user.has_group("spc_oscar_aziza.group_reponsable_magasin"):
            return self.env['oscar.site'].search([('user_ids', 'child_of', [self.env.uid])], limit=1)
    # endregion

    name = fields.Char('Index', readonly=True)
    magasin_id = fields.Many2one('oscar.site', string='Magasin', index=True, default=_default_magasin, required=True,
                                 domain=[('site_type', '=', 'MAGASIN')], track_visibility='onchange', readonly=True, states={'new': [('readonly', False)]})
    user_id = fields.Many2one('res.users', 'Responsable', default=lambda self: self.env.user,
                              index=True, required=True, track_visibility='onchange', readonly=True, states={'new': [('readonly', False)]})
    date = fields.Date(string="Date", default=datetime.today().date(), required=True, track_visibility='onchange', readonly=True, states={'new': [('readonly', False)]})
    customer_id = fields.Many2one('res.partner', string="Client", domain="[('customer','=',True)]", index=True
                                  , required=True, track_visibility='onchange', readonly=True, states={'new': [('readonly', False)]})
    phone = fields.Char(string="Téléphone", related='customer_id.phone', store=True, required=True, readonly=True, states={'new': [('readonly', False)]})
    number_avoir = fields.Char(string='N° de l’avoir', readonly=True, states={'new': [('readonly', False)]})
    comment = fields.Text(string='Commentaire')
    state = fields.Selection([('new', 'Nouveau'), ('validate', 'Validé')], default='new', index=True, string="Statut")
    active = fields.Boolean(string='Activé', default=True)

    # region CRUD (overrides)
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('spc.avoir.client') or 'New'
        result = super(AvoirClient, self).create(vals)
        return result
    # endregion

    # region Actions
    @api.multi
    def to_validate(self):
        return self.write({'state': 'validate'})
    # endregion

