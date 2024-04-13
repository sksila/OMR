# -*- coding: utf-8 -*-

from odoo import api, fields, models

TYPE_SITE_SELECTION = [
    ('MAGASIN', 'Magasin'),
    ('ENTREPOT', 'Entrepôt'),
    ('CENTRALE', 'Centrale'),
]


class OscarSite(models.Model):
    """Ce presente une Site (Magasin/Entrepôt/Central)"""
    # region Private attributes
    _name = "oscar.site"
    _description = 'Site'
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'default_name'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    #fields of entity site
    name = fields.Char(string='Nom', required="True", track_visibility='onchange', index=True)
    code = fields.Char(string="Code", required="True", track_visibility='onchange', index=True)
    code_site = fields.Char("Code Site")
    default_name = fields.Char(string="Libellé", compute="_compute_default_name", store=True)
    site_type = fields.Selection(TYPE_SITE_SELECTION, string='Type', default='MAGASIN')
    ville = fields.Char(string="Ville")
    adresse = fields.Char(string="Adresse")
    region_id = fields.Many2one('oscar.region', string='Région', track_visibility='onchange', index=True)
    region = fields.Char(string="Région")
    zone_id = fields.Many2one('oscar.zone', string='Zone', track_visibility='onchange', index=True)
    zone = fields.Char(string="Zone")
    date_ouverture = fields.Date(string="Date d'ouverture")
    #fields of entity entrepot
    user_id = fields.Many2one('res.users', string='Responsable', track_visibility='onchange', index=True)
    resp_zone_id = fields.Many2one('res.users', string='Responsable Zone', track_visibility='onchange', index=True) #domain=lambda self: [
        #('groups_id', 'in', [self.env.ref('oscar_aziza.group_responsable_zone_oscar').id])],
    dre_id = fields.Many2one('res.users', string='DRE', track_visibility='onchange', index=True) #, domain=lambda self: [
        #('groups_id', 'in', [self.env.ref('spg_aziza_sav.group_dre_sav').id])]
    user_ids = fields.Many2many('res.users', 'oscar_user_mg_rel', 'magasin_id', 'user_id', string='Utilisateur')
    type_versement = fields.Selection([
        ('direct', 'Direct'),
        ('ibs', 'IBS'),
    ], string='Type de versement', index=True, default='direct', track_visibility='onchange')
    bank_id = fields.Many2one('res.bank', string='Banque', track_visibility='onchange')
    color = fields.Integer('Color Index', default=0)
    active = fields.Boolean(string='Activer', default=True)

    # endregion

    # region Fields method
    _sql_constraints = [
        ('code_site_unique', 'UNIQUE (code)', 'Le code de site doit être unique !')
    ]
    
    @api.multi
    @api.depends('code','name')
    def _compute_default_name(self):
        for site in self:
            if site.code and site.name:
                site.default_name = "[%s] %s" %(site.code, site.name)
    
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

class OscarZone(models.Model):

    # region Private attributes
    _name = "oscar.zone"
    _description = 'Zone'
    _order = 'name'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    #fields of entity site
    name = fields.Char(string='Nom', required="True", index=True)
    code = fields.Char(string="Code", index=True)
    active = fields.Boolean(string='Activer', default=True)

    # endregion

    # region Fields method
    _sql_constraints = [
        ('code_zone_unique', 'UNIQUE (code)', 'Le code de zone doit être unique !'),
        ('name_zone_unique', 'UNIQUE (name)', 'Le nom de zone doit être unique !')
    ]

class OscarRegion(models.Model):

    # region Private attributes
    _name = "oscar.region"
    _description = 'Region'
    _order = 'name'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    #fields of entity site
    name = fields.Char(string='Nom', required="True", index=True)
    code = fields.Char(string="Code", index=True)
    active = fields.Boolean(string='Activer', default=True)

    # endregion

    # region Fields method
    _sql_constraints = [
        ('code_zone_unique', 'UNIQUE (code)', 'Le code de region doit être unique !'),
        ('name_zone_unique', 'UNIQUE (name)', 'Le nom de region doit être unique !')
    ]