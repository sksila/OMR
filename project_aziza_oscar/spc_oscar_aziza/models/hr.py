# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Job(models.Model):
    _inherit = 'hr.job'

    #Caissier
    est_caissier = fields.Boolean('Est caissier')
    code_job = fields.Char('Code de poste')

class Employee(models.Model):
    _inherit = 'hr.employee'
    
    
    last_name = fields.Char("Nom d'employé")
    first_name = fields.Char('Prénom')
    code = fields.Char('Code Caisse')
    code_rh = fields.Char('Matricule RH')
    code_employee = fields.Char(string="Code Employé")
    magasin_id = fields.Many2one('oscar.site', string='Magasin', track_visibility='onchange', domain=[('site_type', '=', 'MAGASIN')])
    #Caissier
    est_caissier = fields.Boolean('Est caissier', related='job_id.est_caissier', store=True, invisible=True)
    
    
    @api.onchange('user_id')
    def _onchange_user(self):
        self.work_email = self.user_id.email
        self.image = self.user_id.image
    
    @api.model
    def create(self, vals):
        if vals.get('last_name') and vals.get('first_name'):
            vals['name'] = "[%s] %s %s"%(vals['code_rh'],vals['first_name'],vals['last_name'])
        employee = super(Employee, self).create(vals)
        return employee
