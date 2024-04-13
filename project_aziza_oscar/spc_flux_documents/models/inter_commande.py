# -*- coding: utf-8 -*-
from odoo import fields, models
import logging

_logger = logging.getLogger(__name__)

class CommandeGold(models.Model):
    _name = "oscar.commande.inter"
    _description = "Table Commande Gold"
    _rec_name = "num_cmd"

    num_cmd = fields.Char('Num Commande', required=True)
    date_cmd = fields.Datetime('Date Commande')
    code_site = fields.Char(string='Code Site')
    lib_site = fields.Char('Site')
    code_fr = fields.Char('Code Fournisseur')
    lib_fr = fields.Char('Fournisseur')
    
    
    def planned_oscar_commande(self):
        _logger.info("______________________GOLD integration Commande__________________________", exc_info=True)

        sql_insert_commande = """
        INSERT INTO commande_gold(name, code_site, lib_site, code_fr, lib_fr, date_commande,fournisseur_id,magasin_id,active) 
        SELECT oc.num_cmd, oc.code_site, oc.lib_site, oc.code_fr, oc.lib_fr, oc.date_cmd,(SELECT id FROM res_partner fa WHERE fa.code = oc.code_fr lIMIT 1),(SELECT id FROM oscar_site ma WHERE ma.code = oc.code_site LIMIT 1),True FROM oscar_commande_inter oc 
        ON CONFLICT (name) DO NOTHING;
        """
        self.env.cr.execute(sql_insert_commande)
        _logger.info("Integration was done", exc_info=True)
        return
    
