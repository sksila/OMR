# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import datetime
from odoo.exceptions import ValidationError
import logging

#----------------------------------------------------------
# Imprimer bon de sortie "wizard"
#----------------------------------------------------------


class BonSortieWizard(models.TransientModel):
    _name = 'oscar.sav.bon.sortie.wizard'
    _description = "Bon de Sortie"
    
    @api.model
    def default_get(self, fields):
        record_ids = self._context.get('active_ids')
        result = super(BonSortieWizard, self).default_get(fields)
        if record_ids:
            obj = []
            claims = self.env['oscar.sav.claim'].browse(record_ids)
            for claim in claims:
                if claim.state == 'done2':
                    obj.append((0,0,{'product_id':claim.product_id.id,
                                         'barcode':claim.product_id.barcode,
                                         'categ_id':claim.product_id.categ_id.id,
                                         'supplier_id':claim.supplier_id.id,
                                         'claim_id':claim.id}))
            result['bon_line_ids'] = obj
        return result
    
    name = fields.Char(string='Numéro Bon de Sortie', readonly=True, copy=False)
    date_sortie = fields.Date(string='Date', required="True",default=fields.Date.context_today, readonly=True, states={'new': [('readonly', False)]})
    chauffeur_id = fields.Many2one('res.partner', string='Chauffeur', domain=[('driver', '=', True)], required="True", readonly=True, states={'new': [('readonly', False)]})
    fleet_id = fields.Many2one('fleet.vehicle', string='Véhicule', required="True", readonly=True, states={'new': [('readonly', False)]})
    supplier_id = fields.Many2one('res.partner', string='Fournisseur', domain=[('supplier', '=', True)], required="True", readonly=True, states={'new': [('readonly', False)]})
    bon_line_ids = fields.One2many('oscar.sav.bon.line.wizard', 'bon_id', string='Détails', readonly=True, states={'new': [('readonly', False)]})
    state = fields.Selection([
        ('new', 'Nouveau'),
        ('print', 'Imprimé'),
        ], string='Statut', readonly=True, copy=False, index=True, default='new')
    
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('oscar.sav.bon.sortie.wizard')
        BonSortie = super(BonSortieWizard, self).create(vals)
        return BonSortie
    
    @api.multi
    def print_BonSortie_button(self):
        self.write({'state': 'print'})
        for claim in self.bon_line_ids:
            claim.claim_id.write({'state': 'repair'})
        return self.env.ref('spc_sav_aziza.oscar_sav_bon_sortie').report_action(self)

class BonSortieLineWizard(models.TransientModel):
    _name = 'oscar.sav.bon.line.wizard'
    _description = "Detail Bon de Sortie"
    _rec_name = "product_id"
    
    product_id = fields.Many2one('product.template', string='Article', required=True)
    barcode = fields.Char(string='Code Barre')
    categ_id = fields.Many2one('product.category', string='Catégorie')
    #modele_id = fields.Many2one('sav.product.modele', string='Modèle')
    #mark_id = fields.Many2one('sav.product.mark', string='Marque')
    supplier_id = fields.Many2one('res.partner', string='Fournisseur')
    claim_id = fields.Many2one('oscar.sav.claim', string='Réclamation')
    bon_id = fields.Many2one('oscar.sav.bon.sortie.wizard', string='Bon de Sortie')
