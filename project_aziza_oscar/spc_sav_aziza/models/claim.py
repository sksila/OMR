# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime,timedelta
from odoo.exceptions import ValidationError
# from .ngtapi import Sms,NgTrendSMS
from time import sleep
import logging
import string

_logger = logging.getLogger(__name__)


STATE_CLAIM_SELECTION = [
    ('new', 'Nouvelle'),
    ('road','En route vers SAV'),
    ('done1','Reçue à l\'Entrepôt'),
    ('done2','Reçue au Siège (SAV)'),
    ('repair','En réparation'),
    ('waiting','En attente la validation RM'),
    ('validated','Validée par Magasin'),
    ('fixed','Réparée'),
    ('refuse','Refusée'),
    ('road1','En route vers magasin'),
    ('done01','Reçue à l\'Entrepôt'),
    ('back','Avoir'),
    ('exchanged','Echange'),
    ('done3','Reçue au Magasin'),
    ('done4','Clôturée'),
]


class Claim(models.Model):
    _name = 'oscar.sav.claim'
    _description = 'Réclamation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "date_claim desc"

    _sql_constraints = [
        ('code_remboursement_uniq', 'unique (code_remboursement)', 'Le code de remboursement doit etre unique !')]

    #region Default methods
    def _default_magasin(self):
        if self.env.user.has_group("spc_oscar_aziza.group_reponsable_magasin"):
            return self.env['oscar.site'].search([('user_ids', 'child_of', [self.env.uid])], limit=1)
        return
    # endregion
    
    # region Fields declaration
    name = fields.Char(string='Numéro réclamation',readonly=True,copy=False, track_visibility='onchange')
    date_claim = fields.Date(string='Date de réclamation', required=True, default=fields.Date.context_today, track_visibility='onchange', readonly=True, states={'new': [('readonly', False)]})
    customer_id = fields.Many2one('res.partner', string='Client', index=True,track_visibility='onchange', readonly=True, states={'new': [('readonly', False)]}, domain="[('phone','=','to_disable_many2one_autocomplete')]")
    phone = fields.Char(string='N° Téléphone', related='customer_id.phone', readonly=False )
    #address = fields.Char(string='Adresse Client', related='customer_id.address')
    #cin = fields.Char(string='C.I.N', related='customer_id.cin')
    date_purchase = fields.Date(string="Date d'achat",readonly=True, states={'new': [('readonly', False)]})
    product_id = fields.Many2one('product.template', string='Article', index=True, required=False, track_visibility='onchange', readonly=True, states={'new': [('readonly', False)]}, domain=[('is_sav_product', '=', True)])
    product_supplier_ids = fields.Many2many('res.partner', related="product_id.supplier_ids")
    code = fields.Char(string='N° de série', readonly=True, states={'new': [('readonly', False)],'repair': [('readonly', False)]})
    barcode = fields.Char(string='Code Barre', related='product_id.barcode', readonly=True, store=True)
    supplier_id = fields.Many2one('res.partner', string='Fournisseur', index=True)
    categ_id = fields.Many2one('product.category', string='Catégorie', index=True)
    panne = fields.Text(string='Panne', readonly=True, states={'new': [('readonly', False)],'repair': [('readonly', False)]})
    problem_id = fields.Many2one('oscar.sav.problem', string='Problème', index=True, readonly=True, states={'new': [('readonly', False)],'repair': [('readonly', False)]})
    other = fields.Boolean(string="Autre", readonly=True, states={'new': [('readonly', False)],'repair': [('readonly', False)]})
    magasin_id = fields.Many2one('oscar.site', string='Magasin', index=True, default=_default_magasin, readonly=True, states={'new': [('readonly', False)]},domain=[('site_type', '=', 'MAGASIN')])
    user_id = fields.Many2one('res.users', string='Réceptionné par', index=True, default=lambda self: self.env.user, readonly=True, states={'new': [('readonly', False)]})
    user_dest_id = fields.Many2one('res.users', string='Destination', index=True, readonly=True)
    date_end_guarantee = fields.Date(string="Date fin de garantie", readonly=True, states={'new': [('readonly', False)]})
    has_receipt = fields.Boolean(string="Ticket / Facture", readonly=True, states={'new': [('readonly', False)]})
    has_guarantee = fields.Boolean(string="Certificat de garantie", readonly=True, states={'new': [('readonly', False)]})
    has_accessories = fields.Boolean(string="Présence accessoires", readonly=True, states={'new': [('readonly', False)]})
    repair_mode = fields.Selection([
        ('guarantee', 'Sous garantie'),
        ('not_guarantee', 'Hors garantie'),
        ], string='Nature réparation', default='guarantee', readonly=True, states={'repair': [('readonly', False)]})
    repair_note = fields.Text(string='Commentaire du Réparateur', readonly=True, states={'repair': [('readonly', False)]})
    comment = fields.Text(string='Commentaire')
