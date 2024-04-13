# -*- coding: utf-8 -*-
from odoo import fields, models
import logging

_logger = logging.getLogger(__name__)

TYPE_SITE_SELECTION = [
    ('MAGASIN', 'Magasin'),
    ('ENTREPOT', 'Entrepôt'),
    ('CENTRALE', 'Centrale'),
]


class GoldSite(models.Model):
    _name = 'oscar.inter.site'
    _description = 'Site (Gold)'
    _rec_name = 'site_lib'

    code_site = fields.Char(string="Code", required="True", index=True)
    site_lib = fields.Char(string="Libellé", required="True")
    site_type = fields.Selection(TYPE_SITE_SELECTION, string='Type', default='MAGASIN')
    respzone = fields.Char(string='Responsable Zone')
    date_ouverture = fields.Date(string="Date d'ouverture")
    adresse = fields.Char(string="Adresse")
    ville = fields.Char(string="Ville")
    region = fields.Char(string="Region")
    zone = fields.Char(string="Zone")
    actif = fields.Boolean(string='Actif', default=True)

    def planned_gold_integration_sites(self):
        _logger.info("______________________GOLD integration Site__________________________", exc_info=True)

        # resp_zone_id se type int et respzone de type char !!!

        site_inter = self.env['oscar.inter.site'].search([])
        i = 0
        for site in site_inter:
            site_oscar = self.env['oscar.site'].search([('code', '=', site.code_site),'|',('active', '=', True),('active', '=', False)], limit=1)
            region = self.env['oscar.region'].search([('name', '=', site.region)], limit=1) or self.env['oscar.region'].create({'name': site.region})
            zone = self.env['oscar.zone'].search([('name', '=', site.zone)], limit=1) or self.env['oscar.zone'].create({'name': site.zone})
            vals = {
                'code': site.code_site,
                'name': site.site_lib,
                'default_name': "[%s] %s" % (site.code_site,site.site_lib),
                'site_type': site.site_type,
                'date_ouverture': site.date_ouverture,
                'ville': site.ville,
                'region_id': region.id,
                'region': site.region,
                'zone_id': zone.id,
                'zone': site.zone,
                'active': site.actif,
            }
            if site_oscar:
                _logger.info("Write Site : %s" % (site.code_site), exc_info=True)
                site_oscar.write(vals)
            else:
                i += 1
                _logger.info("Create Site : %s" % (site.code_site), exc_info=True)
                self.env['oscar.site'].create(vals)
        _logger.info("---> %s <--- Sites Created " % (i), exc_info=True)

        _logger.info("Integration was done", exc_info=True)
