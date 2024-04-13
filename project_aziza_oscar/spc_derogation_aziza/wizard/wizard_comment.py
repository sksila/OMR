# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

TYPE_COMMENT_SELECTION = [
    ('purchase', "Achat"),
    ('exploitation', "Exploitation"),
    ('quality', "Qualité")]


class CommentWizard(models.TransientModel):
    _name = 'comment.wizard'
    _description = 'Comment Wizard'

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


    @api.constrains('qty_partielle', 'qty_derogation')
    def _check_quantity(self):
        if self.derogation_id.state == 'to_approve':
            for rec in self.derogation_id.product_ids:
                if rec.qty_derogation == 0:
                    raise ValidationError("La quantité totale UVC doit être supérieur à zéro.")
        if self.derogation_id.state == 'approve_quality' and self.derogation_id.type == 'dlv_entrepot':
            for rec in self.derogation_id.product_ids:
                if rec.qty_partielle <= 0:
                    raise ValidationError("La quantité partielle UVC doit être supérieur à zéro.")

    def action_confirm(self):
        partner_ids = []
        derogation_obj = self.env['derogation.derogation'].browse(self.env.context.get('active_id'))
        self._check_quantity()
        if self.type_comment == 'purchase':
            if (self.derogation_id.type == 'dlv_reception' or self.derogation_id.type == 'dlv_entrepot')and self.derogation_id.origin == 'import':
                self.derogation_id.write({'state': 'controle_gestion', 'commentaire_achat': self.comment})
                partner_ids = derogation_obj.get_partner_ids(self.env.ref('spc_oscar_aziza.group_cg_aziza').id)

            elif self.derogation_id.type == 'dlv_reception' and self.derogation_id.origin == 'local':
                self.derogation_id.write({'state': 'approve_quality', 'commentaire_achat': self.comment})
                partner_ids = derogation_obj.get_partner_ids(self.env.ref('spc_oscar_aziza.group_quality_product_aziza').id)

            elif self.derogation_id.type == "dlv_entrepot" and self.derogation_id.origin == 'local':
                self.derogation_id.write({'state': 'approve_exp', 'commentaire_achat': self.comment})
                partner_ids = derogation_obj.get_partner_ids(self.env.ref('spc_oscar_aziza.group_DE').id)

            elif self.derogation_id.type != 'dlv' and self.derogation_id.origin == 'import':
                self.derogation_id.write({'state': 'controle_gestion', 'commentaire_achat': self.comment})
                partner_ids = derogation_obj.get_partner_ids(self.env.ref('spc_oscar_aziza.group_cg_aziza').id)

            elif self.derogation_id.type != 'dlv' and self.derogation_id.origin == 'local':
                self.derogation_id.write({'state': 'approve_quality', 'commentaire_achat': self.comment})
                partner_ids = derogation_obj.get_partner_ids(
                    self.env.ref('spc_oscar_aziza.group_quality_product_aziza').id)

        elif self.type_comment == 'exploitation':
            if self.derogation_id.type == 'produit':
                self.derogation_id.write({'state': 'approve_dg', 'commentaire_exploitation': self.comment})
                partner_ids = derogation_obj.get_partner_ids(self.env.ref('spc_oscar_aziza.group_dg').id)

            else:
                for rec in self.derogation_id.product_ids:
                    if (rec.qty_partielle <= 0) and (self.derogation_id.state == 'approve_exp'):
                        raise ValidationError(_('Quantité partielle doit avoir une valeur positif'))
                    else:
                        self.derogation_id.write({'state': 'approve_quality', 'commentaire_exploitation': self.comment})
                        partner_ids = derogation_obj.get_partner_ids(self.env.ref('spc_oscar_aziza.group_quality_product_aziza').id)
        elif self.type_comment == 'quality':
            self.derogation_id.write({'state': 'approve_dg', 'commentaire_dqp': self.comment})
            partner_ids = derogation_obj.get_partner_ids(self.env.ref('spc_oscar_aziza.group_dg').id)

        template = self.env.ref('spc_derogation_aziza.spc_email_template_derog')
        for partner_id in partner_ids:
            template.send_mail(derogation_obj.id,
                               force_send=True,
                               email_values={'recipient_ids': [(4, partner_id)]},
                               )

        return True

