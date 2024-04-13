# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

STATE_JOURNEE_SELECTION = [
    ('prepared', 'Clôturée'),
    ('road','En route'),
    ('done','Reçue au siège'),
    ('waiting','En attente'),
    ('accepted','Acceptée'),
    ('waiting2','En attente la deuxième vérification'),
    ('accepted1','Acceptée TR'),
    ('waiting1','En attente avec litige'),
    ('checked','Vérifiée'),
]

class JourneeRecue(models.Model):
    _name = 'oscar.journee.recue'
    _description = 'Journée Siège'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "date_journee desc"
     
    name = fields.Char('Description', readonly=True)
    date_journee = fields.Date(string='Date journée', required="True", readonly=True)
    journee_id = fields.Many2one('oscar.journee', string='Journée', index=True, ondelete='cascade', readonly=True)
#     bordereau_id = fields.Many2one('oscar.bordereau', string='Bordereau', index=True, readonly=True)
    user_id = fields.Many2one('res.users', string='Utilisateur', index=True, readonly=True)
    magasin_id = fields.Many2one('oscar.site', string='Magasin', domain=[('site_type', '=', 'MAGASIN')], readonly=True)
    controller_id = fields.Many2one('res.users', string='Vérificateur', index=True, domain=lambda self: [('groups_id', 'in', [self.env.ref('spc_recette_aziza.group_agent_validation_oscar').id])], track_visibility='onchange', readonly=True)
    controller_tr_id = fields.Many2one('res.users', string='Vérificateur TR & CC', index=True, domain=lambda self: [('groups_id', 'in', [self.env.ref('spc_recette_aziza.group_agent_validation_ticket_resto_oscar').id])], track_visibility='onchange', readonly=True)
    bank_tpe_id = fields.Many2one('res.partner.bank', string='TPE', help='Terminal de Paiement Électronique', readonly=True)
    state = fields.Selection(STATE_JOURNEE_SELECTION, string='Statut', readonly=True, copy=False, index=True, default='done', track_visibility='onchange')
    ecart_ids = fields.One2many('oscar.ecart', 'journee_recue_id',string='Écarts')
    ecart_count = fields.Integer(string='Nombre des écarts', compute="_compute_ecart_count", readonly=True, store=True)
    ecart_vl_count = fields.Integer(string='Nombre des écarts validés', compute="_compute_ecart_count", readonly=True, store=True)
    litige_count = fields.Integer(string='Nombre des litiges', compute="_compute_ecart_count", readonly=True, store=True)
     
    montant_espece = fields.Float(string='Montant versé', digits=(12,3), readonly=True)
     
    montant_espece_vr = fields.Float(string='Montant versé à vérifier', digits=(12,3), readonly=True, states={'accepted': [('readonly', False)]})
     
    total_ticket_restaurant = fields.Float('Montant total des tickets restaurant', digits=(12,3), store=True, readonly=True, compute='_compute_all', track_visibility='onchange')
    total_cheque_cadeaux = fields.Float('Montant total des cheques cadeaux', digits=(12,3), store=True, readonly=True, compute='_compute_all', track_visibility='onchange')
     
    total_cheque = fields.Float('Montant total des cheques', digits=(12,3), store=True, readonly=True, compute='_compute_all', track_visibility='onchange')
    total_carte_ban = fields.Float('Montant total des cartes bancaire', digits=(12,3), store=True, readonly=True, compute='_compute_all', track_visibility='onchange')
    total_sodexo = fields.Float('Montant total des cartes Sodexo', digits=(12,3), store=True, readonly=True, compute='_compute_all', track_visibility='onchange')
    total_autre_paiement = fields.Float('Montant total des autres paiements', digits=(12,3), store=True, readonly=True, compute='_compute_all', track_visibility='onchange')
     
    total_bon_aziza = fields.Float(string="Montant total des Bons d'achat Aziza", digits=(12,3), store=True, readonly=True, compute='_compute_all', track_visibility='onchange')
    total_vente_credit = fields.Float(string='Montant total de vente à crédit', digits=(12,3), store=True, readonly=True, compute='_compute_all', track_visibility='onchange')
     
    montant_global = fields.Float('Montant Total de la journée', digits=(12,3), store=True, readonly=True, compute='_compute_all', track_visibility='onchange')
     
    mode_tr_ids = fields.One2many('oscar.mode.paiement.recue', 'journee_recue_id', string='TR', domain=lambda self: [('moyen_paiement_id.id', '=', self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_ticket_restaurant').id)], readonly=True, states={'accepted1': [('readonly', False)]})
    mode_cc_ids = fields.One2many('oscar.mode.paiement.recue', 'journee_recue_id', string='CC', domain=lambda self: [('moyen_paiement_id.id', '=', self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_cadeaux').id)], readonly=True, states={'accepted1': [('readonly', False)]})
    mode_cb_ids = fields.One2many('oscar.mode.paiement.recue', 'journee_recue_id', string='CB', 
                                  domain=lambda self: [('moyen_paiement_id.id', '=', self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_ban').id),('state', '!=', 'new')], 
                                  readonly=True, states={'accepted': [('readonly', False)]})
    mode_cs_ids = fields.One2many('oscar.mode.paiement.recue', 'journee_recue_id', string='CS', 
                                  domain=lambda self: [('moyen_paiement_id.id', '=', self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_sodexo').id),('state', '!=', 'new')], 
                                  readonly=True, states={'accepted': [('readonly', False)]})
    mode_cheque_ids = fields.One2many('oscar.mode.paiement.recue', 'journee_recue_id', string='Chèque', 
                                      domain=lambda self: [('moyen_paiement_id.id', '=', self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_cheque').id),('state', '!=', 'new')], 
                                      readonly=True, states={'accepted': [('readonly', False)]})
    mode_ba_ids = fields.One2many('oscar.mode.paiement.recue', 'journee_recue_id', string='Bon AZIZA', domain=lambda self: [('moyen_paiement_id.id', '=', self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_bon_achat').id)], readonly=True, states={'accepted': [('readonly', False)]})
    mode_vc_ids = fields.One2many('oscar.mode.paiement.recue', 'journee_recue_id', string='VC', domain=lambda self: [('moyen_paiement_id.id', '=', self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_vente_credit').id)], readonly=True, states={'accepted': [('readonly', False)]}, help="Vente à crédit")
    mode_other_ids = fields.One2many('oscar.mode.paiement.recue', 'journee_recue_id', string='Autres Paiement', domain=['|',('moyen_paiement_id', '=', False),('moyen_paiement_id.is_other', '=', True)], readonly=True, states={'accepted': [('readonly', False)]})
    envelope_id = fields.Many2one('oscar.envelope', string='Enveloppe', index=True, readonly=True)
    references = fields.Char(string="Références", compute="_compute_references", store=True, index=True)

    flyer_ids = fields.One2many('oscar.mode.paiement.recue', inverse_name='journee_recue_id', string='Action Flyers',
                                domain=lambda self: [('moyen_paiement_id.id', '=',
                                                      self.env.ref('spc_recette_aziza.data_oscar_mode_action_flyers').id)],
                                readonly=True, states={'accepted': [('readonly', False)]})
    flyers_vr_count = fields.Integer(string="Nombre de flyers", store=True, readonly=True, compute='_compute_all',
                                     track_visibility='onchange')
     
    _sql_constraints = [
        ('date_journee_uniq', 'UNIQUE (date_journee,magasin_id)',  'La date de la journée doit être unique!')
        ]
     
    @api.onchange('montant_espece_vr')
    def onchange_positive_value(self):
        if self.montant_espece_vr < 0:
            self.montant_espece_vr = abs(self.montant_espece_vr)


    @api.depends("envelope_id")
    def _compute_references(self):
        for journee in self:
            obj = ""
            if journee.envelope_id:
                for ref in journee.envelope_id.reference_ids:
                    obj = obj + ref.name + " ,"
            journee.references = obj[:-1]

    @api.one
    @api.depends('montant_espece_vr','mode_cheque_ids.montant_vr', 'mode_cheque_ids.state', 
                 'mode_cb_ids.montant_vr', 'mode_cb_ids.state',
                 'mode_cs_ids.montant_vr','mode_cs_ids.state',
                 'mode_other_ids.montant_vr','mode_tr_ids.montant_compute_vr','mode_cc_ids.montant_compute_vr')
    def _compute_all(self):                
        self.total_cheque = sum(line.montant_vr for line in self.mode_cheque_ids if line.state in ['confirmed','checked','paid'])
        self.total_carte_ban = sum(line.montant_vr for line in self.mode_cb_ids if line.state in ['confirmed','checked'])
        self.total_sodexo = sum(line.montant_vr for line in self.mode_cs_ids if line.state in ['confirmed','checked'])
        self.total_autre_paiement = sum(line.montant_vr for line in self.mode_other_ids)
         
        self.total_ticket_restaurant = sum(line.montant_compute_vr for line in self.mode_tr_ids)
        self.total_cheque_cadeaux = sum(line.montant_compute_vr for line in self.mode_cc_ids)
        self.total_bon_aziza = sum(line.montant_vr for line in self.mode_ba_ids)
        self.total_vente_credit = sum(line.montant_vr for line in self.mode_vc_ids)
        self.montant_global = self.montant_espece_vr + self.total_cheque + self.total_carte_ban + self.total_sodexo + self.total_autre_paiement + self.total_ticket_restaurant + self.total_cheque_cadeaux + self.total_vente_credit + self.total_bon_aziza
        self.flyers_vr_count = sum(line.nombre_vr for line in self.flyer_ids if line.state in ['confirmed', 'checked'])

    @api.one
    @api.depends('ecart_ids','ecart_ids.state','ecart_ids.type')
    def _compute_ecart_count(self):
        self.ecart_count = sum(1 for ecart in self.ecart_ids if ecart.type == 'ecart' and ecart.state in ['justify'])
        self.ecart_vl_count = sum(1 for ecart in self.ecart_ids if ecart.type == 'ecart' and ecart.state in ['validated'])
        self.litige_count = sum(1 for ecart in self.ecart_ids if ecart.type == 'litige' and ecart.state in ['justify','justify1','justify2','done'])
         
    @api.multi
    def retour_accepte(self):
        """
            Action retour au statut acceptée
        """
        self.filtered(lambda s: s.state in ['waiting2','accepted1','waiting1','checked']).write({'state': 'accepted'})
        self.journee_id.filtered(lambda s: s.state in ['waiting2','accepted1','waiting1','checked']).write({'state': 'accepted'})
        if self.state == 'accepted':
            for litige in self.ecart_ids:
                if litige.type == 'litige':
                    litige.sudo().unlink()
     
    @api.multi
    def retour_accepte_tr(self):
        """
            Action retour au statut acceptée TR
        """
        self.filtered(lambda s: s.state in ['waiting1','checked']).write({'state': 'accepted1'})
        self.journee_id.filtered(lambda s: s.state in ['waiting1','checked']).write({'state': 'accepted1'})
        if self.state == 'accepted1':
            for litige in self.ecart_ids:
                if litige.type == 'litige':
                    if litige.litige_line_ids.ids:
                        for litige_line in litige.litige_line_ids:
                            if litige_line.motif == 'vr2':
                                litige_line.unlink()
                    else:
                        litige.unlink()
                        
 
    @api.multi
    def accept_journees(self):
        if self.env.user.has_group('spc_recette_aziza.group_agent_validation_oscar'):
            self.filtered(lambda s: s.state == 'waiting').write({'state': 'accepted'})
            if self.state == 'accepted':
                self.journee_id.write({'state': 'accepted'})
        else:
            raise ValidationError("Vous n'avez pas l'autorisation d'accepter les journées !")
     
    @api.multi
    def accept_tr_journees(self):
        if self.env.user.has_group('spc_recette_aziza.group_agent_validation_ticket_resto_oscar'):
            self.filtered(lambda s: s.state == 'waiting2').write({'state': 'accepted1'})
            if self.state == 'accepted1':
                self.journee_id.write({'state': 'accepted1'})
        else:
            raise ValidationError("Vous n'avez pas l'autorisation d'accepter TR des journées !")
     
    @api.multi
    def verifier_journee(self):
        if self.env.user.has_group('spc_recette_aziza.group_agent_validation_oscar'):
            if self.mode_cb_ids:
                for cb in self.mode_cb_ids:
                    if not cb.bank_tpe_id:
                        raise ValidationError("Veuillez saisir le banque dans la liste de CB")
            if sum(line.nombre_vr for line in self.flyer_ids if line.state not in ['checked']):
                raise ValidationError("Veuillez vérifier la liste des flyers!")

            total_journee_recue = self.montant_espece_vr + self.total_cheque + self.total_carte_ban +self.total_sodexo + self.total_autre_paiement + self.total_vente_credit + self.total_bon_aziza
            total_journee_mg = self.journee_id.montant_espece + self.journee_id.total_cheque + self.journee_id.total_carte_ban +self.journee_id.total_sodexo + self.journee_id.total_autre_paiement + self.journee_id.total_vente_credit + self.journee_id.total_bon_aziza
             
            bool_litige = ("%.3f" % total_journee_recue) == ("%.3f" % total_journee_mg)
 
            if bool_litige:
                if self.mode_tr_ids.ids or self.mode_cc_ids.ids:
                    self.filtered(lambda s: s.state == 'accepted').write({'state': 'waiting2'})
                    self.journee_id.filtered(lambda s: s.state == 'accepted').write({'state': 'waiting2'})
                elif self.ecart_count > 0:
                    self.filtered(lambda s: s.state == 'accepted').write({'state': 'waiting1'})
                    self.journee_id.filtered(lambda s: s.state == 'accepted').write({'state': 'waiting1'})
                else:
                    self.filtered(lambda s: s.state == 'accepted').write({'state': 'checked'})
                    self.journee_id.filtered(lambda s: s.state == 'accepted').write({'state': 'checked'})
            else:
                '''
                * Calculer les litges
                 
                '''
                 
                obj = []
                litige_sodexo = self.total_sodexo - self.journee_id.total_sodexo
                litige_bancaire = self.total_carte_ban - self.journee_id.total_carte_ban
                litige_cheque = self.total_cheque - self.journee_id.total_cheque
                litige_espece = self.montant_espece_vr - self.journee_id.montant_espece
                 
                litige_bon_aziza =  self.total_bon_aziza - self.journee_id.total_bon_aziza
                litige_vente_credit =  self.total_vente_credit - self.journee_id.total_vente_credit
 
                print("Calculer les litges")
                '''
                ** supp les litiges si on va faire 2eme verification 
                '''
 
                self.env['oscar.litige.line'].sudo().search([('journee_recue_id.id', '=', self.id),('user_id.id', '=', self.env.user.id),('motif','in',['vr1','ibs'])]).unlink()
 
                print("supp les litiges si on va faire 2eme verification")
                '''
                *** Insérer les litiges dans tab obj
                '''
                 
                if litige_espece != 0:
                    obj.append((0,0,{'name': self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_espece').id,
                                     'litige': litige_espece, 'user_id': self.env.uid, 'journee_recue_id': self.id, 'motif': 'vr1'}))
                if litige_cheque != 0:
                    obj.append((0,0,{'name': self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_cheque').id,
                                     'litige': litige_cheque, 'user_id': self.env.uid, 'journee_recue_id': self.id, 'motif': 'vr1'}))
                if litige_bancaire != 0:
                    obj.append((0,0,{'name': self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_ban').id,
                                     'litige': litige_bancaire, 'user_id': self.env.uid, 'journee_recue_id': self.id, 'motif': 'vr1'}))
                if litige_sodexo != 0:
                    obj.append((0,0,{'name':  self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_sodexo').id,
                                     'litige': litige_sodexo, 'user_id': self.env.uid, 'journee_recue_id': self.id, 'motif': 'vr1'}))
                if litige_bon_aziza != 0:
                    obj.append((0,0,{'name':  self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_bon_achat').id,
                                     'litige': litige_bon_aziza, 'user_id': self.env.uid, 'journee_recue_id': self.id, 'motif': 'vr1'}))
                if litige_vente_credit != 0:
                    obj.append((0,0,{'name':  self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_vente_credit').id,
                                     'litige': litige_vente_credit, 'user_id': self.env.uid, 'journee_recue_id': self.id, 'motif': 'vr1'}))
 
                for m in self.env['moyen.paiement'].search([('is_other','=', True)]):
                    montant = sum(line.montant for line in self.mode_other_ids if line.moyen_paiement_id.id == m.id)
                    montant_vr = sum(line.montant_vr for line in self.mode_other_ids if line.moyen_paiement_id.id == m.id)
                    litige_autre = montant_vr - montant
                    if litige_autre != 0:
                        obj.append((0,0,{'name':m.id,'litige': litige_autre, 'user_id': self.env.uid, 'journee_recue_id': self.id, 'motif': 'vr1'}))
                         
                print("Insérer les litiges dans tab obj")
                '''
                **** Creation les litiges sur BD
                '''
 
                vals = {
                    'journee_recue_id': self.id,
                    'journee_id': self.journee_id.id,
                    'type': 'litige',
                    'magasin_id': self.magasin_id.id,
                    'user_id': self.magasin_id.user_id.id,
                    'litige_line_ids': obj,
                    }
                 
                litige = self.env['oscar.ecart'].create(vals)
                print("Creation les litiges sur BD")
                print("litige = ", litige.litige_line_ids.ids)
                context = {'default_id': litige.id, 
                           'default_magasin_id': self.magasin_id.id,
                           'default_type' : 'litige',
                           'default_journee_recue_id': self.id,
                           'default_journee_id': self.journee_id.id,
                           'default_litige_line_ids' :litige.litige_line_ids.ids, }
                return {
                    'name': 'Litiges',
                    'res_id': litige.id,
                    'view_mode': 'form',
                    'view_type': 'form',
                    'res_model': 'oscar.ecart',
                    'type': 'ir.actions.act_window',
                    'context': context,
                    'target': 'new',
                    }
    @api.multi
    def verifier_tr(self):
        if self.env.user.has_group('spc_recette_aziza.group_agent_validation_ticket_resto_oscar'):
            total_journee_recue = self.total_ticket_restaurant + self.total_cheque_cadeaux
            total_journee_mg = self.journee_id.total_ticket_restaurant + self.journee_id.total_cheque_cadeaux
             
            bool_litige = ("%.3f" % total_journee_recue) == ("%.3f" % total_journee_mg)
             
            if bool_litige:
                if self.ecart_count > 0:
                    my_litiges = self.env['oscar.litige.line'].search([('journee_recue_id', '=', self.id),('user_id', '=', self.env.uid),('motif','=','vr2')])
                    if my_litiges:
                        my_litiges.sudo().unlink()
                    self.filtered(lambda s: s.state == 'accepted1').write({'state': 'waiting1'})
                    self.journee_id.filtered(lambda s: s.state == 'accepted1').write({'state': 'waiting1'})
                else:
                    my_litiges = self.env['oscar.litige.line'].search([('journee_recue_id', '=', self.id),('user_id', '=', self.env.uid),('motif','=','vr2')])
                    if my_litiges:
                        my_litiges.sudo().unlink()
                    if self.litige_count:
                        self.filtered(lambda s: s.state == 'accepted1').write({'state': 'waiting1'})
                        self.journee_id.write({'state': 'waiting1'})
                    else:
                        self.filtered(lambda s: s.state == 'accepted1').write({'state': 'checked'})
                        self.journee_id.write({'state': 'checked'})
            else:
                '''
                * Calculer les litges
                 
                '''
                 
                obj = []
                litige_ticket_restaurant = self.total_ticket_restaurant - self.journee_id.total_ticket_restaurant
                litige_cheque_cadeaux = self.total_cheque_cadeaux - self.journee_id.total_cheque_cadeaux
                print("Calculer les litges")
                '''
                ** supp les litiges si on va faire 2eme verification 
                '''
                 
                my_litiges = self.env['oscar.litige.line'].search([('journee_recue_id', '=', self.id),('user_id', '=', self.env.uid),('motif','=','vr2')])
                if my_litiges:
                    my_litiges.sudo().unlink()
                print("supp les litiges si on va faire 2eme verification")
                '''
                *** Insérer les litiges dans tab obj
                '''
                 
                if litige_ticket_restaurant != 0:
                    obj.append((0,0,{'name': self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_ticket_restaurant').id,
                                     'litige': litige_ticket_restaurant, 'user_id': self.env.uid, 'journee_recue_id': self.id, 'motif': 'vr2'}))
                if litige_cheque_cadeaux != 0:
                    obj.append((0,0,{'name': self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_cadeaux').id,
                                         'litige': litige_cheque_cadeaux, 'user_id': self.env.uid, 'journee_recue_id': self.id, 'motif': 'vr2'}))
                print("Insérer les litiges dans tab obj")
                '''
                **** Creation les litiges sur BD
                '''
                litige = self.env['oscar.ecart'].search([('journee_recue_id', '=', self.id),('type', '=', 'litige')], limit=1)
                 
                if litige.id:
                    if litige.state == 'justify':
                        litige.write({'litige_line_ids' : obj})
                    else:
                        litige.sudo().unlink()
                        vals = {
                            'journee_recue_id': self.id,
                            'journee_id': self.journee_id.id,
                            'type': 'litige',
                            'magasin_id': self.magasin_id.id,
                            'litige_line_ids': obj,
                            }
                     
                        litige = self.env['oscar.ecart'].create(vals)
                else:
                    vals = {
                        'journee_recue_id': self.id,
                        'journee_id': self.journee_id.id,
                        'type': 'litige',
                        'magasin_id': self.magasin_id.id,
                        'litige_line_ids': obj,
                        }
                     
                    litige = self.env['oscar.ecart'].create(vals)
                print("Creation les litiges sur BD")
                 
                context = {'default_id': litige.id,
                           'default_magasin_id': self.magasin_id.id, 
                           'default_type' : 'litige',
                           'default_journee_recue_id': self.id,
                           'default_journee_id': self.journee_id.id,
                            'default_litige_line_ids' :litige.litige_line_ids.ids,}
                 
                return {
                    'name': 'Litiges',
                    'res_id': litige.id,
                    'view_mode': 'form',
                    'view_type': 'form',
                    'res_model': 'oscar.ecart',
                    'type': 'ir.actions.act_window',
                    'context': context,
                    'target': 'new',
                    }
                 
     
    @api.multi
    def valider_journee(self):
        if self.env.user.has_group('spc_recette_aziza.group_responsable_financier_oscar') and self.state == 'waiting1':
            if self.ecart_count > 0:
                raise ValidationError("Veuillez vérifier la justification des fiches d'écarts avant la valider !")
            elif self.litige_count > 0:
                for litige in self.ecart_ids:
                    if litige.type == 'litige' and litige.state != 'done' and litige.litige_line_ids.ids:
                        raise ValidationError("Veuillez clôturer les litiges de la journée avant la valider !")
            else:
                self.filtered(lambda s: s.state == 'waiting1').write({'state': 'checked'})
                self.journee_id.filtered(lambda s: s.state == 'waiting1').write({'state': 'checked'})
             
    @api.model
    def create(self, vals):
        return super(JourneeRecue, self).create(vals)

class ModePaiementRecue(models.Model):
    _name = 'oscar.mode.paiement.recue'
    _description = "Modes de paiement"
    _rec_name = 'moyen_paiement_id'
    
    def _default_moyen_paiement(self):
        if self._context.get('default_code'):
            return self.env['moyen.paiement'].search([('code','=',self._context.get('default_code'))], limit=1)
        else:
            return
    
    
    moyen_paiement_id = fields.Many2one('moyen.paiement', string="Moyen de paiement", default=_default_moyen_paiement)
    code_cheque = fields.Char(string='Code')
    date_journee = fields.Date(string='Date journée')
    caissier_id = fields.Many2one('hr.employee', string='Caissier', domain=[('est_caissier', '=', True)])
    magasin_id = fields.Many2one('oscar.site', string='Magasin', domain=[('site_type', '=', 'MAGASIN')])
    montant = fields.Float('Montant', digits=(12,3))
    montant_gold = fields.Float('Montant Gold', digits=(12,3), readonly=True)
    montant_compute = fields.Float('Montant', digits=(12,3), readonly=True, compute='_compute_montant', store=True)
    cin = fields.Char('CIN')
    name_user = fields.Char('Nom titulaire')
    phone_user = fields.Char(string='Tél titulaire')
    oscar_bank_id = fields.Many2one('res.bank', string='Banque')
    bank_tpe_id = fields.Many2one('res.partner.bank', string='TPE', help='Terminal de Paiement Électronique')
    fournisseur_id = fields.Many2one('res.partner', string='Fournisseur')
    valeur = fields.Float(string='Valeur', digits=(12,3))
    nombre = fields.Integer(string='Nombre')
    nombre_gold = fields.Integer(string='Nombre (Gold)', readonly=True)
    nombre_vr = fields.Integer(string='Nombre verifié')
    montant_vr = fields.Float('Montant verifié', digits=(12,3))
    montant_compute_vr = fields.Float('Montant verifié', digits=(12,3), readonly=True, compute='_compute_montant', store=True)
    user_id = fields.Many2one('res.users', string='Utilisateur', default=lambda self: self.env.user)
    journee_recue_id = fields.Many2one('oscar.journee.recue', index=True, string='Journée', ondelete='cascade')
    versement_cheque_id = fields.Many2one('oscar.versement.cheque', index=True, string='Versement Chèque')
    state = fields.Selection([
        ('new', 'Nouveau'),
        ('confirmed', 'Confirmé'),
        ('checked', 'Vérifié'),
        ('paid', 'Versé'),
        ], string='Statut', default='checked', readonly=True)
    
    state_journee = fields.Selection(STATE_JOURNEE_SELECTION, string='Statut de journée', readonly=True, index=True, related='journee_recue_id.state')

    nombre_ecart = fields.Integer('Ecart', readonly=True, compute='_compute_ecart', store=True)
    note = fields.Text(string='Remarque')

    @api.onchange('montant_vr','nombre_vr','valeur')
    def onchange_positive_value(self):
        if self.montant_vr < 0 or self.nombre_vr < 0 or self.valeur < 0:
            self.montant_vr = abs(self.montant_vr)
            self.nombre_vr = abs(self.nombre_vr)
            self.valeur = abs(self.valeur)
    
    @api.multi
    def verifier_paiement(self):
        if self.env.user.has_group('spc_recette_aziza.group_agent_validation_oscar') or self.env.user.has_group('spc_recette_aziza.group_agent_validation_ticket_resto_oscar'):
            self.filtered(lambda s: s.state == 'confirmed').write({'state': 'checked'})
            self.filtered(lambda s: s.montant_vr == 0.0).write({'montant_vr': self.montant})
            self.filtered(lambda s: s.nombre_vr == 0).write({'nombre_vr': self.nombre})
    
    @api.multi
    def annuler_paiement(self):
        if self.env.user.has_group('spc_recette_aziza.group_agent_validation_oscar') or self.env.user.has_group('spc_recette_aziza.group_agent_validation_ticket_resto_oscar'):
            self.filtered(lambda s: s.state == 'checked').write({'state': 'confirmed'})
            self.filtered(lambda s: s.montant_vr == self.montant).write({'montant_vr': 0.0})
            self.filtered(lambda s: s.nombre_vr ==  s.nombre).write({'nombre_vr': 0})
    
    @api.one
    @api.depends('valeur','nombre','nombre_vr')
    def _compute_montant(self):
        self.montant_compute = self.valeur * self.nombre
        self.montant_compute_vr = self.valeur * self.nombre_vr

    @api.one
    @api.depends('nombre', 'nombre_vr')
    def _compute_ecart(self):
        self.nombre_ecart = self.nombre_vr - self.nombre
