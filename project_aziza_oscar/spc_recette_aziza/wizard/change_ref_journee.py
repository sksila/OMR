# -*- coding: utf-8 -*-

from odoo import api, fields, models


#----------------------------------------------------------
# change references wizard
#----------------------------------------------------------

class ChangeRefWizard(models.TransientModel):
    _name = 'change.ref.wizard'
    _description = "Changer les refs de la journee"

    def _default_ref_ids(self):
        active_id = self._context.get('active_id')
        default_value = self._context.get('default_type')
        print(default_value)
        if default_value == 'mg':
            journee_id = self.env['oscar.journee'].browse(active_id)
            return [
            (0, 0, {'user_id': ref.user_id.id, 'journee_mg_id': ref.journee_ids.ids[0],'name': ref.name})
            for ref in journee_id.journee_ref_ids
            ]
        
        elif default_value == 'sg':
            journee_id = self.env['oscar.journee.recue'].browse(active_id)
            return [
            (0, 0, {'user_id': ref.user_id.id, 'journee_id': ref.journee_recue_ids.ids[0],'name': ref.name})
            for ref in journee_id.journee_ref_ids
            ]
    
    def _default_journee_id(self):
        active_id = self._context.get('active_id')
        default_value = self._context.get('default_type')
        print(default_value)
        if default_value == 'sg':
            return self.env['oscar.journee.recue'].browse(active_id)
            pass
    
    def _default_journee_mg_id(self):
        active_id = self._context.get('active_id')
        default_value = self._context.get('default_type')
        print(default_value)
        if default_value == 'mg':
            return self.env['oscar.journee'].browse(active_id)
    
    type = fields.Selection([
        ('mg', 'MG'),
        ('sg', 'SG'),
        ], string='Type')
    journee_id = fields.Many2one('oscar.journee.recue', string='Journée', ondelete='cascade', readonly=True, default=_default_journee_id)
    journee_mg_id = fields.Many2one('oscar.journee', string='Journée', ondelete='cascade', readonly=True, default=_default_journee_mg_id)
    ref_ids = fields.One2many('change.ref.journee', 'wizard_id', string='Réferences', default=_default_ref_ids)
    

    @api.multi
    def change_ref_button(self):
        self.ensure_one()
        self.ref_ids.change_ref_button(self.journee_id,self.journee_mg_id)
        if self.env.user in self.mapped('ref_ids.journee_id'):
            return {'type': 'ir.actions.client', 'tag': 'reload'}
        return {'type': 'ir.actions.act_window_close'}


class ChangeRefJournee(models.TransientModel):
    _name = 'change.ref.journee'
    _description = "Changer refs de la journee"
    
    name = fields.Selection([
        ('journee', 'Journée'),
        ('ticket', 'Ticket restaurant'),
        ], string='Journée/Ticket restaurant', index=True, readonly=True)
    user_id = fields.Many2one('res.users', string='Utilisateur', readonly=True)
    new_ref = fields.Char(string='Nouvelle référence', default='')
    wizard_id = fields.Many2one('change.ref.wizard', string='Wizard', ondelete='cascade')
    

    @api.multi
    def change_ref_button(self, journee_id, journee_mg_id):
        for line in self:
            if journee_id.id:
                for ref in journee_id.journee_ref_ids:
                    if ref.name == line.name and line.new_ref:
                        ref.write({'ref': line.new_ref,'ref_confirm':line.new_ref})
            elif journee_mg_id.id:
                for ref in journee_mg_id.journee_ref_ids:
                    if ref.name == line.name and line.new_ref:
                        ref.write({'ref': line.new_ref,'ref_confirm':line.new_ref})
