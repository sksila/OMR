# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models
from datetime import datetime


STATE_CLAIM_SELECTION = [
    ('new', 'Nouvelle'),
    ('road','En route vers SAV'),
    ('done1','Reçue à l\'Entrepôt'),
    ('done2','Reçue au Siège (SAV)'),
    ('repair','En réparation'),
    ('waiting','En attente la validation RM'),
    ('validated','Validée par Magasin'),
    ('fixed','Réparée'),
    ('refuse','Refusée'),
    ('road1','En route vers magasin'),
    ('done01','Reçue à l\'Entrepôt'),
    ('back','Avoir'),
    ('exchanged','Echange'),
    ('done3','Reçue au Magasin'),
    ('done4','Clôturée'),
]

class ClaimReport(models.Model):
    _name = "sav.claim.report"
    _description = "Claim Statistics"
    _auto = False
    _rec_name = 'date_claim'
    _order = 'date_claim desc'




    name = fields.Char(string='Numéro réclamation', readonly=True)
    date_claim = fields.Date(string='Date de réclamation', readonly=True)
    customer_id = fields.Many2one('res.partner', string='Client', readonly=True)
    date_purchase = fields.Date(string="Date d'achat", readonly=True)
    product_id = fields.Many2one('product.template', string='Article', readonly=True)
    code = fields.Char(string='N° de série', readonly=True)
    supplier_id = fields.Many2one('res.partner', string='Fournisseur')
    panne = fields.Text(string='Panne', readonly=True)
    magasin_id = fields.Many2one('oscar.site', string='Magasin', readonly=True)
    resp_mg_id = fields.Many2one('res.users', string='Responsable Magasin', readonly=True)
    resp_zone_id = fields.Many2one('res.users', string='Responsable Zone', readonly=True)
    
    user_id = fields.Many2one('res.users', string='Réceptionné par', readonly=True)
    
    date_end_guarantee = fields.Date(string="Date fin de garantie", readonly=True)
    has_receipt = fields.Boolean(string="Ticket / Facture", readonly=True)
    has_guarantee = fields.Boolean(string="Certificat de garantie", readonly=True)
    has_accessories = fields.Boolean(string="Présence accessoires", readonly=True)
    repair_mode = fields.Selection([
        ('guarantee', 'Sous garantie'),
        ('not_guarantee', 'Hors garantie'),
        ], string='Nature réparation')
    state = fields.Selection(STATE_CLAIM_SELECTION, string='Statut')
    is_fixed = fields.Boolean(string="Réparée", readonly=True)
    
    duration_road_sav = fields.Float(string='Durée Magasin (aller)', readonly=True, store=True)
    duration_sav_to_mag = fields.Float(string='Durée Magasin (retour)', readonly=True, store=True)

    duration_received_in_siege = fields.Float(string='Durée Entrepôt (aller)')
    duration_received_in_mag_sav = fields.Float(string='Durée Entrepôt (retour)')

    duration_fixed_claim = fields.Float(string='Durée de réparation SAV')
    duration_total_claim = fields.Float(string='Durée de traitement de réclamation')

    def days_between(self, d1, d2):
        return abs((d2 - d1).days)


#-----------------Délai Magasin--------------------
    #---Aller
    def _compute_duration_road_sav(self):
        query_1 = """SELECT create_date FROM public.mail_tracking_value
                               WHERE mail_message_id in (
                               SELECT m.id FROM mail_message AS m join oscar_sav_claim  on m.res_id = oscar_sav_claim.id  
                               WHERE model='oscar.sav.claim' and m.res_id=oscar_sav_claim.id)
                               AND field='state' AND old_value_char = 'Nouvelle'
                               AND new_value_char = 'En route vers SAV'; """
        self._cr.execute(query_1)
        date_road_to_warehouse = self.env.cr.dictfetchone()
        print('date_road_to_warehouse***', date_road_to_warehouse)

        duery_2 = """SELECT create_date FROM public.mail_tracking_value
                                       WHERE mail_message_id in (SELECT m.id FROM mail_message AS m join oscar_sav_claim  on m.res_id = oscar_sav_claim.id  WHERE model='oscar.sav.claim' and m.res_id=oscar_sav_claim.id) AND field='state' AND new_value_char = 'Nouvelle' limit 1;"""
        self._cr.execute(duery_2)
        date_create_claim = self.env.cr.dictfetchone()
        print('date_create_claim****', date_create_claim)
        duration_road_sav = self.days_between(date_road_to_warehouse['create_date'],date_create_claim['create_date'])
        print('result délai magasin aller****', duration_road_sav)
        return duration_road_sav
    #---Retour
    def _compute_duration_sav_to_mag(self):
        query_1 = """SELECT create_date FROM public.mail_tracking_value
                               WHERE mail_message_id in (
                               SELECT m.id FROM mail_message AS m join oscar_sav_claim  on m.res_id = oscar_sav_claim.id  WHERE model='oscar.sav.claim' and m.res_id=oscar_sav_claim.id)
                               AND field='state' AND old_value_char LIKE '%Entrepôt%'
                               AND new_value_char = 'En route vers magasin' limit 1; """
        self._cr.execute(query_1)
        date_warehouse_to_mag = self.env.cr.dictfetchone()
        print('date_warehouse_to_mag***', date_warehouse_to_mag)

        duery_2 = """SELECT create_date FROM public.mail_tracking_value
                                       WHERE mail_message_id in (
                                       SELECT m.id FROM mail_message AS m join oscar_sav_claim  on m.res_id = oscar_sav_claim.id  WHERE model='oscar.sav.claim' and m.res_id=oscar_sav_claim.id) 
                                       AND field='state' AND old_value_char = 'En route vers magasin' 
                                       AND new_value_char = 'Reçue au Magasin'  limit 1;"""
        self._cr.execute(duery_2)

        date_received_in_mag = self.env.cr.dictfetchone()
        print('date_received_in_mag****', date_received_in_mag)
        duration_sav_to_mag = self.days_between(date_warehouse_to_mag['create_date'],date_received_in_mag['create_date'])
        print('result delai magasin retour****', duration_sav_to_mag)
        return duration_sav_to_mag