#     bordereau_ids = fields.Many2many('oscar.sav.bordereau', 'sav_bordereau_claim_rel', 'claim_id', 'bordereau_id', string='Bordereaux')
    state = fields.Selection(STATE_CLAIM_SELECTION, string='Statut', readonly=True, copy=False, index=True, default='new', track_visibility='onchange')
    bordereaux_count = fields.Integer(string='Nombre des bordereaux', compute="_compute_bordereaux_count", readonly=True)
    is_fixed = fields.Boolean(string="Réparée")
    is_refused = fields.Boolean(string="Refusée")
    is_exchanged = fields.Boolean(string="Echange")
    is_back = fields.Boolean(string="Avoir")
    is_receive = fields.Boolean(string="Réceptionné par le client")
    is_back_stock_sav = fields.Boolean(string="Retour Stock SAV")
#     combination = fields.Char(string="Client et Tel",related='customer_id.combination')
    type=fields.Selection([('reclamation_interne','RI'),('reclamation_client','RC')],string='Type de réclamation',track_visibility='onchange',readonly=True,default='reclamation_client',states={'new': [('readonly', False)]})
    number_gold = fields.Char(string='Numéro de transfert Gold')
    number_avoir = fields.Char(string='Numéro Avoir')
    check_date = fields.Boolean(string='vérifier la date de réclamation et la date courante')
    code_magasin = fields.Char(string='Code Magasin')
    code_customer = fields.Char(string='Code Client')
    code_problem = fields.Char(string='Code Probleme')
    code_user = fields.Char(string='Code Utilisateur')
    domain_problem_ids = fields.Many2many('oscar.sav.problem')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.ref('base.TND').id)
    montant = fields.Monetary(string='Montant', currency_field='currency_id')
    code_remboursement = fields.Char('Code de remboursement')

    envelope_ids = fields.Many2many('oscar.envelope', 'claim_envelope_rel', 'oscar_sav_claim_id', 'envelope_id'
                                          , string='Enveloppes', readonly=True, states={'new': [('readonly', False)]})
    envelope_count = fields.Integer(string='Nombre des enveloppes', compute="_compute_envelope_count")
    # endregion

    origin_site_id = fields.Many2one('oscar.site', string="Magasin d'origine", default=_default_magasin, index=True, readonly=True, states={'new': [('readonly', False)]},domain=[('site_type', '=', 'MAGASIN')])

    _sql_constraints = [
        ('name_unique', 'UNIQUE (name)', 'Le numéro de réclamation doit être unique !')
    ]

    # region Fields method

    @api.one
    @api.depends('envelope_ids')
    def _compute_envelope_count(self):
        self.envelope_count = len(self.envelope_ids.ids)

    @api.multi
    def add_follower(self):
        groups_id = self.env.ref('spc_sav_aziza.group_responsable_sav').id
        user = self.env['res.users'].search([('groups_id', 'in', [groups_id])])
        partners_ids = []
        for rec in user:
            partners_ids.append(rec.partner_id.id)
        partner = self.env['res.partner'].search([('id', 'in', partners_ids)])
        subtypes = self.env['mail.message.subtype'].search([])
        if user:
            self.message_subscribe(partner_ids=partner.ids, subtype_ids= subtypes.ids)

    def _sent_sms_create_to_customer(self, customer):
        ng_trend_obj = self.env['spc.sms.ng_trend'].sudo()
        if self.env["ir.config_parameter"].sudo().get_param('spc_sav_aziza.endpoint'):
            message='Bonjour %s, Nous vous informons que votre article a bien été pris en charge par Aziza avec le numéro de réclamation %s. Nous reviendrons vers vous dans un délai de 30 jours.' %(customer.name, self.name)
            destinations=[customer.phone]
            date=datetime.now()
            reference='%s' %(self.name)
            sms = ng_trend_obj.generate_sms(message=message, destinations=destinations, date=date, reference=reference)
            response = ng_trend_obj.send_message(sms)
            sleep(1)
            stat_res = ng_trend_obj.sms_status(sms)
            _logger.info("SMS State : %s" %(stat_res), exc_info=True)
            if response.status_code == 200:
                return True
            else:
                pass

    @api.multi
    def sent_to_supplier(self):
        #calculer la duree de statut en reparation
        if (self.env.user.has_group('spc_sav_aziza.group_responsable_sav')):
            for record in self:
                if record.state == 'done2':
                    record.filtered(lambda s: s.state == 'done2').write({'state': 'repair'})

                else: raise ValidationError("Vous ne pouvez pas envoyer la réclamation %s vers le fournisseur,\n Veuillez vérifier leur statut!" % record.name)
        else: raise ValidationError("Vous n'avez pas de l'autorisation d'envoyer les réclamations vers le fournisseur")
    
    @api.multi
    def to_repair(self):
        #calculer la duree de statut en reparation

        self.filtered(lambda s: s.state in ['repair','validated']).write({'state': 'fixed', 'is_fixed': True })
    
    @api.multi
    def to_print(self):
        """ imprimer la réclamation
        """

        return self.env.ref('spc_sav_aziza.oscar_sav_claims').report_action(self)
    
    @api.multi
    def action_receive(self):
        for record in self:
            record.filtered(lambda s: s.state == 'back').write({'is_receive': True})
            record.filtered(lambda s: s.state in ['exchanged','done3']).write({'is_receive': True,'state' :'done4'})
    
    @api.multi
    def action_confirm(self):
        is_order = False
        cmis = self.env['cmis.backend'].search([], limit=1)
        repo = cmis.get_cmis_repository()
        if self.cmis_folder:
            someDoc = repo.getObject(self.cmis_folder)
            children = someDoc.getChildren()
            if children:
                for doc in children:
                    _logger.info("Doc ===== %s" %(doc.name), exc_info=True)
                    if (str(doc.name).find('dev') >= 0) or (str(doc.name).find('DEV') >= 0):
