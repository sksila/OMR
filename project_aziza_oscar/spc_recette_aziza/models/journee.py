# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError
import operator
import itertools
import logging

_logger = logging.getLogger(__name__)


STATE_JOURNEE_SELECTION = [
    ('new', 'En préparation'),
    ('prepared', 'Clôturée'),
    ('road','En route'),
    ('done1','Reçue à l\'entrepôt'),
    ('done','Reçue au siège'),
    ('waiting','En attente'),
    ('accepted','Acceptée'),
    ('waiting2','En attente la deuxième vérification'),
    ('accepted1','Acceptée TR'),
    ('waiting1','En attente avec litige'),
    ('checked','Vérifiée'),
]

class Journee(models.Model):
    _name = 'oscar.journee'
    _description = 'Journée Magasin'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "date_journee desc"
     
    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id
    
    name = fields.Char('Description', compute="_compute_default_name", store=True)
    date_journee = fields.Date('Date journée', required="True", default=datetime.today().date(), readonly=True, states={'new': [('readonly', False)]})
    montant_global = fields.Float('Montant Total', digits=(12,3), store=True, readonly=True, compute='_compute_all', track_visibility='onchange')
    state = fields.Selection(STATE_JOURNEE_SELECTION, string='Statut', readonly=True, copy=False, index=True, default='new', track_visibility='onchange')
    comment = fields.Text(string="Notes internes")
    user_id = fields.Many2one('res.users', string='Utilisateur', index=True, default=lambda self: self.env.user, readonly=True, states={'new': [('readonly', False)]})
    magasin_id = fields.Many2one('oscar.site', string='Magasin', index=True, readonly=True, states={'new': [('readonly', False)]}, domain=[('site_type', '=', 'MAGASIN')])
    journee_line_ids = fields.One2many('oscar.journee.line', 'journee_id', string='Journée de caissier', readonly=True)
    ecart_ids = fields.One2many('oscar.ecart', 'journee_id',string='Écarts')
    
    currency_id = fields.Many2one('res.currency', string='Devise', required=True, default=_default_currency)
    
    montant_espece = fields.Monetary(string='Montant espèce', store=True, readonly=True, compute='_compute_all', currency_field='currency_id')
    total_cheque = fields.Monetary(string='Montant total des chèques', digits=(12,3), store=True, readonly=True, compute='_compute_all', currency_field='currency_id', track_visibility='onchange')
    total_carte_ban = fields.Monetary(string='Montant total des cartes bancaire', digits=(12,3), store=True, readonly=True, compute='_compute_all', currency_field='currency_id', track_visibility='onchange')
    total_sodexo = fields.Monetary(string='Montant total des cartes Sodexo', digits=(12,3), store=True, readonly=True, compute='_compute_all', currency_field='currency_id', track_visibility='onchange')
    total_autre_paiement = fields.Monetary(string='Montant total des autres paiements', digits=(12,3), store=True, readonly=True, compute='_compute_all', currency_field='currency_id', track_visibility='onchange')
    total_ticket_restaurant = fields.Monetary(string='Montant total des tickets restaurant', digits=(12,3), store=True, readonly=True, compute='_compute_all', currency_field='currency_id', track_visibility='onchange')
    total_cheque_cadeaux = fields.Monetary(string='Montant total des chéques cadeaux', digits=(12,3), store=True, readonly=True, compute='_compute_all', currency_field='currency_id', track_visibility='onchange')
    total_bon_aziza = fields.Monetary(string="Montant total des Bons d'achat Aziza", digits=(12,3), store=True, readonly=True, compute='_compute_all', currency_field='currency_id', track_visibility='onchange')
    total_vente_credit = fields.Monetary(string='Montant total de vente à crédit', digits=(12,3), store=True, readonly=True, compute='_compute_all', currency_field='currency_id', track_visibility='onchange')
   
    versement_ids = fields.One2many('oscar.versement', 'journee_id', string='Versements')
    montant_versement = fields.Monetary('Montant versé espèce', readonly=True, compute='_compute_versement', currency_field='currency_id')
    reste_a_verser = fields.Monetary('Reste à verser espèce', readonly=True, currency_field='currency_id', compute='_compute_all', store=True)
     
    caissier_count = fields.Integer(string='Nombre de journées', compute="_compute_caissier_count", readonly=True, store=True)
    ecart_count = fields.Integer(string='Nombre des écarts', compute="_compute_ecart_count", readonly=True, store=True)
    is_paid = fields.Boolean(string="Versée")
    
    envelope_id = fields.Many2one('oscar.envelope', string="Enveloppe", index=True)
     
    @api.one
    @api.depends('magasin_id.name','date_journee')
    def _compute_default_name(self):
        self.name = "[%s] %s" %(self.date_journee, self.magasin_id.name or "")

    @api.one
    @api.depends('journee_line_ids')
    def _compute_caissier_count(self):
        self.caissier_count = len(self.journee_line_ids.ids)

    @api.one
    @api.depends('ecart_ids.state','ecart_ids.type')
    def _compute_ecart_count(self):
        self.ecart_count = sum(1 for ecart in self.ecart_ids if ecart.type == 'ecart' and ecart.state in ['justify','justify1'])
    
    @api.multi
    @api.depends('versement_ids.montant_versement')
    def _compute_versement(self):
        for journee in self:
            journee.montant_versement = sum(line.montant_versement for line in journee.versement_ids)
    
    @api.one
    @api.depends('journee_line_ids.total_cheque','journee_line_ids.total_carte_ban',
                 'journee_line_ids.total_sodexo','journee_line_ids.total_autre_paiement',
                 'journee_line_ids.total_ticket_restaurant','journee_line_ids.total_cheque_cadeaux',
                 'journee_line_ids.montant_espece','journee_line_ids.montant_global',
                 'journee_line_ids.total_bon_aziza','journee_line_ids.total_vente_credit',
                 'versement_ids.montant_versement')
    def _compute_all(self):
        self.total_cheque = sum(line.total_cheque for line in self.journee_line_ids)
        self.total_carte_ban = sum(line.total_carte_ban for line in self.journee_line_ids)
        self.total_sodexo = sum(line.total_sodexo for line in self.journee_line_ids)
        self.total_autre_paiement = sum(line.total_autre_paiement for line in self.journee_line_ids)
        self.total_ticket_restaurant = sum(line.total_ticket_restaurant for line in self.journee_line_ids)
        self.total_cheque_cadeaux = sum(line.total_cheque_cadeaux for line in self.journee_line_ids)
         
        self.total_bon_aziza = sum(line.total_bon_aziza for line in self.journee_line_ids)
        self.total_vente_credit = sum(line.total_vente_credit for line in self.journee_line_ids)
         
        self.montant_espece = sum(line.montant_espece for line in self.journee_line_ids)
        self.montant_global = sum(line.montant_global for line in self.journee_line_ids)
        
        self.reste_a_verser = sum(line.montant_espece for line in self.journee_line_ids) - sum(line.montant_versement for line in self.versement_ids)
     
    @api.multi
    def preparer_journee(self):
        prepared = True
        for o in self.journee_line_ids:
            if o.state != 'prepared':
                prepared = False
        # if self.ecart_count > 0:
        #     for ecart in self.ecart_ids:
        #         if ecart.state == 'justify':
        #             if ecart.cmis_folder:
        #                 cmis = self.env['cmis.backend'].sudo().search([], limit=1)
        #                 repo = cmis.get_cmis_repository()
        #                 someDoc = repo.getObject(ecart.cmis_folder)
        #                 children = someDoc.getChildren()
        #                 if not children:
        #                     raise ValidationError("Veuillez joindre la fiche de caissier %s" % ecart.caissier_id.name)
        #             else:
        #                 raise ValidationError("Veuillez joindre la fiche de caissier %s" % ecart.caissier_id.name)
        if self.reste_a_verser > 0:
            raise ValidationError("Vous devez effectuer les versements de la journée avant la clôture !")           
        if prepared:
            self.filtered(lambda s: s.state == 'new').write({'state': 'prepared', 'user_id':self.env.user.id})
            message = _("Votre journée a été clôturée avec succès!")
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': message,
                    'type': 'rainbow_man',
                }
            }
        else:
            raise ValidationError("Veuillez clôturer les journées des caissiers !")
         

         
    @api.multi
    def recevoir_journees(self):
        if self.env.user.has_group('spc_recette_aziza.group_agent_reception_oscar'):