# -----------------End Délai Magasin--------------------

# -----------------Délai Entrepôt--------------------
    #---Aller
    def _compute_duration_received_in_siege(self):
        query_1 = """SELECT create_date FROM public.mail_tracking_value
                                  WHERE mail_message_id in (
                                  SELECT m.id FROM mail_message AS m join oscar_sav_claim  on m.res_id = oscar_sav_claim.id  WHERE model='oscar.sav.claim' and m.res_id=oscar_sav_claim.id)
                                  AND field='state' AND old_value_char Like '%Nouvelle%'
                                  AND new_value_char LIKE '%En route vers SAV%' limit 1; """
        self._cr.execute(query_1)
        date_road_to_mag = self.env.cr.dictfetchone()
        print('date_road_to_mag***', date_road_to_mag)

        duery_2 = """SELECT create_date FROM public.mail_tracking_value
                                          WHERE mail_message_id in (SELECT m.id FROM mail_message AS m join oscar_sav_claim  on m.res_id = oscar_sav_claim.id  WHERE 
                                          model='oscar.sav.claim' and m.res_id=oscar_sav_claim.id) AND field='state' 
                                          AND old_value_char LIKE '%En route vers SAV%'
                                        AND new_value_char LIKE '%Reçue au Siège%' limit 1;"""
        self._cr.execute(duery_2)
        date_received_in_siege = self.env.cr.dictfetchone()
        print('date_received_in_siege****', date_received_in_siege)
        duration_received_in_siege = self.days_between(date_road_to_mag['create_date'],date_received_in_siege['create_date'])
        print('result délai entrepot aller****', duration_received_in_siege)
        return duration_received_in_siege

    #---Retour
    def _compute_duration_received_in_mag_sav(self):
        query_1 = """SELECT create_date FROM public.mail_tracking_value
                                  WHERE mail_message_id in (
                                  SELECT m.id FROM mail_message AS m join oscar_sav_claim  on m.res_id = oscar_sav_claim.id  WHERE model='oscar.sav.claim' and m.res_id=oscar_sav_claim.id)
                                  AND field='state' AND old_value_char Like '%Réparée%'
                                  AND new_value_char LIKE '%En route vers magasin%' limit 1; """
        self._cr.execute(query_1)
        date_reparee_to_mag = self.env.cr.dictfetchone()
        print('date_reparee_to_mag***', date_reparee_to_mag)

        duery_2 = """SELECT create_date FROM public.mail_tracking_value
                                          WHERE mail_message_id in (SELECT m.id FROM mail_message AS m join oscar_sav_claim  on m.res_id = oscar_sav_claim.id  WHERE 
                                          model='oscar.sav.claim' and m.res_id=oscar_sav_claim.id) AND field='state' 
                                          AND old_value_char LIKE '%En route vers magasin%'
                                        AND new_value_char LIKE '%Reçue au Magasin%' limit 1;"""
        self._cr.execute(duery_2)
        date_received_in_mag_sav = self.env.cr.dictfetchone()
        print('date_received_in_mag****', date_received_in_mag_sav)
        duration_received_in_mag_sav = self.days_between(date_reparee_to_mag['create_date'], date_received_in_mag_sav['create_date'])
        print('result délai entrepot retour****', duration_received_in_mag_sav)
        return duration_received_in_mag_sav
# -----------------End Délai Entrepôt--------------------

