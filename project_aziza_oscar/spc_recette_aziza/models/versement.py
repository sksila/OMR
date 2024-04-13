# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError

class Versement(models.Model):
    
    _name = 'oscar.versement'
    _description = 'Versement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    @api.model
    def _default_magasin(self):
        if self.env.user.has_group("spc_oscar_aziza.group_reponsable_magasin"):
            return self.env['oscar.site'].search([('user_ids', 'child_of', [self.env.uid]),('site_type', '=', 'MAGASIN')], limit=1)
        return
    
    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id
    
    name = fields.Char('Numéro Versement', readonly=True, copy=False, track_visibility='onchange')
    date_versement = fields.Date('Date de versement', required=True, default=fields.Date.context_today, track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    bank_id = fields.Many2one('res.bank', string='Banque',related="journee_id.magasin_id.bank_id", store=True, readonly=True, track_visibility='onchange')
    journee_id = fields.Many2one('oscar.journee', string='Journée', copy=False, index=True, ondelete='cascade', required=True, domain="[('reste_a_verser','!=', 0)]", track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=_default_currency)
    montant_versement = fields.Monetary('Montant', digits=(12,3), readonly=True, currency_field='currency_id')
    reste_a_verser = fields.Monetary('Montant à verser', store=True, readonly=True, currency_field='currency_id', compute='_compute_versement')
    user_id = fields.Many2one('res.users', string='Utilisateur', readonly=True, states={'draft': [('readonly', False)]},
                              domain=lambda self: [('groups_id', 'in', [self.env.ref('spc_oscar_aziza.group_reponsable_magasin').id])],
                              default=lambda self: self.env.user)
    comment = fields.Text('Commentaire', readonly=True, states={'draft': [('readonly', False)]})
    magasin_id = fields.Many2one('oscar.site', string='Magasin', related="journee_id.magasin_id", store=True, readonly=True, states={'draft': [('readonly', False)]}, track_visibility='onchange')
    state = fields.Selection([
            ('draft','Brouillon'),
            ('validate', 'Validé'),
            ('paid', 'Versée'),
            ('paid_ibs', 'Ramassée par IBS'),
        ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False)

    keepsafe_monnaie = fields.Char('Keepsafe IBS pièces de monnaie', index=True, size=10, copy=False, readonly=True, states={'draft': [('readonly', False)]}, track_visibility='onchange')
    pieces_monnaie = fields.Monetary('Pièces de monnaie', digits=(12, 3), currency_field='currency_id', readonly=True, states={'draft': [('readonly', False)]})
    keepsafe_billet = fields.Char('Keepsafe IBS billet', index=True, size=10, copy=False, readonly=True,
                                   states={'draft': [('readonly', False)]}, track_visibility='onchange')
    billet = fields.Monetary('Montant Billet', digits=(12, 3), currency_field='currency_id', readonly=True, states={'draft': [('readonly', False)]})
    type_versement = fields.Selection([
        ('direct', 'Direct'),
        ('ibs', 'IBS'),
    ], string='Type de versement', related="journee_id.magasin_id.type_versement")

    @api.onchange('journee_id')
    def _onchange_journee_id(self):
        if self.journee_id:
            return {'domain': {'user_id': [('id', 'in', [rec.id for rec in self.journee_id.magasin_id.user_ids])]}}

    @api.constrains('pieces_monnaie','billet','reste_a_verser','state')
    def _check_num_keepsafe(self):
        for vr in self:
            total = vr.pieces_monnaie + vr.billet
            # domain = [
            #     '&',
            #     '|',
            #     ('keepsafe_monnaie', '=', vr.keepsafe_monnaie),
            #     ('keepsafe_billet', '=', vr.keepsafe_billet),
            #     ('id', '!=', vr.id),
            # ]
            # count_versement = self.search_count(domain)
            # if count_versement:
            #     raise ValidationError(_('le numéro Keepsafe doit être unique!'))

            print("total : ",round(total,3))
            print("vr.reste_a_verser : ", round(vr.reste_a_verser,3))

            diff_total = round(total,3) - round(vr.reste_a_verser,3)
            print("diff_total = total - vr.reste_a_verser :",diff_total)
            if diff_total != 0.0 and self.state == 'draft':
                raise ValidationError(_('La somme des montants "Billet" et "Pièces de monnaie" doit être égale au montant du versement!'))

    @api.one
    @api.depends('journee_id','montant_versement')
    def _compute_versement(self):
        if self.journee_id:
            self.reste_a_verser = self.journee_id.reste_a_verser
    
    @api.multi
    def versement_print(self):
        """ imprimer versement du journee """
        return self.env.ref('spc_recette_aziza.oscar_versements').report_action(self)
    
    @api.multi
    def action_validate(self):
        """ Valider le versement du journee
        """
        print("self.reste_a_verser :",self.reste_a_verser)
        if self.bank_id:
            self.filtered(lambda s: s.state == 'draft').write({'state': 'validate', 'montant_versement': self.reste_a_verser})
        else:
            raise ValidationError("Veuillez contacter l'admin pour vérifier Le champ banque de magasin !")
    
    @api.multi
    def action_draft(self):
        """ Remettre en brouillon
        """
        self.filtered(lambda s: s.state == 'paid' or s.state == 'paid_ibs').write({'state': 'draft'})
    
    @api.multi
    def action_verser(self):
        """ Verser le montant espece du journee
        """
        
        if self.magasin_id.type_versement == 'direct':
            self.filtered(lambda s: s.state == 'validate').write({'state': 'paid'})
            for versement in self:
                versement.journee_id.write({'is_paid' : True})
        elif self.magasin_id.type_versement == 'ibs':
            self.filtered(lambda s: s.state == 'validate').write({'state': 'paid_ibs'})
            for versement in self:
                versement.journee_id.write({'is_paid' : True})

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('oscar.versement')
        versement = super(Versement, self).create(vals)
        return versement

class VersementCheque(models.Model):
    
    _name = 'oscar.versement.cheque'
    _description = 'Versement Cheque'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char('Numéro Versement', readonly=True, copy=False, track_visibility='onchange')
    date_versement = fields.Date('Date de versement', required=True, default=datetime.today().date(), track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    bank_id = fields.Many2one('res.bank', string='Banque', required=True, track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    montant_versement = fields.Float('Montant Total', digits=(12,3), store=True, readonly=True, compute='_compute_versement', track_visibility='onchange')
    user_id = fields.Many2one('res.users', string='Utilisateur', required=True, readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env.user, domain=lambda self: [('groups_id', 'in', [self.env.ref('spc_recette_aziza.group_responsable_financier_oscar').id])])
    mode_cheque_ids = fields.One2many('oscar.mode.paiement.recue', 'versement_cheque_id', string='Chèque',
                                      readonly=True, states={'draft': [('readonly', False)]})
    cheque_count = fields.Integer(string='Nombre des chèques', compute="_compute_versement", readonly=True, store=True)
    comment = fields.Text('Commentaire', readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([
            ('draft','Brouillon'),
            ('validate', 'Validé'),
            ('paid', 'Versé'),
        ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False)

    @api.onchange('user_id','bank_id')
    def _onchange_mode_cheque_ids(self):
        return {'domain': {'mode_cheque_ids': [('moyen_paiement_id.id', '=', self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_cheque').id),('state', '=', 'checked')]}}
    
    @api.one
    @api.depends('mode_cheque_ids','mode_cheque_ids.montant_vr')
    def _compute_versement(self):
        self.cheque_count = len(self.mode_cheque_ids.ids)
        self.montant_versement = sum(line.montant_vr for line in self.mode_cheque_ids)
    

    @api.multi
    def versement_print(self):
        """ imprimer ecart du journee """
        return self.env.ref('spc_recette_aziza.oscar_versements_cheques').report_action(self)
    
    @api.multi
    def action_validate(self):
        """ Valider le versement cheques
        """
        self.filtered(lambda s: s.state == 'draft').write({'state': 'validate'})
    
    @api.multi
    def action_draft(self):
        """ Remettre en brouillon
        """
        for mode in self.mode_cheque_ids:
            mode.write({'state': 'checked'})
        self.filtered(lambda s: s.state == 'paid').write({'state': 'draft'})
        
    @api.multi
    def action_verser(self):
        """ Verser les cheques
        """
        self.filtered(lambda s: s.state == 'validate').write({'state': 'paid'})
        for mode in self.mode_cheque_ids:
            mode.write({'state': 'paid'})
    
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('oscar.versement.cheque')
        return super(VersementCheque, self).create(vals)
