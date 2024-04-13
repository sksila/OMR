# -*- coding: utf-8 -*-
'''
@author: Mohamed Sghaier
'''


from odoo import api, fields, models, _


class Employee(models.Model):

    _inherit = "hr.employee"
    
    evaluation_ids = fields.One2many('oscar.contract.evaluation', 'employee_id', string='Contracts',readonly=True)
    evaluation_id = fields.Many2one('oscar.contract.evaluation', compute='_compute_evaluation_id', string="Evaluation en cours", help="Derniï¿½re ï¿½valuation de l'employï¿½",readonly=True)
    evaluations_count = fields.Integer(compute='_compute_evaluations_count', string='Evaluations',readonly=True)
    
    
    def _compute_evaluation_id(self):
        """ get the lastest evaluation """
        Contract = self.env['oscar.contract.evaluation']
        for employee in self:
            employee.contract_id = Contract.search([('employee_id', '=', employee.id)], order='date desc', limit=1)

    def _compute_evaluations_count(self):
        # read_group as sudo, since evaluation count is displayed on form view
        evaluation_data = self.env['oscar.contract.evaluation'].sudo().read_group([('employee_id', 'in', self.ids)], ['employee_id'], ['employee_id'])
        result = dict((data['employee_id'][0], data['employee_id_count']) for data in evaluation_data)
        for employee in self:
            employee.evaluations_count = result.get(employee.id, 0)

class Department(models.Model):

    _inherit = "hr.department"

    # type = fields.Selection([('magasin', "Magasin"), ('siege', "Siége")], string="Type", default="magasin")
    manager_ids = fields.Many2many('hr.employee',string="Gestionnaires")