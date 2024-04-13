# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class InterEmployee(models.Model):
    _name = 'oscar.inter.employee'
    _description = 'Employee (Interface)'
    _rec_name = 'matricule'
    
    matricule = fields.Char('Matricule RH', required=False)
    matricule_caisse = fields.Char('Matricule Caisse', required=True)
    nom = fields.Char('Nom', required=True)
    prenom = fields.Char('Prénom', required=False)
    email = fields.Char('Email')
    cin = fields.Char('CIN')
    date_naissance = fields.Date("Date de naissance")
    unite = fields.Char('Unite')
    service = fields.Char('Service')
    fonction = fields.Char('Fonction')
    date_start = fields.Date("Date de début contrat")
    date_end = fields.Date("Date de fin contrat")
    date_embauche = fields.Date("Date d'embauche")
    date_depart = fields.Date("Date de départ")
    solde_conge = fields.Float("Solde de congé")
    actif = fields.Boolean("Activé", default=True)
    

    
    def planned_gold_integration_employee(self):
        _logger.info("______________________GOLD integration Employee__________________________", exc_info=True)
        emp_inter = self.env['oscar.inter.employee'].search([])
        i = 0
        for emp in emp_inter:
            emp_oscar = self.env['hr.employee'].search([('code', '=', emp.matricule_caisse)], limit=1)
            vals = {
                    'name': "[%s] %s"%(emp.matricule_caisse,emp.nom),
                    'last_name': emp.nom,
                    'first_name': emp.prenom,
                    'code': emp.matricule_caisse,
                    'code_rh': emp.matricule_caisse,
                }
            if emp_oscar:
                _logger.info("Write Employee : %s"%(emp.matricule_caisse), exc_info=True)
                emp_oscar.write(vals)
            else:
                i += 1
                _logger.info("Create Employee : %s"%(emp.matricule_caisse), exc_info=True)
                emp_created = self.env['hr.employee'].create(vals)
        _logger.info("---> %s <--- Employee Created "%(i), exc_info=True)
        return True