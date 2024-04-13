# -*- coding: utf-8 -*-

import xlrd
import base64
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


TYPE_FILE_SELECTION = [
    ('renewal', "Renouvellement"),
    ('evaluation', "Evaluation")]

class RejetWizard(models.TransientModel):
    _name = 'import.excel.wizard'
    _description = 'Import excel Wizard'
    
    
    attachment = fields.Binary(string='Fichier')
    attachment_name = fields.Char("File name")
    type_file = fields.Selection(TYPE_FILE_SELECTION, string='Type file', readonly=True)
    type = fields.Selection([('magasin', "Magasin"), ('siege', "Siége")], string="Type", required=True)


    def read_file(self, data):
        data = self.attachment
        file_data = base64.b64decode(data)
        workbook = xlrd.open_workbook(file_contents=file_data)
        return workbook
    
    def import_contract_renewal(self, data):
        workbook = self.read_file(data)
        sheets_name = workbook.sheet_names()
        message = _("Veuillez vérifier le modèle de fichier importé!")
        try:
            for names in sheets_name:
                worksheet = workbook.sheet_by_name(names)
    #             num_cells = worksheet.ncols
                num_rows = worksheet.nrows
                for curr_row in range(1, num_rows):
                    # Matricule
                    value = worksheet.cell_value(curr_row, 0)
                    name = str(value)
                    employee = self.env['hr.employee'].search([('code_rh','=',name)], limit=1)
                    if not employee:
                        message = _("Le code d'employé %s n'existe pas! Veuillez l'ajouter à la liste d'employés "%(name))
                    # Emploi occupé
                    value = worksheet.cell_value(curr_row, 1)
                    job = self.env['hr.job'].search([('name','=', value)])
                    # Nature du contrat
                    value = worksheet.cell_value(curr_row, 2)
                    contract_type = self.env['hr.contract.type'].search([('name','=', value)])
                    # Date d'embauche société
                    value = worksheet.cell_value(curr_row, 3)
                    date_embauche = datetime(*xlrd.xldate_as_tuple(value, workbook.datemode))
                    # Date de début de contrat
                    value = worksheet.cell_value(curr_row, 4)
                    date_start = datetime(*xlrd.xldate_as_tuple(value, workbook.datemode))
                    # Date de fin de contrat
                    value = worksheet.cell_value(curr_row, 5)
                    date_end = datetime(*xlrd.xldate_as_tuple(value, workbook.datemode))
                    # Direction
                    value = worksheet.cell_value(curr_row, 6)
                    department = self.env['hr.department'].search([('name','=', value)])
                    # Code Magasin
                    value = worksheet.cell_value(curr_row, 7)
                    code = str(int(value))
                    magasin = self.env['oscar.site'].search([('code','=', code)], limit=1)
                    # Manager Direct
                    value = worksheet.cell_value(curr_row, 8)
                    matricule = str(value)
                    manager = self.env['hr.employee'].search([('code_rh','=',matricule)], limit=1)
                    # SOLDE DE CONGE
                    value = worksheet.cell_value(curr_row, 9)
                    solde_conge = value

                    vals = {
                        'name': name,
                        'date': datetime.today(),
                        'employee_id': employee.id,
                        'job_id': job.id,
                        'type_current_id': contract_type.id,
                        'date_embauche': date_embauche,
                        'date_start': date_start,
                        'date_end': date_end,
                        'department_id': department.id,
                        'magasin_id': magasin.id,
                        'manager_id': manager.id,
                        'remaining_leaves': solde_conge,
                        'type': self.type
                        }
                    self.env['oscar.contract.renewal'].create(vals)
        except Exception:
            raise ValidationError(message)
        return True
    
    def import_evaluation(self, data):
        workbook = self.read_file(data)
        sheets_name = workbook.sheet_names()
        try:
            for names in sheets_name:
                worksheet = workbook.sheet_by_name(names)
    #             num_cells = worksheet.ncols
                num_rows = worksheet.nrows
    
                for curr_row in range(1, num_rows):
                    # Matricule
                    value = worksheet.cell_value(curr_row, 0)
                    name = str(value)
                    employee = self.env['hr.employee'].search([('code_rh','=',name)], limit=1)
                    if not employee:
                        raise ValidationError(_("Le code d'employé %s n'existe pas! Veuillez l'ajouter à la liste d'employés "%(name)))
                    # Emploi occupé
                    value = worksheet.cell_value(curr_row, 1)
                    job = self.env['hr.job'].search([('name','=', value)])
                    # Nature du contrat
                    value = worksheet.cell_value(curr_row, 2)
                    contract_type = self.env['hr.contract.type'].search([('name','=', value)])
                    # Date d'embauche société
                    value = worksheet.cell_value(curr_row, 3)
                    date_embauche = datetime(*xlrd.xldate_as_tuple(value, workbook.datemode))
                    # Date de début de contrat
                    value = worksheet.cell_value(curr_row, 4)
                    date_start = datetime(*xlrd.xldate_as_tuple(value, workbook.datemode))
                    # Date de fin de la période d'essai
                    value = worksheet.cell_value(curr_row, 5)
                    trial_date_end = datetime(*xlrd.xldate_as_tuple(value, workbook.datemode))
                    # Direction
                    value = worksheet.cell_value(curr_row, 6)
                    department = self.env['hr.department'].search([('name','=', value)])
                    # Code Magasin
                    value = worksheet.cell_value(curr_row, 7)
                    code = str(int(value))
                    magasin = self.env['oscar.site'].search([('code','=', code)], limit=1)
                    # Manager Direct
                    value = worksheet.cell_value(curr_row, 8)
                    matricule = str(value)
                    manager = self.env['hr.employee'].search([('code_rh','=',matricule)], limit=1)
                    # SOLDE DE CONGE
                    value = worksheet.cell_value(curr_row, 9)
                    solde_conge = value
                    
                    vals = {
                        'name': name,
                        'date': datetime.today(),
                        'employee_id': employee.id,
                        'job_id': job.id,
                        'type_current_id': contract_type.id,
                        'date_embauche': date_embauche,
                        'date_start': date_start,
                        'trial_date_end': trial_date_end,
                        'department_id': department.id,
                        'magasin_id': magasin.id,
                        'manager_id': manager.id,
                        'remaining_leaves': solde_conge
                        }
                    
                    self.env['oscar.contract.evaluation'].create(vals)
        except Exception:
            raise ValidationError(_("Veuillez vérifier le modèle de fichier importé!"))
        return True
    
    def action_import(self):
        data = self.attachment
        type_file = self.type_file
        if type_file == 'renewal':
            if self.import_contract_renewal(data):
                message = _("Votre fichier a bien été importé")  
        elif type_file == 'evaluation':
            if self.import_evaluation(data):
                message = _("Votre fichier a bien été importé")  
        
        if message:
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': message,
                    'type': 'rainbow_man',
                }
            }
        
        
    