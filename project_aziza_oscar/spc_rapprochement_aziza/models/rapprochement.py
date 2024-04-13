# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class BonReception(models.Model):
    _name = 'oscar.bon.reception'
    _description = 'Bon de Réception'

    # region Default methods
    # def _default_site(self):
    #     if self.env.user.has_group("spc_oscar_aziza.group_reponsable_magasin"):
    #         return self.env['oscar.site'].search([('user_ids', 'child_of', [self.env.uid])], limit=1)
    #     return

    @api.model
    def default_get(self, fields):
        result = super(BonReception, self).default_get(fields)
        if self.env.user.has_group("spc_oscar_aziza.group_reponsable_magasin"):
            result['site_id'] = self.env['oscar.site'].search([('user_ids', 'child_of', [self.env.uid])],
                                                              limit=1).id or None
            brv = self.env['oscar.brv'].search([('state', '=', 'new')], order='date_brv desc',
                                               limit=1)
            result['num_brv'] = brv.name
            result['supplier_id'] = brv.supplier_id.id
            result['num_bl'] = self.env['oscar.bl'].search(
                [('state', '=', 'new'), ('partner_id', '=', brv.supplier_id.id)], order='date_bl desc', limit=1).name
        return result

    # endregion

    name = fields.Char('Nom', readonly=True, copy=False, index=True)
    date_creation = fields.Date('Date', required=True, default=fields.Date.context_today, index=True)
    site_id = fields.Many2one('oscar.site', string='Magasin', index=True, required=True,
                              readonly=True,
                              states={'new': [('readonly', False)]}, domain=[('site_type', '=', 'MAGASIN')])
    user_id = fields.Many2one('res.users', string='Utilisateur', required=True, readonly=True,
                              states={'new': [('readonly', False)]},
                              domain=lambda self: [
                                  ('groups_id', 'in', [self.env.ref('spc_oscar_aziza.group_reponsable_magasin').id])],
                              default=lambda self: self.env.user)
    rapprochement_ids = fields.One2many('oscar.rapprochement', 'bon_id', string='Rapprochement')
    bl_id = fields.Many2one('oscar.bl', string='BL', index=True,readonly=True)
    brv_id = fields.Many2one('oscar.brv', string='BRV', index=True, readonly=True)
    num_brv = fields.Char('Numéro BRV', required=True, index=True)
    num_bl = fields.Char('Numéro BL', required=True, index=True)
    supplier_id = fields.Many2one('res.partner', string='Fournisseur', domain="[('supplier','=', True)]", index=True)
    state = fields.Selection([
        ('new', 'Nouveau'),
        ('validated', 'Validé'),
    ], string='Status', index=True, readonly=True, default='new', copy=False)
    active = fields.Boolean(string='Activé', default=True)

    @api.multi
    def action_rapprochement(self):
        """ Rapprochement
        """
        print("Site : ", self.site_id.name)
        print("Date : ", self.date_creation)
        brv = self.env['oscar.brv'].search([('name', '=', self.num_brv)])
        bl = self.env['oscar.bl'].search([('name', '=', self.num_bl)])
        self.bl_id = bl.id
        self.brv_id = brv.id

        if brv.supplier_id != bl.partner_id:
            raise ValidationError(_('Le fournisseur BL et le fournisseur BRV sont différents!'))
        vals = {}
        self.rapprochement_ids = [(5,0,0)]
        new_rapprochement = []
        brv_lst = []
        bl_lst = []
        for brv_line in brv.brv_line_ids:
            brv_lst.append(brv_line.product_id)
            for bl_line in bl.bl_line_ids:
                bl_lst.append(bl_line.product_id)
                if brv_line.product_id == bl_line.product_id:
                    vals = {
                        'product_id': bl_line.product_id.id,
                        'supplier_id': self.supplier_id.id,
                        'qte_livree': bl_line.qte_livree,
                        'qte_recue': brv_line.qte_recue,
                        'bon_id': self.id,
                    }
                    new_rapprochement.append((0,0,vals))
        print('symmetric_difference : ', list(set(brv_lst).symmetric_difference(set(bl_lst))))
        diff_lst = list(set(brv_lst).symmetric_difference(set(bl_lst)))
        if diff_lst:
            for brv_line in brv.brv_line_ids:
                for diff in diff_lst:
                    if brv_line.product_id == diff:
                        vals = {
                            'product_id': brv_line.product_id.id,
                            'supplier_id': self.supplier_id.id,
                            'qte_livree': 0,
                            'qte_recue': brv_line.qte_recue,
                            'bon_id': self.id,
                        }
                        new_rapprochement.append((0,0,vals))
            for bl_line in bl.bl_line_ids:
                for diff in diff_lst:
                    if bl_line.product_id == diff:
                        vals = {
                            'product_id': bl_line.product_id.id,
                            'supplier_id': self.supplier_id.id,
                            'qte_livree': bl_line.qte_livree,
                            'qte_recue': 0,
                            'bon_id': self.id,
                        }
                        new_rapprochement.append((0,0,vals))
        self.rapprochement_ids = new_rapprochement
        return

    @api.multi
    def action_validate(self):
        """ Validate bon de reception
        """
        self.brv_id.write({'state': 'validated'})
        self.bl_id.write({'state': 'validated'})
        self.filtered(lambda s: s.state == 'new').write({'state': 'validated'})
        # for rapp in self.rapprochement_ids:
        #     rapp.write({'state': 'validated'})

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('oscar.rapprochement')
        rapprochement = super(BonReception, self).create(vals)
        return rapprochement


class Rapprochement(models.Model):
    _name = 'oscar.rapprochement'
    _description = 'Rapprochement'

    name = fields.Char('Désignation', related='product_id.name')
    product_id = fields.Many2one('product.template', string='Article', index=True, required=True, ondelete='cascade')
    supplier_id = fields.Many2one('res.partner', string='Fournisseur', index=True)
    num_bl = fields.Char('Numéro BL', index=True)
    qte_livree = fields.Float('Qté livrée')
    unite_livree = fields.Char('Unité livrée')
    num_brv = fields.Char('Numéro BRV', index=True)
    qte_recue = fields.Float('Qté reçue')
    ecart = fields.Float('Écart', compute="_compute_ecart", store=True)
    bon_id = fields.Many2one('oscar.bon.reception', string='Bon de Réception', index=True, ondelete='cascade')

    @api.multi
    @api.depends('qte_livree', 'qte_recue')
    def _compute_ecart(self):
        for line in self:
            line.ecart = line.qte_recue - line.qte_livree