# -----------------End Délai de réparation SAV--------------------
    def _compute_duration_fixed_claim(self):
        query_1 = """SELECT create_date FROM public.mail_tracking_value
                                  WHERE mail_message_id in (
                                  SELECT m.id FROM mail_message AS m join oscar_sav_claim  on m.res_id = oscar_sav_claim.id  WHERE model='oscar.sav.claim' and m.res_id=oscar_sav_claim.id)
                                  AND field='state' AND old_value_char Like '%En route vers SAV%'
                                  AND new_value_char LIKE '%Reçue au Siège%' limit 1; """
        self._cr.execute(query_1)
        date_received_in_siege_fixed = self.env.cr.dictfetchone()
        print('date_received_in_siege_fixed***', date_received_in_siege_fixed)

        duery_2 = """SELECT create_date FROM public.mail_tracking_value
                                          WHERE mail_message_id in (SELECT m.id FROM mail_message AS m join oscar_sav_claim  on m.res_id = oscar_sav_claim.id  WHERE 
                                          model='oscar.sav.claim' and m.res_id=oscar_sav_claim.id) AND field='state' 
                                          AND old_value_char LIKE '%Réparée%'
                                        AND new_value_char LIKE '%En route vers magasin%' limit 1;"""
        self._cr.execute(duery_2)
        date_road_to_mag_sav = self.env.cr.dictfetchone()
        print('date_road_to_mag_sav****', date_road_to_mag_sav)
        duration_fixed_claim = self.days_between(date_received_in_siege_fixed['create_date'],date_road_to_mag_sav['create_date'])
        print('result delai de réparation SAV****', duration_fixed_claim)
        return duration_fixed_claim

    # -----------------End Délai de traitement de réclamation--------------------
    def _compute_duration_total_claim(self):
        query_1 = """SELECT create_date FROM public.mail_tracking_value
                                     WHERE mail_message_id in (
                                     SELECT m.id FROM mail_message AS m join oscar_sav_claim  on m.res_id = oscar_sav_claim.id  WHERE model='oscar.sav.claim' and m.res_id=oscar_sav_claim.id)
                                     AND field='state' AND old_value_char Like '%En route vers magasin%'
                                     AND new_value_char LIKE '%Reçue au Magasin%' limit 1; """
        self._cr.execute(query_1)
        date_received_in_magasin = self.env.cr.dictfetchone()
        print('date_received_in_magasin***', date_received_in_magasin)

        duery_2 = """SELECT create_date FROM public.mail_tracking_value
                                             WHERE mail_message_id in (SELECT m.id FROM mail_message AS m join oscar_sav_claim  on m.res_id = oscar_sav_claim.id  WHERE 
                                             model='oscar.sav.claim' and m.res_id=oscar_sav_claim.id) AND field='state' 
                                            AND new_value_char = 'Nouvelle' limit 1;"""
        self._cr.execute(duery_2)
        date_create_claim_sav = self.env.cr.dictfetchone()
        print('date_create_claim_sav****', date_create_claim_sav)
        duration_total_claim = self.days_between(date_received_in_magasin['create_date'],date_create_claim_sav['create_date'])
        print('result delai de traitement de réclamation****', duration_total_claim)
        return duration_total_claim

    def _select(self):
        return """
               SELECT
                  c.id,
                c.name,
                c.date_claim as date_claim,
                %s as duration_road_sav,
                %s as duration_sav_to_mag,
                %s as duration_received_in_siege,
                %s as duration_received_in_mag_sav,
                %s as duration_fixed_claim,
                %s as duration_total_claim,
                c.magasin_id,
                (SELECT user_id FROM oscar_site WHERE id=c.magasin_id LIMIT 1) as resp_mg_id,
                (SELECT resp_zone_id FROM oscar_site WHERE id=c.magasin_id LIMIT 1) as resp_zone_id,
                c.customer_id,
                c.date_purchase as date_purchase,
                c.product_id,
                c.code,
                c.panne,
                c.date_end_guarantee as date_end_guarantee,
                c.has_receipt,
                c.has_guarantee,
                c.has_accessories,
                c.user_id,
                c.state,
                c.is_fixed,
                c.supplier_id as supplier_id
           """ %(self._compute_duration_road_sav(), self._compute_duration_sav_to_mag(), self._compute_duration_received_in_siege(),
                 self._compute_duration_received_in_mag_sav(), self._compute_duration_fixed_claim(), self._compute_duration_total_claim())

    def _from(self):
        return """
               FROM oscar_sav_claim AS c
           """

    def _join(self):
        return """
               JOIN product_template AS p ON (c.product_id=p.id)
           """

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
                CREATE OR REPLACE VIEW %s AS (
                    %s
                    %s
                    %s
                   
                )
            """ % (self._table, self._select(), self._from(), self._join())
                         )

