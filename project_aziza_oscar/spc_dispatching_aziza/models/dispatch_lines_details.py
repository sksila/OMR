# -*- coding: utf-8 -*-

from odoo import api, fields, models,_

_STATES = [
    ('draft', 'Demande de dispatching'),
    ('to_approve', 'Approbation marchandise'),
    ('approved', 'Approbation exploitation'),
    ('verification', 'Dispatching exploitation'),
    ('verification_2', 'Vérification'),
    ('done', 'Clôturé'),
    ('rejected', 'Rejeté')
]

class DispatchLinesDetails(models.Model):
    _name = "oscar.dispatch.lines.details"
    _description = "Details des lignes de dispatch"
    _inherit = ['mail.thread']
    _mail_post_access = 'read'
    _order = "id desc"

    name = fields.Char("Description")
    entrepot_id = fields.Many2one('oscar.site', 'Entrepot', required=True, domain=[('site_type', '=', 'ENTREPOT')])
    qty_estimated = fields.Integer("Qté à dispatcher", required=True)
    qty_dispatched = fields.Integer("Qté  dispatchée")
    qty_ecart = fields.Integer("Écart 1", compute='_compute_qty', store=True)
    motif_ecart = fields.Char("Motif Écart 1")
    dispatch_line_id = fields.Many2one('oscar.dispatch.lines', 'Ligne de dispatch')
    origin = fields.Char('Réf demande', related='dispatch_line_id.origin')
    product_id = fields.Many2one('product.template', string='Code Article', related='dispatch_line_id.product_id')
    designation_article = fields.Char('Designation Article', related='dispatch_line_id.designation_article')
    requested_by = fields.Many2one('res.users',
                                   string='Approvisionneur',
                                   default=lambda self: self.env.uid,
                                   index=True, track_visibility='always', readonly=True,
                                   related='dispatch_line_id.requested_by')
    date_dispatch = fields.Datetime(string="Date", default=fields.Datetime.now,
                                    related='dispatch_line_id.date_dispatch')
    category_id = fields.Many2one('product.category', 'Categorie', related='dispatch_line_id.category_id')
    sub_category_id = fields.Many2one('product.category', 'Famille', related='dispatch_line_id.sub_category_id')
    state = fields.Selection(selection=_STATES,
                             string='Status',
                             index=True,
                             track_visibility='onchange',
                             default='draft',
                             copy=False,
                             related='dispatch_line_id.state', store=True, readonly=True)
    qty_reel_dispatched = fields.Integer("Qté réellement livrée")
    qty_reel_ecart = fields.Integer("Écart 2", compute="_compute_qty", store=True)
    motif_ecart_reel = fields.Char("Motif Écart 2")
    num_cmd = fields.Char("N° BC")

    @api.one
    @api.depends('qty_estimated', 'qty_dispatched', 'qty_reel_dispatched')
    def _compute_qty(self):
        self.ensure_one()
        for line in self:
            self.qty_ecart = line.qty_estimated - line.qty_dispatched
            self.qty_reel_ecart = line.qty_dispatched - line.qty_reel_dispatched