#               if record.last_br_id: record.last_br_id.filtered(lambda s: s.state == 'send').write({'state': 'done'}) 
            self.filtered(lambda s: s.state == 'road').write({'state': 'done'})
            if self.state == 'done':
                vals = {
                    'name' : self.name,
                    'date_journee' : self.date_journee,
                    'journee_id' : self.id,
                    'envelope_id' : self.envelope_id.id,
                    'user_id' : self.user_id.id,
                    'magasin_id' : self.magasin_id.id,
                    'montant_espece' : self.montant_espece,
                    'state' : self.state,
                    }
                journee_recue = self.env['oscar.journee.recue'].sudo().create(vals)
                if journee_recue:
                    for ecart_ids in self.ecart_ids:
                        journee_recue.write({'ecart_ids' : [(4, ecart_ids.id)]})
                    for journee in self.journee_line_ids:
                        if journee.bank_tpe_id:
                            journee_recue.write({'bank_tpe_id' : journee.bank_tpe_id.id})

                    #Group payment methods by amount and supplier and insert them into the table
                    sql_insert_group = ("""
                                INSERT INTO oscar_mode_paiement_recue 
                                    (
                                    date_journee,
                                    magasin_id,
                                    moyen_paiement_id,
                                    fournisseur_id,
                                    nombre,
                                    valeur,
                                    montant_compute,
                                    state,
                                    user_id,
                                    journee_recue_id
                                    )
                                    (SELECT 
                                    date_journee,
                                    magasin_id,
                                    moyen_paiement_id,
                                    fournisseur_id,
                                    SUM(nombre),
                                    valeur,
                                    SUM(montant_compute::NUMERIC),
                                    state,
                                    2,
                                    %s 
                                    FROM oscar_mode_paiement 
                                    WHERE date_journee='%s' AND magasin_id='%s' AND moyen_paiement_id IN (SELECT id FROM moyen_paiement WHERE code IN ('5','6','99'))
                                    GROUP BY 
                                    date_journee,
                                    magasin_id,
                                    moyen_paiement_id,
                                    fournisseur_id,
                                    valeur,
                                    state);
                                """ %(journee_recue.id,self.date_journee,self.magasin_id.id))
                    self._cr.execute(sql_insert_group)
                    sql_insert_other = ("""
                                INSERT INTO oscar_mode_paiement_recue 
                                    (
                                    date_journee,
                                    magasin_id,
                                    moyen_paiement_id,
                                    code_cheque,
                                    oscar_bank_id,
                                    bank_tpe_id,
                                    cin,
                                    name_user,
                                    phone_user,
                                    montant,
                                    state,
                                    user_id,
                                    journee_recue_id
                                    )
                                    (SELECT 
                                    date_journee,
                                    magasin_id,
                                    moyen_paiement_id,
                                    code_cheque,
                                    oscar_bank_id,
                                    bank_tpe_id,
                                    cin,
                                    name_user,
                                    phone_user,
                                    montant,
                                    state,
                                    user_id,
                                    %s 
                                    FROM oscar_mode_paiement 
                                    WHERE date_journee='%s' AND magasin_id='%s' AND moyen_paiement_id NOT IN (SELECT id FROM moyen_paiement WHERE code IN ('5','6','99')));
                                """ %(journee_recue.id,self.date_journee,self.magasin_id.id))
                    self._cr.execute(sql_insert_other)
                    dispatching = self.env['oscar.dispatching'].search([('magasin_id', '=', self.magasin_id.id),('start_date','<=', datetime.now()),('end_date','>=',datetime.now())], limit=1, order="end_date desc")
                    if dispatching:
                        journee_recue.write({'controller_id' : dispatching.controller_id.id, 'controller_tr_id' : dispatching.controller_tr_id.id, 'state' : 'waiting'})
                else: raise ValidationError("Veuillez vérifier votre journée !")
        else: raise ValidationError("Vous n'avez pas l'autorisation de recevoir les journées!")
                     
     
    @api.multi
    def unlink(self):
        '''
        Delete the references of this journee
        '''
        for journee in self:
            journee.ecart_ids.unlink()
        return models.Model.unlink(self)
 
