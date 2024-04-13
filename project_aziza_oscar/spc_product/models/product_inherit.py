# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    vl = fields.Char('VL')
    spot_id = fields.Many2one('oscar.product.spot', 'Spot')
    # supplier_id = fields.Many2one('res.partner', string='Fournisseur', index=True)
    product_detail_ids = fields.One2many('spc_product.detail', 'product_id', string="Details")
    barcode = fields.Char(string='Code Barre', copy=False, index=True)
    to_update = fields.Integer(default=0, index=True)
    code_product = fields.Char(string="Code Produit")
    approvisionneur_ids = fields.Many2many('res.users', 'approvisionneur_product_rel', string='Approvisionneur')
    tag_ids = fields.Many2many('oscar.product.tag', 'oscar_product_tag_rel', 'product_id', 'tag_id', string='Étiquettes')
    new_rec_name = fields.Char()
    # Indexation de code
    default_code = fields.Char(index=True)

    _sql_constraints = [
        ('reference_uniq', 'UNIQUE (default_code)', "Le code d'article doit être unique")
    ]

    #plano
    marque = fields.Char()
    niveau = fields.Char()
    classement = fields.Char()
    facing_prevue = fields.Char()
    #promo

    prix_promo = fields.Char('Prix promo')

    supplier_ids = fields.Many2many('res.partner', string='Fournisseurs', domain=[('supplier','=',True)])
    # element_niveau = fields.Char("Element-Niveau")
    # facing = fields.Char("Facing")
    #
    # stock_min = fields.Char("Stock Min")
    #
    # nature = fields.Char("Nature")


class ProductCategory(models.Model):
    _inherit = "product.category"

    code = fields.Char(string="Code")
    active = fields.Boolean(string="Activé", default=True)
    code_product_category = fields.Char(string="Code Catégorie de produit")

    _sql_constraints = [
        ('code_uniq', 'UNIQUE (code)', "Le code de catégorie d'article doit être unique")
    ]


class ProductSpot(models.Model):
    _name = "oscar.product.spot"
    _description = "Spot"
    _inherit = ['mail.thread']
    _mail_post_access = 'read'
    _order = "id desc"

    name = fields.Char('Nom', required=True)

    _sql_constraints = [
        ('name_uniq', 'UNIQUE (name)', "Le nom de spot doit être unique")
    ]


class Tag(models.Model):
    _name = "oscar.product.tag"
    _description = "Étiquettes"

    name = fields.Char('Nom', required=True)
    color = fields.Integer('Couleur')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Le nom existe déjà !"),
    ]