#                         raise ValidationError('dev',str(doc.name).find('dev'),'DEV',(str(doc.name).find('DEV') < 0))
#                         str(doc.name).find('ticket') < 0 or str(doc.name).find('caisse') < 0
                        is_order = True
                if not is_order:
                    raise ValidationError("Veuillez joindre le Devis de la réparation")
#                   createFolder = someDoc.createFolder('Devis')
#                   _logger.info("createFolder : %s" %(createFolder), exc_info=True)
                else:
                    self.filtered(lambda s: s.state == 'repair').write({'state': 'waiting'})
            else:
                raise ValidationError("Veuillez joindre le Devis de la réparation")
        else:
            raise ValidationError("Veuillez créer le répertoire dans la GED")
    
    @api.multi
    def action_refuse(self):
        for record in self:
            record.filtered(lambda s: s.state == 'waiting').write({'state': 'refuse', 'is_refused': True})
    
    @api.multi
    def action_validate(self):
        is_ticket = False
        cmis = self.env['cmis.backend'].search([], limit=1)
        repo = cmis.get_cmis_repository()
        if self.cmis_folder:
            someDoc = repo.getObject(self.cmis_folder)
            children = someDoc.getChildren()
            if children:
                for doc in children:
                    _logger.info("Doc ===== %s" %(doc.name), exc_info=True)
                    if (str(doc.name).find('ticket') >= 0) or (str(doc.name).find('caisse') >= 0):
                        is_ticket = True
                if not is_ticket:
                    raise ValidationError("Veuillez joindre le ticket de caisse")
                else:
                    self.filtered(lambda s: s.state == 'waiting').write({'state': 'validated'})
            else:    
                raise ValidationError("Veuillez joindre le ticket de caisse")
        else:
            raise ValidationError("Veuillez créer le répertoire dans la GED")
        
    
    def _sent_sms_to_customer(self, customer, product, magasin):
        ng_trend_obj = self.env['spc.sms.ng_trend'].sudo()
        if self.env["ir.config_parameter"].sudo().get_param('spc_sav_aziza.endpoint'):
            message='Bonjour %s,\nVotre Article %s est à votre disposition au %s. Prière de le récupérer.\nMerci pour votre confiance.' %(customer.name, product.name, magasin.name)
            destinations=[customer.phone]
            date=datetime.now()
            reference='%s' %(self.name)
            sms = ng_trend_obj.generate_sms(message=message, destinations=destinations, date=date, reference=reference)
            response = ng_trend_obj.send_message(sms)
            sleep(1)
            stat_res = ng_trend_obj.sms_status(sms)
            _logger.info("SMS State : %s" %(stat_res), exc_info=True)
            if response.status_code == 200:
                return True
            else:
                pass

    # def send_mail_avoir_or_echange_emails(self):
    #     email_ids = ''
    #     email_ids = str(magasin_id.resp_zone_id.partner_id.email) + ',' + str(magasin_id.user_id.partner_id.email)
    #     for user in self.env.ref('spc_sav_aziza.group_responsable_sav').users:
    #         email_ids = email_ids + ',' + str(user.partner_id.email)
    #     return email_ids

    def send_mail_avoir_or_echange(self,avoir,echange):
        template = ""
        if avoir:
            template = self.env.ref('spc_sav_aziza.avoir_mail_template')
        if echange:
            template = self.env.ref('spc_sav_aziza.echange_mail_template')
        template.send_mail(self.id, force_send=True)

    def _sent_sms_to_rz_rm(self,avoir,echange):
        destinations = []
        msg = ""
        date = datetime.now()
        reference = '%s' % (self.name)
        ng_trend_obj = self.env['spc.sms.ng_trend'].sudo()
        if self.env["ir.config_parameter"].sudo().get_param('spc_sav_aziza.endpoint'):
            if avoir:
                msg = "Un avoir a été validé par le SAV au magasin %s pour la RC %s.\nPrière de l'émettre rapidement." % (self.magasin_id.name,self.name)
                destinations = [self.magasin_id.user_id.partner_id.phone,self.magasin_id.resp_zone_id.partner_id.phone]
            if echange:
                msg = 'Un échange a été validé par le SAV pour la RC %s.\nPrière le valider pour le client.' % (self.name)
                destinations = [self.magasin_id.user_id.partner_id.phone, self.magasin_id.resp_zone_id.partner_id.phone]
            sms = ng_trend_obj.generate_sms(message=msg, destinations=destinations, date=date, reference=reference)
            response = ng_trend_obj.send_message(sms)
            sleep(1)
            stat_res = ng_trend_obj.sms_status(sms)
            _logger.info("SMS State : %s" % (stat_res), exc_info=True)
            if response.status_code == 200:
                return True
            else:
                pass

    @api.multi
    def back_money(self):
        if (self.env.user.has_group('spc_sav_aziza.group_responsable_sav')):
            for record in self:
                record.filtered(lambda s: s.state == 'repair').write({'state': 'back','is_back': True})
            self.send_mail_avoir_or_echange(True,False)
            print("back_money")
            self._sent_sms_to_rz_rm(True,False)
        else:
            raise ValidationError("Vous n'avez pas de l'autorisation pour valider avoir l'argent")
               
    @api.multi
    def exchange_product(self): 
        if (self.env.user.has_group('spc_sav_aziza.group_responsable_sav')):
            for record in self:
                record.filtered(lambda s: s.state == 'repair').write({'state': 'exchanged','is_exchanged': True})
            self.send_mail_avoir_or_echange(False,True)
            self._sent_sms_to_rz_rm(False,True)
        else:
            raise ValidationError("Vous n'avez pas de l'autorisation pour valider l'échange du produit")
    
    @api.multi
    def close_cycle(self): 
        for record in self:
            #Avoir
            if self.env.user.has_group('spc_sav_aziza.group_reglement_financier'):
                if record.type in ['exchanged']:
                    raise ValidationError("Vous n'avez pas de l'autorisation pour cloturer la réclamation")
                if record.type =='reclamation_client':
                    if record.state in ['back']:
                        if record.is_receive:
                            record.write({'state':'done4'})
                        else:
                            raise ValidationError(_('La clôture de la réclamation ne fait que l article est réceptionné par client'))
                else: #'reclamation_interne'
                    if record.state in ['back']:
                        record.write({'state':'done3'})
            #Echange
            elif self.env.user.has_group('spc_sav_aziza.group_responsable_sav'):
                if record.type in ['back']:
                    raise ValidationError("Vous n'avez pas de l'autorisation pour cloturer la réclamation")
                if record.type =='reclamation_client':
                    if record.state in ['exchanged']:
                        if record.is_receive:
                            record.write({'state':'done4'})
                        else:
                            raise ValidationError(_('La clôture de la réclamation ne fait que l article est réceptionné par client'))
                else: #'reclamation_interne'
                    if record.state in ['exchanged']:
                        record.write({'state':'done3'})
            else:
                raise ValidationError("Vous n'avez pas de l'autorisation pour cloturer la réclamation")
        return

    @api.multi
    def back_stock_sav(self):
        for record in self:
            record.write({'state':'done4','is_back_stock_sav':True})

    @api.multi
    def check_date_current_claim(self):
        
        claims = self.env['oscar.sav.claim'].search([('state','=','new')])  
        for claim in claims:
            now_date = datetime.strptime(str(datetime.now().date()),"%Y-%m-%d") 
            claim_date = datetime.strptime(str(claim.date_claim),"%Y-%m-%d")   
            if ((now_date-claim_date).days > 3):
                claim.check_date = True
            else : 
                
                claim.check_date = False
    # endregion

    # region Constrains and Onchange
    
    @api.constrains('date_purchase', 'date_claim')
    def check_date_achat(self):
        for rec in self:
            if rec.type == 'reclamation_client':
                if rec.date_purchase > rec.date_claim:
                    raise ValidationError(_("La date d'achat ne doit pas dépasser la date de réclamation!"))

    
    @api.onchange('product_id','supplier_id','categ_id','domain_problem_ids')
    def _onchange_article(self):
        problems_list = []
        if self.product_id:
            self.barcode=self.product_id.barcode
            self.categ_id=self.product_id.categ_id
            # self.supplier_id=self.product_id.supplier_id
            for rec in self.env['oscar.sav.problem'].search([]):
                if self.categ_id in rec.categ_ids:
                    problems_list.append(rec.id)
            self.domain_problem_ids = problems_list

    # endregion

    # region CRUD (overrides)
    @api.model
    def create(self, vals):
        if vals.get('type') == 'reclamation_client':
            vals['name'] = self.env['ir.sequence'].next_by_code('oscar.sav.client.claim')
        elif vals.get('type') == 'reclamation_interne':
            vals['name'] = self.env['ir.sequence'].next_by_code('oscar.sav.internal.claim')
        claim = super(Claim, self).create(vals)
#         claim.add_follower()
        claim._sent_sms_create_to_customer(claim.customer_id)
        return claim

    @api.multi
    def write(self, values):
        state = values.get('state', False)
        if state == 'done3' and not self.is_back:
            self._sent_sms_to_customer(self.customer_id, self.product_id, self.magasin_id)
        result = super(Claim, self).write(values)
        return result
    # endregion

    # region Actions
    # endregion

    # region Model methods

    # endregion


class Problem(models.Model):
    _name = 'oscar.sav.problem'
    _description = 'Problème'
        
    name = fields.Char(string="Libellé", required=True)
    categ_sav = fields.Char(string='Catégorie SAV')
    categ_ids = fields.Many2many('product.category', string='Catégories')
    code_problem = fields.Char(string="Code Problem")