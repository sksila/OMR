# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
from odoo.tools.translate import _

class Dispatching(models.Model):
    _name = 'oscar.dispatching'
    _description = 'Dispatching'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'controller_id'
    
    
    controller_id = fields.Many2one('res.users', string='Vérificateur', required="True", domain=lambda self: [('groups_id', 'in', [self.env.ref('spc_recette_aziza.group_agent_validation_oscar').id])], track_visibility='onchange')
    controller_tr_id = fields.Many2one('res.users', string='Vérificateur TR', required="True", domain=lambda self: [('groups_id', 'in', [self.env.ref('spc_recette_aziza.group_agent_validation_ticket_resto_oscar').id])], track_visibility='onchange')
    magasin_id = fields.Many2one('oscar.site', string='Magasin', domain=[('site_type', '=', 'MAGASIN')], required="True")
    start_date = fields.Date('Date de début', required="True")
    end_date = fields.Date('Date de fin', required="True")
    comment = fields.Text(string="Notes internes")
    
    @api.onchange('magasin_id')
    def onchange_start_end_date(self):
        if self.magasin_id:
            exist = self.search([('magasin_id', '=', self.magasin_id.id)], order="end_date desc", limit=1)
            if exist:
                self.start_date = exist.end_date + timedelta(days=1)
                if self.start_date:
                    self.end_date = self.start_date + timedelta(days=1)
            else: 
                self.start_date = datetime.today().date()
                self.end_date = None

    @api.model
    def create(self, values):
        start_date = values.get('start_date', False)
        end_date = values.get('end_date', False)
        magasin_id = values.get('magasin_id', False)
        controller_id = values.get('controller_id', False)
        controller_tr_id = values.get('controller_tr_id', False)
        if start_date and end_date and magasin_id:
            journees = self.env['oscar.journee.recue'].search([('magasin_id', '=', magasin_id),('state', 'not in', ['accepted','waiting1','waiting2','checked'])])
            for journee in journees:
                journee.write({'controller_id': controller_id, 'controller_tr_id': controller_tr_id,
                               'state':'waiting'})
        dispatching = super(Dispatching, self).create(values)
        return dispatching
    
    @api.multi
    def write(self, values):
        for dispatch in self:
            start_date = values.get('start_date', dispatch.start_date)
            end_date = values.get('end_date', dispatch.end_date)
            magasin_id = values.get('magasin_id', dispatch.magasin_id.id)
            controller_id = values.get('controller_id', dispatch.controller_id.id)
            controller_tr_id = values.get('controller_tr_id', dispatch.controller_tr_id.id)

            journees = self.env['oscar.journee.recue'].search([('magasin_id', '=', magasin_id),('state', 'not in', ['accepted','accepted1','waiting1','waiting2','checked']),('date_journee', '>=', start_date),('date_journee', '<=', end_date)])
            for journee in journees:
                journee.write({'controller_id': controller_id, 'controller_tr_id': controller_tr_id,
                               'state':'waiting'})
        dispatching = super(Dispatching, self).write(values)
        return dispatching
    
    @api.constrains('start_date', 'end_date')
    def _check_date(self):
        for dispatch in self:
            domain = [
                ('start_date', '<=', dispatch.end_date),
                ('end_date', '>=', dispatch.start_date),
                ('magasin_id', '=', dispatch.magasin_id.id),
                ('id', '!=', dispatch.id),
            ]
            count_dispatchs = self.search_count(domain)
            if count_dispatchs:
                raise ValidationError(_('Veuillez vérifier la date de début et la date de fin de votre dispatch!'))
            if dispatch.start_date >= dispatch.end_date:
                raise ValidationError(_('La date de début doit être antérieure à la date de fin!'))
