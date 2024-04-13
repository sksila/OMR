# -*- coding: utf-8 -*-

'''
@author: Mohamed Sghaier
'''

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import logging


class ContractRenewal(models.Model):
    
    _name = 'oscar.contract.renewal'
    _description = 'Renouvellement de contrat'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    
    name = fields.Char(string="Matricule")
    date = fields.Date("Date", default=fields.Date.today)
    magasin_id = fields.Many2one('oscar.site', string='Magasin', index=True, required=True)
    # Identification de l'employé
    
    employee_id = fields.Many2one("hr.employee", string="Employé", help="ID utilisé pour l'identification des employés.", required=True, index=True)
    job_id = fields.Many2one('hr.job', string='Poste')
    department_id = fields.Many2one('hr.department', string="Direction", required=True)
    manager_id = fields.Many2one('hr.employee', string="Manager Direct", required=True)
    date_embauche = fields.Date("Date d'embauche")
    date_start = fields.Date("Date de début contrat")
    date_end = fields.Date("Date de fin contrat")
    remaining_leaves = fields.Float("Solde de congé")
    
    # Décision
    
    type_current_id = fields.Many2one('hr.contract.type', string="Type de contrat en cours")
    type_id = fields.Many2one('hr.contract.type', string="Type de contrat", track_visibility='onchange')
    number_months = fields.Integer("Nombre de mois", track_visibility='onchange')
    end_contract = fields.Boolean("Mettre fin à la relation contractuelle", track_visibility='onchange')
    is_expired = fields.Boolean("Expiré")
    
    notes = fields.Text('Notes')
    
    date_md =fields.Datetime("Date de validation MD")
    date_dre =fields.Datetime("Date de validation DRE")
    date_dhrbp =fields.Datetime("Date de validation D. HRBP")
    date_de =fields.Datetime("Date de validation DE")
    date_dg =fields.Datetime("Date de validation DG")
    date_drh = fields.Datetime("Date de validation DRH")
    date_dir_concernee = fields.Datetime("Date de validation D.concernée")
    date_sub_dir_concernee = fields.Datetime("Date de validation sous D.concernée")
    
    state = fields.Selection([
        ('new', 'Nouvelle'),
        ('validate_sub_dir_concernee', 'Validée par sous D.concernée'),
        ('validate_md', 'Validée par MD'),
        ('validate_dre', 'Validée par DRE'),
        ('validate_dhrbp', 'Validée par D. HRBP'),
        ('validate_de', 'Validée par DE'),
        ('validate_dir_concernee', 'Validée par D.concernée'),
        ('validate_drh', 'Validée par DRH'),
        ('validate_dg', 'Validée par DG'),
    ], string='Statut', track_visibility='onchange', default="new", readonly=True)

    type = fields.Selection([('magasin', "Magasin"), ('siege', "Siége")], string="Type")

    @api.onchange('end_contract')
    def _onchange_end_contract(self):
        if self.end_contract:
            self.type_id = ""
            self.number_months = 0
    

    def get_list_partners(self,group):
        list = []
        for rec in self.env['res.users'].search([]):
            if rec.has_group(group):
                list.append(rec.partner_id.id)
        return list
    
    @api.multi
    def add_follower(self, partner):
        subtypes = self.env['mail.message.subtype'].search([])
        if partner:
            self.message_subscribe(partner_ids=partner.ids, subtype_ids= subtypes.ids)
    
    @api.multi
    def validate_contract_renewal(self):
        list = []
        for record in self:
            if record.type == 'magasin':
                if record.state == 'new' and (self.env.user.has_group('spc_oscar_aziza.group_reponsable_zone') or self.env.user.has_group('spc_oscar_aziza.group_drh')):
                    record.write({'state':'validate_md', 'date_md':datetime.today()})
                    list = self.get_list_partners('spc_oscar_aziza.group_DRE')
                    self.message_post(subject = "Validation de renouvellement de contrat", body = "Le renouvellement de contrat a été validé par le Manager Direct", partner_ids=list)
                elif record.state == 'validate_md' and (self.env.user.has_group('spc_oscar_aziza.group_DRE') or self.env.user.has_group('spc_oscar_aziza.group_drh')):
                    record.write({'state':'validate_dre', 'date_dre':datetime.today()})
                    list = self.get_list_partners('spc_oscar_aziza.group_dhrbp')
                    self.message_post(subject = "Validation de renouvellement de contrat", body = "Le renouvellement de contrat a été validé par le DRE", partner_ids=list)
                elif record.state == 'validate_dre' and (self.env.user.has_group('spc_oscar_aziza.group_dhrbp') or self.env.user.has_group('spc_oscar_aziza.group_drh')):
                    record.write({'state':'validate_dhrbp', 'date_dhrbp':datetime.today()})
                    list = self.get_list_partners('spc_oscar_aziza.group_DE')
                    self.message_post(subject= "Validation de renouvellement de contrat", body = "Le renouvellement de contrat a été validé par le DHRBP", partner_ids=list)
                elif record.state == 'validate_dhrbp' and (self.env.user.has_group('spc_oscar_aziza.group_DE') or self.env.user.has_group('spc_oscar_aziza.group_drh')):
                    record.write({'state':'validate_de', 'date_de':datetime.today()})
                    list = self.get_list_partners('spc_oscar_aziza.group_dg')
                    self.message_post(subject = "Validation de renouvellement de contrat", body = "Le renouvellement de contrat a été validé par le Directeur d'exploitation", partner_ids=list)
                elif record.state == 'validate_de' and (self.env.user.has_group('spc_oscar_aziza.group_dg') or self.env.user.has_group('spc_oscar_aziza.group_drh')):
                    record.write({'state':'validate_dg', 'date_dg':datetime.today()})
                    list = self.get_list_partners('spc_oscar_aziza.group_drh')
                    self.message_post(subject = "Validation de renouvellement de contrat", body = "Le renouvellement de contrat a été validé par le Directeur Générale", partner_ids=list)
                else:
                    raise ValidationError(_("Vous n'avez pas le droit pour valider le renouvellement!"))
            else: #siege
                if record.state == 'new' and self.env['hr.employee'].search([('user_id','=',self.env.uid)], limit=1).id in record.department_id.manager_ids.ids:
                    if not record.department_id.parent_id:
                        record.write({'state':'validate_dir_concernee', 'date_dir_concernee':datetime.today()})
                    if record.department_id.parent_id:
                        record.write({'state': 'validate_sub_dir_concernee', 'date_sub_dir_concernee': datetime.today()})
                elif record.state == 'validate_sub_dir_concernee' and self.env['hr.employee'].search([('user_id','=',self.env.uid)], limit=1).id in record.department_id.parent_id.manager_ids.ids:
                    record.write({'state':'validate_dir_concernee', 'date_dir_concernee':datetime.today()})
                elif record.state == 'validate_dir_concernee' and self.env.user.has_group('spc_oscar_aziza.group_drh'):
                    record.write({'state':'validate_drh', 'date_drh':datetime.today()})
                elif record.state == 'validate_drh' and self.env.user.has_group('spc_oscar_aziza.group_dg'):
                    record.write({'state': 'validate_dg', 'date_dg': datetime.today()})
                else:
                    raise ValidationError(_("Vous n'avez pas le droit pour valider le renouvellement!"))
            record.add_follower(self.env.user)
        return

    def get_users_from_groups(self,list_groups):
        list=[]
        list_users=[]
        for group in list_groups :
            list=self.get_list_partners(group)
            for element in list:
                list_users.append(element)
            list=[]
        return list_users
    
    def _check_groups(self, user):
        if self.type == 'magasin':
            if self.state == 'new' and not (user.has_group('spc_oscar_aziza.group_reponsable_zone') or user.has_group('spc_oscar_aziza.group_drh')):
                raise ValidationError(_("Vous n'avez pas le droit pour modifier la décision de renouvellement de contrat!"))
            elif self.state == 'validate_md' and not (user.has_group('spc_oscar_aziza.group_DRE') or user.has_group('spc_oscar_aziza.group_drh')):
                raise ValidationError(_("Vous n'avez pas le droit pour modifier la décision de renouvellement de contrat!"))
            elif self.state == 'validate_dre' and not (user.has_group('spc_oscar_aziza.group_dhrbp') or user.has_group('spc_oscar_aziza.group_drh')):
                raise ValidationError(_("Vous n'avez pas le droit pour modifier la décision de renouvellement de contrat!"))
            elif self.state == 'validate_dhrbp' and not (user.has_group('spc_oscar_aziza.group_DE') or user.has_group('spc_oscar_aziza.group_drh')):
                raise ValidationError(_("Vous n'avez pas le droit pour modifier la décision de renouvellement de contrat!"))
            elif self.state == 'validate_de' and not (user.has_group('spc_oscar_aziza.group_dg') or user.has_group('spc_oscar_aziza.group_drh')):
                raise ValidationError(_("Vous n'avez pas le droit pour modifier la décision de renouvellement de contrat!"))
        else: #siege
            if self.state == 'new' and not self.env['hr.employee'].search([('user_id', '=', self.env.uid)],limit=1).id in self.department_id.manager_ids.ids:
                raise ValidationError(_("Vous n'avez pas le droit pour modifier la décision de renouvellement de contrat!"))
            if self.state == 'validate_sub_dir_concernee' and not self.env['hr.employee'].search([('user_id', '=', self.env.uid)],limit=1).id in self.department_id.parent_id.manager_ids.ids:
                raise ValidationError(_("Vous n'avez pas le droit pour modifier la décision de renouvellement de contrat!"))
            elif self.state == 'validate_dir_concernee' and not self.env.user.has_group('spc_oscar_aziza.group_drh'):
                raise ValidationError(_("Vous n'avez pas le droit pour modifier la décision de renouvellement de contrat!"))
            elif self.state == 'validate_drh' and not self.env.user.has_group('spc_oscar_aziza.group_dg'):
                raise ValidationError(_("Vous n'avez pas le droit pour modifier la décision de renouvellement de contrat!"))


    
    @api.model
    def create(self, values):
        contract = super(ContractRenewal, self).create(values)
        contract.add_follower(self.env.user)
        return contract
    
    @api.multi
    def write(self, values):
        self._check_groups(self.env.user)
        res=super(ContractRenewal,self).write(values)
        return res

    @api.multi
    def set_expired_contract(self):
        contracts=self.env['oscar.contract.renewal'].sudo().search([('date_end','!=', False)])
        for contract in contracts:
            date_now = datetime.strptime(str(datetime.now().date()),"%Y-%m-%d") 
            date_end = datetime.strptime(str(contract.date_end),"%Y-%m-%d")   
            if ((date_end-date_now).days <= 15):
                contract.is_expired = True
            else : 
                contract.is_expired = False


