# -*- coding: utf-8 -*-


from odoo import models, fields, api
from datetime import datetime, date
from odoo.exceptions import ValidationError
import time
import logging

_logger = logging.getLogger(__name__)



class GoldJournee(models.Model):
    _name = 'oscar.gold.journee'
    _description = 'Journée (Gold)'
    _rec_name = 'date_journee'
    _order = "date_journee desc"

    line_id = fields.Char(string='Identifiant')
    date_journee = fields.Date(string='Date journée', required=True, index=True)
    code_magasin = fields.Integer(string='Code Magasin', required=True)
    code_caissier = fields.Integer(string='Code Caissier', required=True,)
    code_paiement = fields.Integer(string='Code paiement')
    code_fournisseur = fields.Integer(string='Code Fournisseur')
    cin_client = fields.Char(string='CIN Client')
    valeur_tr = fields.Float(string='Valeur', digits=(12,3))
    nombre_tr = fields.Integer(string='Nombre')
    montant = fields.Float(string='Montant', digits=(12,3))
    
    def printProgressBar(self, iteration, total, prefix='', suffix='', decimals=1, length=100, fill='#'):
        """
        Call in a loop to create terminal progress bar
        @params:
            iteration   - Required  : current iteration (Int)
            total       - Required  : total iterations (Int)
            prefix      - Optional  : prefix string (Str)
            suffix      - Optional  : suffix string (Str)
            decimals    - Optional  : positive number of decimals in percent complete (Int)
            length      - Optional  : character length of bar (Int)
            fill        - Optional  : bar fill character (Str)
        """
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        _logger.info("\r%s |%s| %s%% %s" %(prefix, bar, percent, suffix), exc_info=True)
        if iteration == total:
            return
    
    
    
    def _sleeper(self):
        _logger.info("Waiting...", exc_info=True)
        time.sleep(1)
        return
    
    def planned_gold_integration_journees(self):
        sql_date = ("SELECT date_journee FROM oscar_gold_journee ORDER BY date_journee DESC LIMIT 1;")
        self._cr.execute(sql_date)
        last_date_journee = self._cr.dictfetchall()
        print(last_date_journee)
        sql_mg = ("SELECT code_magasin FROM oscar_gold_journee WHERE date_journee = '%s' GROUP BY code_magasin ORDER BY code_magasin DESC;" %(str(last_date_journee[0]['date_journee'])))
        self._cr.execute(sql_mg)
        all_magasin_gold = self._cr.dictfetchall()
         
        sql_journee = ("SELECT * FROM oscar_gold_journee WHERE date_journee = '%s' ORDER BY code_magasin DESC;" %(str(last_date_journee[0]['date_journee'])))
        self._cr.execute(sql_journee)
        all_journee_gold = self._cr.dictfetchall()
        
        i = 0
        len_journee = len(all_journee_gold)
        len_mg = len(all_magasin_gold)
        _logger.info("Nombre de lignes : %s"%(len_journee), exc_info=True)
        _logger.info("Nombre de magasins : %s"%(len_mg), exc_info=True)
        l = 0
        if len_mg != 0:
            obj_mode = ''
            index = 0
            for data_mg in all_magasin_gold:
                i=i+1
                
                for data_all in all_journee_gold:
                    
                    if data_mg['code_magasin'] == data_all['code_magasin']:
                        l = l + 1
                        index = index + 1   
                        magasin_id = self.env['oscar.site'].search([('code', '=', str(data_all['code_magasin']))], limit=1).id
                        caissier_id = self.env['hr.employee'].search([('code', '=', str(data_all['code_caissier']))], limit=1).id
                        moyen_paiement_id = self.env['moyen.paiement'].search([('code', '=', str(data_all['code_paiement']))], limit=1).id
                        fournisseur_id = self.env['res.partner'].search([('code', '=', str(data_all['code_fournisseur'])),('type_tr', '!=', False)], limit=1).id
                        
                        
                        vals_journee = {
                                    'date_journee': data_all['date_journee'],
                                    'magasin_id': magasin_id,
                                    'user_id': 2,
                                    'state': 'new',
                                    }
                        if magasin_id:
                            journee = self.env['oscar.journee'].search([('date_journee', '=', data_all['date_journee']),('magasin_id', '=', magasin_id)]) or self.env['oscar.journee'].create(vals_journee)
                        
                            if journee.state == 'new':
                                vals_journee_line = {
                                                'date_journee': data_all['date_journee'],
                                                'magasin_id': magasin_id,
                                                'caissier_id': caissier_id,
                                                'journee_id': journee.id,
                                                'user_id': 2,
                                                'state': 'new',
                                                }

                                journee_line = self.env['oscar.journee.line'].search([('date_journee', '=', data_all['date_journee']),('caissier_id', '=', caissier_id),('magasin_id', '=', magasin_id)]) or self.env['oscar.journee.line'].create(vals_journee_line)

                                if data_all['code_paiement'] == 1:
                                    journee_line.write({'espece_gold': data_all['montant']})

                                today = datetime.today().date()
                                if journee_line.create_date.date() == today:

                                    vals_paiement = (
                                                str(data_all['date_journee']),
                                                magasin_id or None,
                                                caissier_id or None,
                                                moyen_paiement_id or None,
                                                str(data_all['cin_client']) or None,
                                                fournisseur_id or None,
                                                data_all['valeur_tr'],
                                                data_all['nombre_tr'],
                                                data_all['montant'],
                                                2,
                                                journee_line.id,
                                                'new',
                                                True
                                                )

                                    str_log = "LINE N %s : Journee %s, Magasin N %s, Code Magasin %s, MP %s" %(l,data_all['date_journee'],i,data_all['code_magasin'],data_all['code_paiement'])
                                    _logger.info("%s" %(str_log), exc_info=True)

                                    obj_mode = obj_mode + str(vals_paiement) + ','
                                
                self.printProgressBar(i,len_mg,prefix = 'Progress:',suffix = 'Complete', length = 50)
                if index >= 1000 and obj_mode:
                    sql_mode_paiement = ("INSERT INTO oscar_mode_paiement (date_journee,magasin_id,caissier_id,moyen_paiement_id,cin,fournisseur_id,valeur,nombre_gold,montant_gold,user_id,journee_line_id,state,active) VALUES %s;" %(obj_mode[:-1].replace("None", "NULL")) )
                    try:
                        self._cr.execute(sql_mode_paiement)
                        self._sleeper()
                        index = 0
                        obj_mode = ''
                    except Exception:
                        _logger.info("Erreur d'integration des journees!", exc_info=True)
            if index > 0 and obj_mode:
                sql_mode_paiement = ("INSERT INTO oscar_mode_paiement (date_journee,magasin_id,caissier_id,moyen_paiement_id,cin,fournisseur_id,valeur,nombre_gold,montant_gold,user_id,journee_line_id,state,active) VALUES %s;" %(obj_mode[:-1].replace("None", "NULL")) )
                try:
                    self._cr.execute(sql_mode_paiement)
                    self._sleeper()
                except Exception:
                    _logger.info("Erreur d'integration des journees!", exc_info=True)
                
        return True
        