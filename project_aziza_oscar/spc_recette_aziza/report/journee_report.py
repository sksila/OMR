# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models

STATE_JOURNEE_SELECTION = [
    ('new', 'En préparation'),
    ('prepared', 'Clôturée'),
    ('road','En route'),
    ('done1','Reçue au l\'entrepôt'),
    ('done','Reçue au siège'),
    ('waiting','En attente'),
    ('accepted','Acceptée'),
    ('waiting2','En attente la deuxième vérification'),
    ('accepted1','Acceptée TR'),
    ('waiting1','En attente avec litige'),
    ('checked','Vérifiée'),
]

STATE_JOURNEE_RECUE_SELECTION = [
    ('prepared', 'Clôturée'),
    ('road','En route'),
    ('done','Reçue'),
    ('waiting','En attente'),
    ('accepted','Acceptée'),
    ('waiting2','En attente la deuxième vérification'),
    ('accepted1','Acceptée TR'),
    ('waiting1','En attente avec litige'),
    ('checked','Vérifiée'),
]

class JourneeReport(models.Model):
    _name = "oscar.journee.report"
    _description = "Journee Statistics"
    _auto = False
    _rec_name = 'date_journee'
    _order = 'date_journee desc'

    date_journee = fields.Date('Date journée', readonly=True)
    magasin_id = fields.Many2one('oscar.site', string='Magasin', readonly=True, domain=[('site_type', '=', 'MAGASIN')])
    resp_mg_id = fields.Many2one('res.users', string='Responsable Magasin', readonly=True)
    resp_zone_id = fields.Many2one('res.users', string='Responsable Zone', readonly=True)
    user_id = fields.Many2one('res.users', string='Utilisateur', readonly=True)
    state = fields.Selection(STATE_JOURNEE_SELECTION, string='Statut', readonly=True, index=True, default='new')
    
    montant_espece = fields.Float(string='Montant espèce', digits=(12,3), readonly=True)
    total_ticket_restaurant = fields.Float(string='Montant total des tickets restaurant', digits=(12,3), readonly=True)
    total_cheque_cadeaux = fields.Float(string='Montant total des chéques cadeaux', digits=(12,3), readonly=True)
    total_carte_ban = fields.Float(string='Montant total des cartes bancaire', digits=(12,3), readonly=True)
    total_cheque = fields.Float(string='Montant total des chèques', digits=(12,3), readonly=True)
    total_sodexo = fields.Float(string='Montant total des cartes Sodexo', digits=(12,3), readonly=True)
    total_bon_aziza = fields.Float(string="Montant total des Bons d'achat Aziza", digits=(12,3), readonly=True)
    total_vente_credit = fields.Float(string='Montant total de vente à crédit', digits=(12,3), readonly=True)
    total_autre_paiement = fields.Float(string='Montant total des autres paiements', digits=(12,3), readonly=True)
    montant_global = fields.Float('Montant Total', digits=(12,3), readonly=True)
    caissier_count = fields.Integer(string='Nombre de caissiers', readonly=True)
    ecart_count = fields.Integer(string='Nombre des écarts', readonly=True)
    is_paid = fields.Boolean(string="Versée")
    
    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'oscar_journee_report')
        self._cr.execute("""
            CREATE or REPLACE VIEW oscar_journee_report AS (
                SELECT
                    j.id,
                    j.date_journee as date_journee,
                    j.magasin_id,
                    (SELECT user_id FROM oscar_site WHERE id=j.magasin_id LIMIT 1) as resp_mg_id,
                    (SELECT resp_zone_id FROM oscar_site WHERE id=j.magasin_id LIMIT 1) as resp_zone_id,
                    j.user_id,
                    j.state,
                    j.montant_espece,
                    j.total_ticket_restaurant,
                    j.total_cheque_cadeaux,
                    j.total_carte_ban,
                    j.total_cheque,
                    j.total_sodexo,
                    j.total_bon_aziza,
                    j.total_vente_credit,
                    j.total_autre_paiement,
                    j.montant_global,
                    j.caissier_count,
                    j.ecart_count,
                    j.is_paid
                FROM
                    "oscar_journee" j
            )""")

        
class JourneeRecueReport(models.Model):
    _name = "oscar.journee.recue.report"
    _description = "Journee Recue Statistics"
    _auto = False
    _rec_name = 'date_journee'
    _order = 'date_journee desc'

    date_journee = fields.Date('Date journée', readonly=True)
    magasin_id = fields.Many2one('oscar.site', string='Magasin', readonly=True, domain=[('site_type', '=', 'MAGASIN')])
    resp_mg_id = fields.Many2one('res.users', string='Responsable Magasin', readonly=True)
    resp_zone_id = fields.Many2one('res.users', string='Responsable Zone', readonly=True)
    user_id = fields.Many2one('res.users', string='Utilisateur', readonly=True)
    controller_id = fields.Many2one('res.users', string='Vérificateur', readonly=True)
    controller_tr_id = fields.Many2one('res.users', string='Vérificateur TR & CC', readonly=True)
    state = fields.Selection(STATE_JOURNEE_RECUE_SELECTION, string='Statut', readonly=True, index=True, default='new')
    
    montant_espece = fields.Float(string='Montant versé', digits=(12,3), readonly=True)
    montant_espece_vr = fields.Float('Montant versé à vérifier', readonly=True)
    total_ticket_restaurant = fields.Float(string='Montant total des tickets restaurant', digits=(12,3), readonly=True)
    total_cheque_cadeaux = fields.Float(string='Montant total des chéques cadeaux', digits=(12,3), readonly=True)
    total_carte_ban = fields.Float(string='Montant total des cartes bancaire', digits=(12,3), readonly=True)
    total_cheque = fields.Float(string='Montant total des chèques', digits=(12,3), readonly=True)
    total_sodexo = fields.Float(string='Montant total des cartes Sodexo', digits=(12,3), readonly=True)
    total_bon_aziza = fields.Float(string="Montant total des Bons d'achat Aziza", digits=(12,3), readonly=True)
    total_vente_credit = fields.Float(string='Montant total de vente à crédit', digits=(12,3), readonly=True)
    total_autre_paiement = fields.Float(string='Montant total des autres paiements', digits=(12,3), readonly=True)
    montant_global = fields.Float('Montant Total', digits=(12,3), readonly=True)
    ecart_count = fields.Integer(string='Nombre des écarts', readonly=True)
    ecart_vl_count = fields.Integer(string='Nombre des écarts validés', readonly=True)
    litige_count = fields.Integer(string='Nombre des litiges', readonly=True)
    
    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'oscar_journee_recue_report')
        self._cr.execute("""
            CREATE or REPLACE VIEW oscar_journee_recue_report AS (
                SELECT
                    j.id,
                    j.date_journee as date_journee,
                    j.magasin_id,
                    (SELECT user_id FROM oscar_site WHERE id=j.magasin_id LIMIT 1) as resp_mg_id,
                    (SELECT resp_zone_id FROM oscar_site WHERE id=j.magasin_id LIMIT 1) as resp_zone_id,
                    j.user_id,
                    j.controller_id,
                    j.controller_tr_id,
                    j.state,
                    j.montant_espece,
                    j.montant_espece_vr,
                    j.total_ticket_restaurant,
                    j.total_cheque_cadeaux,
                    j.total_carte_ban,
                    j.total_cheque,
                    j.total_sodexo,
                    j.total_bon_aziza,
                    j.total_vente_credit,
                    j.total_autre_paiement,
                    j.montant_global,
                    j.ecart_count,
                    j.ecart_vl_count,
                    j.litige_count
                FROM
                    "oscar_journee_recue" j
            )""")

