# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

STATE_JOURNEE_SELECTION = [
    ('new', 'En préparation'),
    ('prepared', 'Clôturée'),
    ('road','En route'),
    ('done1','Reçue au l\'entrepôt'),
    ('done','Reçue au siège'),
    ('waiting','En attente'),
    ('accepted','Acceptée'),
    ('waiting2','En attente la deuxième vérification'),
    ('accepted1','Acceptée TR'),
    ('waiting1','En attente avec litige'),
    ('checked','Vérifiée'),
]

class Ecart(models.Model):
    _name = 'oscar.ecart'
    _description = 'écarts de journée'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"
    
    name = fields.Char("Nom", compute='_default_name' , readonly=True)
    date_ecart = fields.Date('Date écart', required="True", default=datetime.today().date())
    journee_id = fields.Many2one('oscar.journee', 'Journée', readonly=True, index=True, track_visibility='onchange', ondelete='cascade')
    journee_recue_id = fields.Many2one('oscar.journee.recue', 'Journée', readonly=True, index=True)
    magasin_id = fields.Many2one('oscar.site', string='Magasin', readonly=True, track_visibility='onchange', domain=[('site_type', '=', 'MAGASIN')])
    ecart_line_ids = fields.One2many('oscar.ecart.line', 'ecart_id', string='Détail des écarts')
    litige_line_ids = fields.One2many('oscar.litige.line', 'ecart_id', string='Détail des litiges')
    litige_count = fields.Integer("Nombre de litiges", compute="_compute_litige_count")
    ecart_justify_line_ids = fields.One2many('oscar.ecart.justify.line', 'ecart_id', string='Écarts à justifier', readonly=True, states={'confirmed': [('readonly', False)]})
    state = fields.Selection([
        ('invalidate', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('justify', 'Justifié'),
        ('validated', 'Validé'),
        ('justify1', 'Vérifié par Responsable financier'),
        ('justify2', 'Vérifié par RE'),
        ('corrected', 'Corrigé'),
        ('done', 'Clôturé'),
        ], string='Statut', readonly=True, copy=False, index=True, default='invalidate', track_visibility='onchange')
    caissier_id = fields.Many2one('hr.employee', string='Caissier', readonly=True, domain=[('est_caissier', '=', True)], track_visibility='onchange')
    user_id = fields.Many2one('res.users', string='Utilisateur',default=lambda self: self.env.user)
    is_corrected = fields.Boolean("Est corrigé", index=True)
    type = fields.Selection([
        ('ecart', 'Ecart'),
        ('litige', 'Litige'),
        ], string='Type', default='ecart', index=True, track_visibility='onchange')
    
    state_journee = fields.Selection(STATE_JOURNEE_SELECTION, string='Statut de journée', readonly=True, index=True, related='journee_id.state')
    
    @api.one
    @api.depends('type','journee_id.date_journee','caissier_id.name')
    def _default_name(self):
        date_journee = self.journee_id.date_journee or self.journee_recue_id.date_journee
        display_name = ""
        if self.caissier_id:
            display_name = self.caissier_id.name or ""
        else:
            display_name = self.magasin_id.name
        self.name = "%s-%s- %s" %(dict(self._fields['type'].selection).get(self.type), date_journee, display_name)

    @api.one
    @api.depends('litige_line_ids')
    def _compute_litige_count(self):
        self.litige_count = len(self.litige_line_ids.ids)
    
    @api.multi
    def confirm_ecart(self):
        self.ensure_one()
        self.filtered(lambda s: s.state == 'invalidate').write({'state': 'confirmed'})
        return {
            'name': 'Ecarts',
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'oscar.ecart',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            }
    
    @api.multi
    def confirm_litige(self):
        self.ensure_one()
        if self.env.user.has_group("spc_recette_aziza.group_agent_validation_oscar") and self.journee_recue_id.state == 'accepted' :
            if self.journee_recue_id.mode_tr_ids.ids or self.journee_recue_id.mode_cc_ids.ids:
                self.filtered(lambda s: s.state == 'invalidate').write({'state': 'justify'})
                self.journee_id.write({'state': 'waiting2'})
                self.journee_recue_id.write({'state': 'waiting2'})
            else:
                self.filtered(lambda s: s.state == 'invalidate').write({'state': 'justify'})
                self.journee_id.write({'state': 'waiting1'})
                self.journee_recue_id.write({'state': 'waiting1'})
        elif self.env.user.has_group("spc_recette_aziza.group_agent_validation_ticket_resto_oscar") and self.journee_recue_id.state == 'accepted1':
            self.write({'state': 'justify'})
            self.journee_id.write({'state': 'waiting1'})
            self.journee_recue_id.write({'state': 'waiting1'})
            return {}
    
    @api.multi
    def justify_ecart(self):
        #justify ecart
        if self.ecart_justify_line_ids.ids:
            montant_inv = 0
            justify = True
            list_ej = []
            list_e = []
            for e in self.ecart_line_ids:
                montant_ecart = e.ecart
                montant_justify = 0
                list_e.append(e.name.id)
                for ej in self.ecart_justify_line_ids:
                    list_ej.append(ej.name.id)
                    if e.name == ej.name:
                        montant_justify = montant_justify + ej.ecart
                    if ej.motif == 'inversement' and ej.name.id != self.env.ref('spc_recette_aziza.data_oscar_mode_action_flyers').id:
                        montant_inv = montant_inv + ej.ecart
                # Montant d'ecart = somme des ecarts dec quel que soit motif
                bool_ecart = ("%.3f" % montant_ecart) != ("%.3f" % montant_justify)
                if bool_ecart:
                    justify = False
 
            # verifier que le mode de paiement entre est existe dans la liste des ecarts
            mode_paiement = all(elem in list_e  for elem in list_ej)
 
            # somme total des motifs inversements = 0
            if montant_inv == 0 and justify and mode_paiement:
                self.filtered(lambda s: s.state == 'confirmed').write({'state': 'justify'})
                self.env['oscar.journee.line'].search([('journee_id', '=', self.journee_id.id),('caissier_id', '=', self.caissier_id.id)], limit=1).write({'state':'prepared', 'user_id':self.env.user.id})
                for ecart in self.ecart_line_ids:
                    if ecart.name.id == self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_ticket_restaurant').id:
                        ecart.write({'ecart' : ecart.ecart_js})
                # return {'type': 'ir.actions.do_nothing'}
            else:             
                raise ValidationError("Veuillez vérifier la justification des écarts !")
        else:
            raise ValidationError("Veuillez vérifier la liste des écarts !")
    

    
    @api.multi
    def ecart_print(self):
        """ imprimer ecart du journee """
        return self.env.ref('spc_recette_aziza.oscar_ecarts').report_action(self)
    
    @api.multi
    def valider_ecart(self):
        self.ensure_one()
        self.filtered(lambda s: s.state in ['justify','justify1']).write({'state': 'validated'})
        
    @api.multi
    def cloturer_litiges(self):
        has_group_resp_financier = self.env.user.has_group('spc_recette_aziza.group_responsable_financier_oscar')
        if self.litige_line_ids and has_group_resp_financier:
            correct = True
            obj = []
            for litige in self.litige_line_ids:
                if litige.state not in ['corrected','done']:
                    raise ValidationError("Veuillez clôturer les détails du litige !")
                if litige.state == 'corrected':
                    litige.write({'state':'done'})
                elif litige.state == 'done' and litige.est_ecart:
                    correct = False
                    vals = {
                        'name': litige.name.id,
                        'ecart': litige.litige,
                        'ecart_js': litige.litige,
                        'ecart_id': litige.ecart_id.id,
                        }
                    self.env['oscar.ecart.line'].create(vals)
                elif litige.state == 'done' and not litige.est_ecart:
                    obj.append(litige.id)
                    journee_recue = self.journee_recue_id
                    journee = self.journee_id
                    if litige.name.id == self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_espece').id:
                        journee_recue.write({'montant_espece_vr': journee.montant_espece})
                    elif litige.name.id == self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_ticket_restaurant').id:
                        journee_recue.write({'total_ticket_restaurant': journee.total_ticket_restaurant})
                    elif litige.name.id == self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_cadeaux').id:
                        journee_recue.write({'total_cheque_cadeaux': journee.total_cheque_cadeaux})
                    elif litige.name.id == self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_ban').id:
                        journee_recue.write({'total_carte_ban': journee.total_carte_ban})
                    elif litige.name.id == self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_sodexo').id:
                        journee_recue.write({'total_sodexo': journee.total_sodexo})
                    elif litige.name.id == self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_cheque').id:
                        journee_recue.write({'total_cheque': journee.total_cheque})
                    elif litige.name.id == self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_bon_achat').id:
                        journee_recue.write({'total_bon_aziza': journee.total_bon_aziza})
                    elif litige.name.id == self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_vente_credit').id:
                        journee_recue.write({'total_vente_credit': journee.total_vente_credit})
                    elif litige.name.is_other == True:
                        journee_recue.write({'total_autre_paiement': journee_recue.total_autre_paiement - litige.litige})
            if not correct:
                self.write({'type': 'ecart','state': 'done'})
            elif not correct and obj:
                vals = {
                    'name': self.name,
                    'type': 'litige',
                    'date_ecart': self.date_ecart,
                    'journee_id': self.journee_id.id,
                    'journee_recue_id':self.journee_recue_id.id,
                    'magasin_id':self.magasin_id.id,
                    'litige_line_ids': [(6, 0, obj)],
                    'is_corrected': True,
                    'state':'done',
                    }
                self.create(vals)
            elif correct:
                self.write({'is corrected': True,'state': 'done'})
        return True

    @api.multi
    def valider_litiges(self):
        has_group_resp_financier = self.env.user.has_group('spc_recette_aziza.group_responsable_financier_oscar')
        has_group_boe = self.env.user.has_group('spc_oscar_aziza.group_bo_oscar')
        if self.state == 'justify' and has_group_resp_financier:
            for litige in self.litige_line_ids:
                if litige.state == 'invalidate':
                    raise ValidationError("Veuillez vérifier les justifications de litige !")
            self.write({'state': 'justify1'})
        elif self.state == 'justify1' and has_group_boe:
            for litige in self.litige_line_ids:
                if litige.state == 'dismissed':
                    raise ValidationError("Veuillez vérifier les justifications de litige !")
            self.write({'state': 'justify2'})
        else:
            raise ValidationError(_("Veuillez attendre la validation du responsable d'exploitation!"))


    @api.multi
    def check_ecart(self):
        if self.env.user.has_group('spc_recette_aziza.group_responsable_financier_oscar') and self.journee_recue_id.state == 'waiting1':
            self.filtered(lambda s: s.state == 'justify').write({'state': 'validated'})
        else:
            raise ValidationError('Veuillez vérifier le statut de la journée !')
    
    @api.multi
    def check_mg_ecart(self):
        if self.env.user.has_group('spc_recette_aziza.group_responsable_financier_oscar') and self.journee_recue_id.state == 'waiting1':
            for ecart in self.ecart_line_ids:
                val = {
                        'name' : ecart.name.id,
                        'litige': ecart.ecart,
                        'user_id': self.env.uid,
                        'journee_recue_id': self.journee_recue_id.id,
                        'motif': None,
                        'state': 'dismissed',
                        'ecart_id': self.id,
                    }
                self.env['oscar.litige.line'].create(val)
            self.filtered(lambda s: s.state == 'justify').write({'type': 'litige', 'state': 'justify1'})
        else:
            raise ValidationError('Veuillez vérifier le statut de la journée !')
    
    
    @api.model
    def create(self, vals):
        result = super(Ecart, self).create(vals)
        return result
    
    @api.multi
    def unlink(self):
        for ecart in self:
            if ecart.cmis_folder:
                cmis = self.env['cmis.backend'].search([], limit=1)
                repo = cmis.get_cmis_repository()
                try:
                    someFolder = repo.getObject(ecart.cmis_folder)
                    if someFolder.deleteTree():
                        _logger.info("Folder %s is Deleted", someFolder.name)
                except Exception:
                    _logger.warning("Erreur! Impossible de supprimer les fiches de caisse")
                    pass
        return models.Model.unlink(self)
    
class EcartLine(models.Model):
    _name = 'oscar.ecart.line'
    _description = 'Detail de écarts de journée'
    _order = "ecart desc"

    name = fields.Many2one('moyen.paiement',string='Mode de paiement')
    ecart = fields.Float(string='Écart', digits=(12,3), store=True, readonly=True)
    ecart_js = fields.Float(string='Écart', digits=(12,3), store=True, readonly=True)
    ecart_id = fields.Many2one('oscar.ecart', readonly=True, index=True, ondelete='cascade')
    ecart_unit = fields.Selection([
        ('amount', 'Montant'),
        ('quantity', 'Quantité'),
        ], string='Type', default='amount')
    state = fields.Selection([
        ('invalidate', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('justify', 'Justifié'),
        ('validated', 'Validé'),
        ('justify1', 'Vérifié par Responsable financier'),
        ('justify2', 'Vérifié par RE'),
        ('done', 'Clôturé'),
        ], string='Statut', readonly=True, copy=False, related='ecart_id.state', index=True, default='invalidate')

class LitigeLine(models.Model):
    _name = 'oscar.litige.line'
    _description = 'Detail de litiges de journée'
    _order = "litige desc"

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id
     
    name = fields.Many2one('moyen.paiement',string='Mode de paiement')
    currency_id = fields.Many2one('res.currency', string='Currency', default=_default_currency)
    litige = fields.Monetary(string='Litige', digits=(12,3), store=True, readonly=True, currency_field='currency_id')
    corrected_amount = fields.Monetary(string='Montant corrigé', digits=(12, 3), currency_field='currency_id')
    ecart_id = fields.Many2one('oscar.ecart', readonly=True, index=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', string='Utilisateur', default=lambda self: self.env.user)
    journee_recue_id = fields.Many2one('oscar.journee.recue', string='Journée', index=True)
    motif = fields.Selection([
        ('vr1', 'Vérification 1'),
        ('vr2', 'Vérification 2'),
        ('ibs', 'IBS'),
        ], string='Type litige', default='vr1')
    motif_id = fields.Many2one('oscar.litige.motif',string="Motif", index=True)
    comment = fields.Text("Commentaire")
    est_ecart = fields.Boolean("Est écart", index=True)
    state = fields.Selection([
        ('invalidate', 'Brouillon'),
        ('dismissed', 'Ecarté'),
        ('corrected', 'Corrigé'),
        ('accepted', 'Accepté'),
        ('refused', 'Refusé'),
        ('done', 'Clôturé'),
        ], string='Statut', readonly=True, copy=False, index=True, default='invalidate')
    state_ecart = fields.Selection(related='ecart_id.state')
     
    @api.multi
    def corriger_litige(self):
        self.filtered(lambda s: s.state == 'invalidate').write({'state': 'corrected'})
     
    @api.multi
    def ecarter_litige(self):
        self.filtered(lambda s: s.state == 'invalidate').write({'state': 'dismissed'})

    @api.multi
    def accept_litige(self):
        self.filtered(lambda s: s.state in ['dismissed','corrected']).write({'state': 'accepted'})

    @api.multi
    def not_accept_litige(self):
        self.filtered(lambda s: s.state == 'refused').write(
            {'corrected_amount': 0, 'est_ecart': True, 'state': 'done'})

    @api.multi
    def clo_litige(self):
        self.filtered(lambda s: s.state in ['accepted','refused']).write({'state': 'done'})
        if self.corrected_amount:
            diff_amount = self.litige - self.corrected_amount
            self.write({'litige': diff_amount})
 
class EcartJustifyLine(models.Model):
    _name = 'oscar.ecart.justify.line'
    _description = 'Écarts à justifier'
 
    name = fields.Many2one('moyen.paiement',string='Mode de paiement', required=True)
    motif = fields.Selection([
        ('inversement', 'inversement de mode de paiement'),
        ('ecart_caisse', 'écart de caisse'),
        ], string='Motif', default='inversement', required=True)
    ecart = fields.Float('Écart', digits=(12,3))
    comment = fields.Text('Commentaire')
    caissier_id = fields.Many2one('hr.employee', string='Caissier', domain=[('est_caissier', '=', True)], related="ecart_id.caissier_id", readonly=True, store=True)
    ecart_id = fields.Many2one('oscar.ecart', readonly=True, index=True, ondelete='cascade')
    

class LitigeMotif(models.Model):
    _name = 'oscar.litige.motif'
    _description = "Motif de litige"
    _order = 'other asc'

    name = fields.Char(string='Libellé')
    other = fields.Boolean("Autre")

