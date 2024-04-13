# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CounterReadingSteg(models.Model):
    _name = 'oscar.reading.counter.steg'
    _description = 'Rélevé de compteur STEG'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    # region Default methods
    def _default_magasin(self):
        if self.env.user.has_group("spc_oscar_aziza.group_reponsable_magasin"):
            return self.env['oscar.site'].search([('user_ids', 'child_of', [self.env.uid])], limit=1)

    # endregion

    name = fields.Char('Numéro', readonly=True, index=True, track_visibility='onchange')
    magasin_id = fields.Many2one('oscar.site', string='Magasin', required=True, index=True, default=_default_magasin, domain=[('site_type', '=', 'MAGASIN')], track_visibility='onchange')
    user_id = fields.Many2one('res.users', string='Responsable', required=True, index=True, default=lambda self: self.env.user)
    date_reading = fields.Datetime(string='Date de relèvement', required=True, index=True, default=lambda self: fields.Datetime.now())
    state = fields.Selection([('new', 'Nouveau'),
                              ('validate', 'Validé')], default='new', index=True, string="Statut", track_visibility='onchange')
    counter_ids = fields.Many2many('oscar.counter.steg', 'oscar_reading_counter_steg_rel', 'reading_id',
                                           'counter_id', string='Compteurs')
    comment = fields.Text(string='Commentaire', track_visibility='onchange')
    active = fields.Boolean(string='Activé', default=True)

    # region Constraints and Onchange
    @api.onchange('magasin_id')
    def onchange_counter(self):
        if self.magasin_id:
            self.counter_ids = [(6, None, self.magasin_id.counter_ids.ids)]
    # endregion

    # region CRUD (overrides)
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('spc.reading.counter.steg') or 'New'
        result = super(CounterReadingSteg, self).create(vals)
        return result
    # endregion

    # region Actions
    @api.multi
    def to_validate(self):
        return self.write({'state': 'validate'})
    # endregion
