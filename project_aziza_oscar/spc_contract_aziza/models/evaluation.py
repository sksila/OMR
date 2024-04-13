# -*- coding: utf-8 -*-

'''
@author: Mohamed Sghaier
'''

from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from datetime import datetime, timedelta
import logging

class Evaluation(models.Model):
    _name = 'oscar.contract.evaluation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Evaluation'
    
    
    name = fields.Char(string="Matricule")
    date = fields.Date("Date", default=fields.Date.today)
    magasin_id = fields.Many2one('oscar.site', string='Magasin', index=True)
    # Identification de l'employé
    
    employee_id = fields.Many2one("hr.employee", string="Employé", help="ID utilisé pour l'identification des employés.", required=True, index=True)
    job_id = fields.Many2one('hr.job', string='Poste')
    department_id = fields.Many2one('hr.department', string="Direction", required=True)
    manager_id = fields.Many2one('hr.employee', string="Manager Direct", index=True, required=True)
    date_embauche = fields.Date("Date d'embauche",readonly=True, store=True)
    date_start = fields.Date("Date de début contrat")
    trial_date_end = fields.Date("Date de fin de la période d'essai")
    remaining_leaves = fields.Float("Solde de congé",readonly=True, store=True)
    type_current_id = fields.Many2one('hr.contract.type', string="Type de contrat en cours")
    trial_end=fields.Boolean("Mettre fin de l'evaluation")
    # Critères sommaires d'évaluation
    summary_criteria_ids = fields.One2many("oscar.contract.summary.evaluation.criteria", "evaluation_id", string="Critères d'évaluation")
    notes = fields.Text('Notes')
    
    # Points forts du collaborateur
    strong_points = fields.Text("Points forts du collaborateur")
    
    # Aspects à améliorer
    aspects_to_improve = fields.Text("Aspects à améliorer")
    
    # Recommandations
    recommendation_id = fields.Many2one('oscar.contract.evaluation.recommendation', string='Recommandation')
    
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
    ], string='Statut', track_visibility='onchange',default="new", readonly=True)

    type = fields.Selection([('magasin', "Magasin"), ('siege', "Siége")], string="Type")


    @api.model
    def create(self,vals):
        list = []
        res=super(Evaluation,self).create(vals)
        for rec in self.env['oscar.contract.evaluation.criteria'].search([]):
            dict_of_values = (0, 0, {'criteria_id': rec.id})
            list.append(dict_of_values)
        res.summary_criteria_ids=list
        return res
    
    @api.multi
    @api.depends('code_magasin')
    def _compute_magasin_id(self):
        for record in self:
            if record.code_magasin:
                record.magasin_id = self.env['oscar.site'].search([('code', '=', record.code_magasin)], limit=1).id
    
    @api.multi
    @api.depends('name')
    def _compute_employee_id(self):
        for record in self:
            if record.name:
                record.employee_id = self.env['hr.employee'].search([('name', '=', record.name)], limit=1).id
    
    def _check_groups(self, user):
        if self.type == 'magasin':
            if self.state == 'new' and not (user.has_group('spc_oscar_aziza.group_reponsable_zone') or user.has_group('spc_oscar_aziza.group_drh')):
                raise ValidationError(_("Vous n'avez pas le droit pour modifier l'evaluation!"))
            elif self.state == 'validate_md' and not (user.has_group('spc_oscar_aziza.group_DRE') or user.has_group('spc_oscar_aziza.group_drh')):
                raise ValidationError(_("Vous n'avez pas le droit pour modifier l'evaluation!"))
            elif self.state == 'validate_dre' and not (user.has_group('spc_oscar_aziza.group_dhrbp') or user.has_group('spc_oscar_aziza.group_drh')):
                raise ValidationError(_("Vous n'avez pas le droit pour modifier l'evaluation!"))
            elif self.state == 'validate_dhrbp' and not (user.has_group('spc_oscar_aziza.group_DE') or user.has_group('spc_oscar_aziza.group_drh')):
                raise ValidationError(_("Vous n'avez pas le droit pour modifier l'evaluation!"))
            elif self.state == 'validate_de' and not (user.has_group('spc_oscar_aziza.group_dg') or user.has_group('spc_oscar_aziza.group_drh')):
                raise ValidationError(_("Vous n'avez pas le droit pour modifier l'evaluation!"))
        else: #siege
            if self.state == 'new' and not self.env['hr.employee'].search([('user_id', '=', self.env.uid)],limit=1).id in self.department_id.manager_ids.ids:
                raise ValidationError(_("Vous n'avez pas le droit pour modifier la décision de renouvellement de contrat!"))
            if self.state == 'validate_sub_dir_concernee' and not self.env['hr.employee'].search([('user_id', '=', self.env.uid)],limit=1).id in self.department_id.parent_id.manager_ids.ids:
                raise ValidationError(_("Vous n'avez pas le droit pour modifier la décision de renouvellement de contrat!"))
            elif self.state == 'validate_dir_concernee' and not self.env.user.has_group('spc_oscar_aziza.group_drh'):
                raise ValidationError(_("Vous n'avez pas le droit pour modifier la décision de renouvellement de contrat!"))
            elif self.state == 'validate_drh' and not self.env.user.has_group('spc_oscar_aziza.group_dg'):
                raise ValidationError(_("Vous n'avez pas le droit pour modifier la décision de renouvellement de contrat!"))
    
    @api.multi
    def write(self, values):
        
        self._check_groups(self.env.user)
        res=super(Evaluation,self).write(values)
        return res
    
    def get_list_partners(self,group):
        list = []
        for rec in self.env['res.users'].search([]):
            if rec.has_group(group):
                list.append(rec.partner_id.id)
        return list     
    
    @api.multi
    def validate_evaluation(self):
        list = []
        for record in self:
            if record.type == 'magasin':
                if record.state == 'new' and (self.env.user.has_group('spc_oscar_aziza.group_reponsable_zone') or self.env.user.has_group('spc_oscar_aziza.group_drh')):
                    record.write({'state':'validate_md', 'date_md':datetime.today()})
                    list = self.get_list_partners('spc_oscar_aziza.group_DRE')
                    self.message_post(subject = "Validation de l'évaluation", body = "L'évaluation a été validée par le Manager Direct ", partner_ids=list)
                elif record.state == 'validate_md' and (self.env.user.has_group('spc_oscar_aziza.group_DRE') or self.env.user.has_group('spc_oscar_aziza.group_drh')):
                    record.write({'state':'validate_dre', 'date_dre':datetime.today()})
                    list = self.get_list_partners('spg_oscar_aziza.group_dhrbp')
                    self.message_post(subject = "Validation de l'évaluation", body = "L'évaluation a été validée par le DRE", partner_ids=list)
                elif record.state == 'validate_dre' and (self.env.user.has_group('spc_oscar_aziza.group_dhrbp') or self.env.user.has_group('spc_oscar_aziza.group_drh')):
                    record.write({'state':'validate_dhrbp', 'date_dhrbp':datetime.today()})
                    list = self.get_list_partners('spc_oscar_aziza.group_DE')
                    self.message_post(subject= "Validation de l'évaluation", body = "L'évaluation a été validée par le par DHRBP", partner_ids=list)
                elif record.state == 'validate_dhrbp' and (self.env.user.has_group('spc_oscar_aziza.group_DE') or self.env.user.has_group('spc_oscar_aziza.group_drh')):
                    record.write({'state':'validate_de', 'date_de':datetime.today()})
                    list = self.get_list_partners('spc_oscar_aziza.group_dg')
                    self.message_post(subject = "Validation de l'évaluation", body = "L'évaluation a été validée par le Directeur Exploitation", partner_ids=list)
                elif record.state == 'validate_de' and (self.env.user.has_group('spc_oscar_aziza.group_dg') or self.env.user.has_group('spc_oscar_aziza.group_drh')):
                    record.write({'state':'validate_dg', 'date_dg':datetime.today()})
                    list = self.get_list_partners('spc_oscar_aziza.group_drh')
                    self.message_post(subject = "Validation de l'évaluation", body = "L'évaluation a été validée par le Directeur Générale", partner_ids=list)
                else:
                    raise ValidationError(_("Vous n'avez pas le droit pour valider l'évaluation!"))
            else: #siege
                if record.state == 'new' and self.env['hr.employee'].search([('user_id','=',self.env.uid)], limit=1).id in record.department_id.manager_ids.ids:
                    if not record.department_id.parent_id:
                        record.write({'state': 'validate_dir_concernee', 'date_dir_concernee': datetime.today()})
                    if record.department_id.parent_id:
                        record.write({'state': 'validate_sub_dir_concernee', 'date_sub_dir_concernee': datetime.today()})
                elif record.state == 'validate_sub_dir_concernee' and self.env['hr.employee'].search([('user_id','=',self.env.uid)], limit=1).id in record.department_id.parent_id.manager_ids.ids:
                    record.write({'state':'validate_dir_concernee', 'date_dir_concernee':datetime.today()})
                elif record.state == 'validate_dir_concernee' and self.env.user.has_group('spc_oscar_aziza.group_drh'):
                    record.write({'state':'validate_drh', 'date_drh':datetime.today()})
                elif record.state == 'validate_drh' and self.env.user.has_group('spc_oscar_aziza.group_dg'):
                    record.write({'state': 'validate_dg', 'date_dg': datetime.today()})
                else:
                    raise ValidationError(_("Vous n'avez pas le droit pour valider l'évaluation!"))
        return


class SummaryEvaluationCriteria(models.Model):
     
    _name = 'oscar.contract.summary.evaluation.criteria'
    _description = 'Criteres sommaires evaluation'
    _rec_name = 'criteria_id'
    
    criteria_id = fields.Many2one("oscar.contract.evaluation.criteria", string="Critère", required=True)
    evaluation = fields.Selection([
        ('0','Non satisfaisant'),
        ('1', 'Pas satisfaisant'),
        ('2', 'À améliorer'),
        ('3', 'Satisfaisant'),
        ('4', 'Trés satisfaisant'),
    ], string='Evaluation', default='1')
    comment = fields.Text("commentaires")
    evaluation_id = fields.Many2one('oscar.contract.evaluation', string='Evaluation', index=True)

class EvaluationCriteria(models.Model):
     
    _name = 'oscar.contract.evaluation.criteria'
    _description = 'Criteres evaluation'
    
    name = fields.Char("Intitulé", required=True)
    description = fields.Text('Description')

class EvaluationRecommendation(models.Model):
     
    _name = 'oscar.contract.evaluation.recommendation'
    _description = 'Recommandation'
    
    name = fields.Char("Intitulé", required=True)
    description = fields.Text('Description')
    

    