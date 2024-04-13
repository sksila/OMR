# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

TYPE_COMMENT_SELECTION = [
    ('magasin', "Magasin")]


class CommentWizard(models.TransientModel):
    _name = 'comment.wizard.magasin'
    _description = 'Comment Wizard To Magasin'

    @api.model
    def default_get(self, fields):
        result = super(CommentWizard, self).default_get(fields)
        if self._context.get('active_id'):
            derogation = self.env['derogation.derogation'].browse(self._context['active_id'])
            result['derogation_id'] = derogation.id
        return result

    derogation_id = fields.Many2one('derogation.derogation', "Dérogation", required=True)
    comment = fields.Text("Commentaire", required=True)
    type_comment = fields.Selection(TYPE_COMMENT_SELECTION, string='Type', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner')

    def action_confirm_to_magasin(self):
        partner_ids = []
        derogation_obj = self.env['derogation.derogation'].browse(self.env.context.get('active_id'))
        group_id = self.env.ref('spc_oscar_aziza.group_reponsable_magasin').id
        partner_ids = self.env['res.users'].search([('groups_id', '=', group_id), ('profil', '=', 'RESPMAG')]).ids
        print('partner_ids----', partner_ids)
        if self.type_comment == 'magasin':
                self.derogation_id.write({'state': 'magasin', 'commentaire_magasin': self.comment})
                template = self.env.ref('spc_derogation_aziza.spc_email_template_derog')
                if partner_ids:
                    for partner_id in partner_ids:
                        template.send_mail(derogation_obj.id,
                                           force_send=True,
                                           email_values={'recipient_ids': [(4, partner_id)]},
                                           )
        return True

