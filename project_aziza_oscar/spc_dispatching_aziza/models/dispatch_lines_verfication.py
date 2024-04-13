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

class DispatchLinesVerfication(models.Model):
    _name = "oscar.dispatch.lines.verification"
    _description = "Lignes de dispatch"
    _inherit = ['mail.thread']
    _mail_post_access = 'read'
    _order = "id desc"

    name = fields.Char('Nom')
    origin = fields.Char('Réf demande', related='dispatch_id.name')
    origin_line = fields.Char('Id origine')
    dispatch_id = fields.Many2one('oscar.dispatch', 'Dispatch')
    product_id = fields.Many2one('product.template', string='Code Article')
    designation_article = fields.Char('Designation Article')
    vl_id = fields.Many2one('dispatch.vl', 'VL')
    spcb = fields.Boolean('SPCB')
    pcb = fields.Boolean('PCB')
    unity = fields.Selection([
        ('spcb', 'SPCB'),
        ('pcb', 'PCB'),
        ('uvc', 'UVC'),
        ('palette', 'Palette'),
    ], string="Unité")
    dispatch_lines_details_ids = fields.One2many('oscar.dispatch.lines.details.verification', 'dispatch_line_id',
                                                 'Détails de dispatch')
    total_qty_dispatched = fields.Integer("Total Qté  dispatchée", compute='_compute_qty', store=True)
    total_qty_qty_estimated = fields.Integer("Total Qté à dispatcher")
    total_qty_reel_dispatched = fields.Integer("Quantité réellement livrée ", compute='_compute_qty', store=True)
    total_qty_ecart = fields.Integer("Total Ecart")
    requested_by = fields.Many2one('res.users',
                                   string='Approvisionneur',
                                   default=lambda self: self.env.uid,
                                   index=True, track_visibility='always', readonly=True,
                                   related='dispatch_id.requested_by')
    date_dispatch = fields.Datetime(string="Date", default=fields.Datetime.now, related='dispatch_id.date_dispatch')
    category_id = fields.Many2one('product.category', 'Categorie', related='dispatch_id.category_id')
    sub_category_id = fields.Many2one('product.category', 'Famille', related='dispatch_id.sub_category_id')
    state = fields.Selection(selection=_STATES,
                             string='Status',
                             index=True,
                             track_visibility='onchange',
                             default='draft',
                             copy=False,
                             related='dispatch_id.state')

    @api.one
    @api.depends('dispatch_lines_details_ids.qty_reel_dispatched')
    def _compute_qty(self):
        self.ensure_one()
        for line in self:
            self.total_qty_reel_dispatched = sum(line.dispatch_lines_details_ids.mapped('qty_reel_dispatched'))
            self.total_qty_dispatched = sum(line.dispatch_lines_details_ids.mapped('qty_dispatched'))