class JourneeLine(models.Model):
    _name = 'oscar.journee.line'
    _description = 'Journée de caissier'
    _order = "date_journee desc"
    _rec_name = 'date_journee'
     
    date_journee = fields.Date(string='Date journée', readonly=True, related='journee_id.date_journee', store=True)
    montant_global = fields.Float('Montant global', digits=(12,3), compute='_compute_all', track_visibility='onchange')
    bank_tpe_id = fields.Many2one('res.partner.bank', string='TPE', help='Terminal de Paiement Électronique', readonly=True, states={'new': [('readonly', False)]})
    total_cheque = fields.Float(string='Montant total des cheques', digits=(12,3), store=True, readonly=True, compute='_compute_all', track_visibility='onchange')
    total_carte_ban = fields.Float(string='Montant total des cartes bancaires', digits=(12,3), store=True, readonly=True, compute='_compute_all', track_visibility='onchange')
    total_sodexo = fields.Float(string='Montant total des cartes Sodexo', digits=(12,3), store=True, readonly=True, compute='_compute_all', track_visibility='onchange')
    total_autre_paiement = fields.Float(string='Montant total des autres paiement', digits=(12,3), store=True, readonly=True, compute='_compute_all', track_visibility='onchange')
    total_ticket_restaurant = fields.Float(string='Montant total des tickets restaurant', digits=(12,3), store=True, readonly=True, compute='_compute_all', track_visibility='onchange')
    total_cheque_cadeaux = fields.Float(string='Montant total des chéques cadeaux', digits=(12,3), store=True, readonly=True, compute='_compute_all', track_visibility='onchange')
    total_bon_aziza = fields.Float(string="Montant total des Bons d'achat Aziza", digits=(12,3), store=True, readonly=True, compute='_compute_all', track_visibility='onchange')
    total_vente_credit = fields.Float(string='Montant total de vente à crédit', digits=(12,3), store=True, readonly=True, compute='_compute_all', track_visibility='onchange')
    montant_espece = fields.Float(string='Montant Espèce', digits=(12,3), track_visibility='onchange', readonly=True, states={'new': [('readonly', False)]})
    espece_gold = fields.Float(string='Espèce (Caisse)', digits=(12,3))
    tr_gold = fields.Float(string='Ticket restaurant (Caisse)', digits=(12,3))
    cc_gold = fields.Float(string='Chéque cadeaux (Caisse)', digits=(12,3))
    cheque_gold = fields.Float(string='Chéque (Caisse)', digits=(12,3))
    cb_gold = fields.Float(string='Carte bancaire (Caisse)', digits=(12,3))
    cs_gold = fields.Float(string='Carte sodexo (Caisse)', digits=(12,3))
    ba_gold = fields.Float(string='Bon AZIZA (Caisse)', digits=(12,3))
    vc_gold = fields.Float(string='Vente à crédit (Caisse)', digits=(12,3))
    other_gold = fields.Float(string='Autres paiement (Caisse)', digits=(12,3))
    caissier_id = fields.Many2one('hr.employee', string='Caissier', index=True, domain=[('est_caissier', '=', True)])
    magasin_id = fields.Many2one('oscar.site', string='Magasin', domain=[('site_type', '=', 'MAGASIN')])
    journee_id = fields.Many2one('oscar.journee', string='Journée', index=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', string='Utilisateur', default=lambda self: self.env.user, readonly=True, states={'new': [('readonly', False)]})
    state = fields.Selection(STATE_JOURNEE_SELECTION, string='Statut', readonly=True, copy=False, index=True, default='new')
    mode_tr_ids = fields.One2many('oscar.mode.paiement', 'journee_line_id', string='TR', domain=lambda self: [('moyen_paiement_id.id', '=', self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_ticket_restaurant').id)], readonly=True, states={'new': [('readonly', False)]})
    mode_cc_ids = fields.One2many('oscar.mode.paiement', inverse_name='journee_line_id', string='CC', domain=lambda self: [('moyen_paiement_id.id', '=', self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_cadeaux').id)], readonly=True, states={'new': [('readonly', False)]})
    mode_cb_ids = fields.One2many('oscar.mode.paiement', inverse_name='journee_line_id', string='CB', domain=lambda self: [('moyen_paiement_id.id', '=', self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_ban').id)], readonly=True, states={'new': [('readonly', False)]})
    mode_cs_ids = fields.One2many('oscar.mode.paiement', inverse_name='journee_line_id', string='CS', domain=lambda self: [('moyen_paiement_id.id', '=', self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_sodexo').id)], readonly=True, states={'new': [('readonly', False)]})
    mode_cheque_ids = fields.One2many('oscar.mode.paiement', inverse_name='journee_line_id', string='Chèque', domain=lambda self: [('moyen_paiement_id.id', '=', self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_cheque').id)], readonly=True, states={'new': [('readonly', False)]})
    mode_ba_ids = fields.One2many('oscar.mode.paiement', inverse_name='journee_line_id', string='Bon AZIZA', domain=lambda self: [('moyen_paiement_id.id', '=', self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_bon_achat').id)], readonly=True, states={'new': [('readonly', False)]})
    mode_vc_ids = fields.One2many('oscar.mode.paiement', inverse_name='journee_line_id', string='VC', domain=lambda self: [('moyen_paiement_id.id', '=', self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_vente_credit').id)], readonly=True, states={'new': [('readonly', False)]}, help="Vente à crédit")
    mode_other_ids = fields.One2many('oscar.mode.paiement', inverse_name='journee_line_id', string='Autres Paiement', domain=['|',('moyen_paiement_id', '=', False),('moyen_paiement_id.is_other', '=', True)], readonly=True, states={'new': [('readonly', False)]})
    
    check = fields.Boolean("A vérifier")
    
    flyer_ids = fields.One2many('oscar.mode.paiement', inverse_name='journee_line_id', string='Action Flyers', domain=lambda self: [('moyen_paiement_id.id', '=', self.env.ref('spc_recette_aziza.data_oscar_mode_action_flyers').id)], readonly=True, states={'new': [('readonly', False)]})
    flyers_mg_count = fields.Integer(string="Nombre de flyers", store=True, readonly=True, compute='_compute_all')
    flyers_gold_count = fields.Integer(string="Nombre de flyers (Caisse)")
    
    @api.onchange('bank_tpe_id')
    def onchange_bank_tpe_id(self):
        if self.mode_cb_ids:
            for cb in self.mode_cb_ids:
                if not cb.oscar_bank_id:
                    cb.write({'bank_tpe_id': self.bank_tpe_id.id})
    
    @api.onchange('montant_espece')
    def onchange_positive_value(self):
        if self.montant_espece < 0:
            self.montant_espece = abs(self.montant_espece)
     
    @api.one
    @api.depends('magasin_id.name','date_journee')
    def _compute_default_name(self):
        self.name = "[%s] %s" %(self.date_journee, self.magasin_id.name or "")
         
    @api.one
    @api.depends('montant_espece','total_ticket_restaurant',
                 'total_cheque_cadeaux','total_cheque',
                 'total_carte_ban','total_sodexo','total_vente_credit','total_bon_aziza','total_autre_paiement',
                 'mode_tr_ids.montant_compute','mode_cc_ids.montant_compute',
                 'mode_cheque_ids.montant', 'mode_cheque_ids.state', 
                 'mode_cb_ids.montant', 'mode_cb_ids.state',
                 'mode_cs_ids.montant','mode_cs_ids.state',
                 'mode_ba_ids.montant','mode_vc_ids.montant',
                 'mode_other_ids.montant','flyer_ids.nombre')
    def _compute_all(self):                
        self.total_ticket_restaurant = sum(line.montant_compute for line in self.mode_tr_ids)
        self.total_cheque_cadeaux = sum(line.montant_compute for line in self.mode_cc_ids)
        self.total_cheque = sum(line.montant for line in self.mode_cheque_ids if line.state in ['confirmed','checked'])
        self.total_carte_ban = sum(line.montant for line in self.mode_cb_ids if line.state in ['confirmed','checked'])
        self.total_sodexo = sum(line.montant for line in self.mode_cs_ids if line.state in ['confirmed','checked'])
        self.total_bon_aziza = sum(line.montant for line in self.mode_ba_ids)
        self.total_vente_credit = sum(line.montant for line in self.mode_vc_ids)
        self.total_autre_paiement = sum(line.montant for line in self.mode_other_ids)
        self.montant_global = self.montant_espece + self.total_cheque + self.total_carte_ban + self.total_sodexo + self.total_autre_paiement + self.total_ticket_restaurant + self.total_cheque_cadeaux + self.total_vente_credit + self.total_bon_aziza
        self.flyers_mg_count = sum(line.nombre for line in self.flyer_ids if line.state in ['confirmed','checked'])
 
    @api.multi
    def preparer_journee(self):
        # verifier le services "Livraison à domicile" et "Click and Collect"
        records = self.mode_other_ids.filtered(lambda m: m.moyen_paiement_id.is_process == True)
        if records:
            self.check = True
            return
        
        if self.mode_cb_ids and not self.bank_tpe_id:
            raise ValidationError("Veuillez saisir le TPE de Magasin")
        ecart = False
        espece_gold = self.espece_gold
        tr_gold = sum(line.valeur * line.nombre_gold for line in self.mode_tr_ids)
        cc_gold = sum(line.valeur * line.nombre_gold for line in self.mode_cc_ids)
        cheque_gold = sum(line.montant_gold for line in self.mode_cheque_ids)
        cb_gold = sum(line.montant_gold for line in self.mode_cb_ids)
        cs_gold = sum(line.montant_gold for line in self.mode_cs_ids)
        ba_gold = sum(line.montant_gold for line in self.mode_ba_ids)
        vc_gold = sum(line.montant_gold for line in self.mode_vc_ids)
        other_gold = sum(line.montant_gold for line in self.mode_other_ids)
        flyers_gold_count = sum(line.nombre_gold for line in self.flyer_ids)
        ''' 
        add new sum of a new payment mode
        '''
        bool_esp = ("%.3f" % self.montant_espece) == ("%.3f" % espece_gold)
        bool_tr = ("%.3f" % self.total_ticket_restaurant) == ("%.3f" % tr_gold)
        bool_cc = ("%.3f" % self.total_cheque_cadeaux) == ("%.3f" % cc_gold)
        bool_cb = ("%.3f" % self.total_carte_ban) == ("%.3f" % cb_gold)
        bool_cheque = ("%.3f" % self.total_cheque) == ("%.3f" % cheque_gold)
        bool_cs = ("%.3f" % self.total_sodexo) == ("%.3f" % cs_gold)
        bool_ba = ("%.3f" % self.total_bon_aziza) == ("%.3f" % ba_gold)
        bool_vc = ("%.3f" % self.total_vente_credit) == ("%.3f" % vc_gold)
        bool_other = True #("%.3f" % self.total_autre_paiement) == ("%.3f" % other_gold)
        bool_flyers = self.flyers_mg_count == flyers_gold_count

        other_paiements = sorted(self.mode_other_ids, key=operator.itemgetter("moyen_paiement_id","montant","montant_gold"))
        outputList = []
        for mp, list_g in itertools.groupby(other_paiements, key=operator.itemgetter("moyen_paiement_id")):
            # mp : moyen paiement
            # list_g : liste regroupée par moyen de paiement

            list_g = list(list_g)
            montant = 0
            montant_caisse = 0
            for line in list_g:
                montant += line.montant
                montant_caisse += line.montant_gold
            ecart = round(montant,3) - round(montant_caisse,3)
            if ecart != 0.0:
                bool_other = False
            outputList.append(list_g)

        if (bool_esp and 
            bool_tr and 
            bool_cc and 
            bool_cb and 
            bool_cheque and 
            bool_cs and 
            bool_ba and 
            bool_vc and 
            bool_other and
            bool_flyers):
             
            ecart = False
        else:
            ecart = True
        if ecart == False:
            self.filtered(lambda s: s.state == 'new').write({'state': 'prepared','user_id':self.env.user.id})
        elif ecart:
             
            '''
            * Calculer les ecarts
             
            '''
            obj = []
            ecart_sodexo = self.total_sodexo - cs_gold
            ecart_bancaire = self.total_carte_ban - cb_gold
            ecart_cheque = self.total_cheque - cheque_gold
            ecart_espece = self.montant_espece - espece_gold
            ecart_cadeaux = self.total_cheque_cadeaux - cc_gold
            ecart_ticket = self.total_ticket_restaurant - tr_gold
             
            ecart_ba = self.total_bon_aziza - ba_gold
            ecart_vc = self.total_vente_credit - vc_gold
            
            ecart_flyers = self.flyers_mg_count - flyers_gold_count
             
            pourcentage = (abs(ecart_ticket) * 10) / 100
            if ecart_ticket > 0:
                ecart_ticket_js = ecart_ticket - pourcentage
            elif ecart_ticket < 0:
                ecart_ticket_js = ecart_ticket + pourcentage

            '''
            ** supp les ecarts si on va faire 2eme verification
            '''
            self.env['oscar.ecart'].sudo().search([('caissier_id','=',self.caissier_id.id),('journee_id','=',self.journee_id.id)]).unlink()
            '''
            *** Insérer les ecarts dans tab obj
            '''
             
            if ecart_ticket != 0:
                obj.append((0,0,{'name': self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_ticket_restaurant').id,
                                 'ecart': ecart_ticket, 'ecart_js': ecart_ticket_js}))
            if ecart_cadeaux != 0:
                obj.append((0,0,{'name': self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_cadeaux').id,
                                 'ecart': ecart_cadeaux, 'ecart_js': ecart_cadeaux}))
            if ecart_espece != 0:
                obj.append((0,0,{'name': self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_espece').id,
                                 'ecart': ecart_espece, 'ecart_js': ecart_espece}))
            if ecart_cheque != 0:
                obj.append((0,0,{'name': self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_cheque').id,
                                 'ecart': ecart_cheque, 'ecart_js': ecart_cheque}))
            if ecart_bancaire != 0:
                obj.append((0,0,{'name': self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_ban').id,
                                 'ecart': ecart_bancaire, 'ecart_js': ecart_bancaire}))
            if ecart_sodexo != 0:
                obj.append((0,0,{'name': self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_sodexo').id,
                                 'ecart': ecart_sodexo, 'ecart_js': ecart_sodexo}))
            if ecart_ba != 0:
                obj.append((0,0,{'name': self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_bon_achat').id,
                                 'ecart': ecart_ba, 'ecart_js': ecart_ba}))
            if ecart_vc != 0:
                obj.append((0,0,{'name': self.env.ref('spc_recette_aziza.data_oscar_mode_paiement_vente_credit').id,
                                 'ecart': ecart_vc, 'ecart_js': ecart_vc}))
            if ecart_flyers != 0:
                obj.append((0,0,{'name': self.env.ref('spc_recette_aziza.data_oscar_mode_action_flyers').id,
                                 'ecart': ecart_flyers, 'ecart_js': ecart_flyers, 'ecart_unit': 'quantity'}))
            for m in self.env['moyen.paiement'].search([('is_other','=', True)]):
                montant = sum(line.montant for line in self.mode_other_ids if line.moyen_paiement_id.id == m.id)
                montant_gold = sum(line.montant_gold for line in self.mode_other_ids if line.moyen_paiement_id.id == m.id)
                ecart_autre = montant - montant_gold
                if ecart_autre != 0:
                    obj.append((0,0,{'name':m.id,'ecart': ecart_autre, 'ecart_js': ecart_autre}))

            '''
            **** Creation les litiges sur BD
            '''
            ecart = self.env['oscar.ecart'].search([('journee_id', '=', self.journee_id.id),('caissier_id','=',self.caissier_id.id)], limit=1)
             
            if ecart.id:
                ecart.write({'ecart_line_ids' : obj})
            else:
                vals = {
                    'journee_id': self.journee_id.id,
                    'caissier_id': self.caissier_id.id,
                    'type': 'ecart',
                    'magasin_id': self.journee_id.magasin_id.id,
                    'user_id': self.env.user.id,
                    'ecart_line_ids': obj,
                    }
                ecart = self.env['oscar.ecart'].create(vals)
             
            context = {'default_id': ecart.id,
                       'default_journee_id': self.journee_id.id,
                       'default_caissier_id': self.caissier_id.id,
                       'default_type' : 'ecart',
                       'default_magasin_id': self.journee_id.magasin_id.id,
                       'default_ecart_line_ids': ecart.ecart_line_ids.ids,}
            return {
            'name': 'Ecarts',
            'res_id': ecart.id,
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'oscar.ecart',
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new',
            }
 
class MoyenPaiement(models.Model):
    _name = 'moyen.paiement'
    _description = 'Moyen de paiement'
    _order = "id asc"
 
    name = fields.Char(string='Libellé', required=True)
    code = fields.Char(string='Code')
    lb_court = fields.Char(string='Libellé court')
    is_other = fields.Boolean('Autres')
    is_process = fields.Boolean('Est un processus')
    unit_type = fields.Selection([
        ('amount', 'Montant'),
        ('quantity', 'Quantité'),
        ], string='Type', default='amount')
    active = fields.Boolean(string='Activé', default=True)
    
    _sql_constraints = [
        ('code_moyen_paiement_unique', 'UNIQUE (code)', 'Le code de moyen de paiement doit être unique !')
    ]
 
class ModePaiement(models.Model):
    _name = 'oscar.mode.paiement'
    _description = "Modes de paiement"
    _rec_name = 'moyen_paiement_id'
     
    def _default_moyen_paiement(self):
        if self._context.get('default_code'):
            return self.env['moyen.paiement'].search([('code','=',self._context.get('default_code'))], limit=1)
        else:
            return
         
    moyen_paiement_id = fields.Many2one('moyen.paiement', string="Moyen de paiement", default=_default_moyen_paiement)
    origine_id = fields.Many2one('moyen.paiement', string="Origine", default=_default_moyen_paiement)
    code_cheque = fields.Char(string='Code')
    date_journee = fields.Date(string='Date journée', related='journee_line_id.date_journee', store=True)
    caissier_id = fields.Many2one('hr.employee', string='Caissier', index=True, related='journee_line_id.caissier_id', store=True, domain=[('est_caissier', '=', True)])
    magasin_id = fields.Many2one('oscar.site', string='Magasin', index=True, related='journee_line_id.magasin_id', store=True, domain=[('site_type', '=', 'MAGASIN')])
    montant = fields.Float('Montant', digits=(12,3))
    montant_gold = fields.Float('Montant Caisse', digits=(12,3), readonly=True)
    montant_compute = fields.Float('Montant', digits=(12,3), readonly=True, compute='_compute_montant', store=True)
    cin = fields.Char('CIN')
    name_user = fields.Char('Nom titulaire')
    phone_user = fields.Char(string='Tél titulaire')
    oscar_bank_id = fields.Many2one('res.bank', string='Banque')
    bank_tpe_id = fields.Many2one('res.partner.bank', string='TPE', help='Terminal de Paiement Électronique')
    fournisseur_id = fields.Many2one('res.partner', string='Fournisseur')
    valeur = fields.Float(string='Valeur', digits=(12,3))
    nombre = fields.Integer(string='Nombre')
    nombre_gold = fields.Integer(string='Nombre (Caisse)', readonly=True)
    nombre_vr = fields.Integer(string='Nombre verifié')
    montant_vr = fields.Float('Montant verifié', digits=(12,3))
    montant_compute_vr = fields.Float('Montant verifié', digits=(12,3), readonly=True, compute='_compute_montant', store=True)
    user_id = fields.Many2one('res.users', string='Utilisateur', index=True, default=lambda self: self.env.user)
    journee_line_id = fields.Many2one('oscar.journee.line', string='Journee', index=True, ondelete='cascade')
    journee_recue_id = fields.Many2one('oscar.journee.recue', index=True, string='Journée')
    
    is_refund = fields.Boolean('Est un avoir')
    num_avoir = fields.Char(string="Numéro d'avoir")
    
    state = fields.Selection([
        ('new', 'Nouveau'),
        ('confirmed', 'Confirmé'),
        ('checked', 'Vérifié'),
        ], string='Statut', default='confirmed', readonly=True, copy=False)
     
    state_journee = fields.Selection(STATE_JOURNEE_SELECTION, string='Statut de journée', readonly=True, index=True, related='journee_line_id.state')
    active = fields.Boolean(string='Activé', default=True)
    
    @api.onchange('montant','nombre','valeur')
    def onchange_positive_value(self):
        if self.montant < 0 or self.nombre < 0 or self.valeur < 0:
            self.montant = abs(self.montant)
            self.nombre = abs(self.nombre)
            self.valeur = abs(self.valeur)
     
    @api.multi  
    def valider_paiement(self):
        if self.moyen_paiement_id.code == "2" :
            if self.code_cheque and self.oscar_bank_id:
                self.filtered(lambda s: s.state == 'new').write({'state': 'confirmed'})
                self.filtered(lambda s: s.montant == 0.0).write({'montant': self.montant_gold})
            else:
                raise ValidationError("Veuillez vérifier les champs (Code et Banque) de Chèque !")
        else:
            self.filtered(lambda s: s.state == 'new').write({'state': 'confirmed'})
            self.filtered(lambda s: s.montant == 0.0).write({'montant': self.montant_gold})
            self.filtered(lambda s: s.nombre == 0).write({'nombre': self.nombre_gold})
     
    @api.multi  
    def annuler_paiement(self):
        if self.env.user.has_group('spc_oscar_aziza.group_reponsable_magasin'):
            self.filtered(lambda s: s.state == 'confirmed').write({'state': 'new'})
            self.filtered(lambda s: s.montant == s.montant_gold).write({'montant': 0.0})
            self.filtered(lambda s: s.nombre ==  s.nombre_gold).write({'nombre': 0})
     
     
    @api.one
    @api.depends('valeur','nombre','nombre_vr')
    def _compute_montant(self):
        self.montant_compute = self.valeur * self.nombre
        self.montant_compute_vr = self.valeur * self.nombre_vr
 
    @api.model
    def create(self, vals):
        result = super(ModePaiement, self).create(vals)
        return result
     
    @api.multi
    def write(self, vals):
        return super(ModePaiement, self).write(vals)
     
    @api.multi
    def copy(self, default=None):
        default = dict(default or {})
        _logger.info("Payment mode is duplicated _-_-_ %s" %(default), exc_info=True)
        default.update({'journee_line_id': False})
        return super(ModePaiement, self).copy(default)
    