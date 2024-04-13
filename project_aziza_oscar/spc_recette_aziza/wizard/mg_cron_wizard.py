# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import datetime
from odoo.exceptions import ValidationError
import time
import logging

_logger = logging.getLogger(__name__)


#----------------------------------------------------------
# charger journees wizard
#----------------------------------------------------------


class MgCronWizard(models.TransientModel):
    _name = 'mg.cron.wizard'
    _description = "Action planifiee"
    
    cron_type = fields.Selection([
            ('all', 'Tous les Magasins'),
            ('by_mg', 'Par Magasin'),
        ], string="Type d'action", default='all')
    date_journee = fields.Date(string='Date journée', required="True", default=datetime.datetime.today().date())
    magasin_ids = fields.Many2many('oscar.site', 'mg_cron_wizard_rel', 'mg_cron_wizard_id', 'magasin_id', string='Magasins', domain=[('site_type', '=', 'MAGASIN')])
    
    
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
    
    def charger_journee_button(self):
        if self.cron_type == 'all':
            sql_mg = ("SELECT code_magasin FROM oscar_gold_journee WHERE date_journee = '%s' GROUP BY code_magasin ORDER BY code_magasin DESC;" %(self.date_journee))
            self._cr.execute(sql_mg)
            all_magasin_gold = self._cr.dictfetchall()
              
            sql_journee = ("SELECT * FROM oscar_gold_journee WHERE date_journee = '%s' ORDER BY code_magasin DESC;" %(self.date_journee))
            self._cr.execute(sql_journee)
            all_journee_gold = self._cr.dictfetchall()
            
        elif self.cron_type == 'by_mg':
            code_mg = []
            magasins = self.magasin_ids
            for mg in magasins:
                code_mg.append(int(mg.code))
            code_mg = str(code_mg).replace("[", "(")
            code_mg = code_mg.replace("]", ")")

            sql_mg = ("SELECT code_magasin FROM oscar_gold_journee WHERE date_journee = '%s' AND code_magasin IN %s GROUP BY code_magasin ORDER BY code_magasin DESC;" %(self.date_journee, code_mg))
            self._cr.execute(sql_mg)
            all_magasin_gold = self._cr.dictfetchall()
              
            sql_journee = ("SELECT * FROM oscar_gold_journee WHERE date_journee = '%s' AND code_magasin IN %s ORDER BY code_magasin DESC;" %(self.date_journee, code_mg))
            self._cr.execute(sql_journee)
            all_journee_gold = self._cr.dictfetchall()
        
        i = 0
        len_journee = len(all_magasin_gold)
        
        if len_journee != 0:
            obj_mode = ''
            index = 0
            for data_mg in all_magasin_gold:
                i=i+1
                for data_all in all_journee_gold:
                    
                    if data_mg['code_magasin'] == data_all['code_magasin']:
                        index = index + 1
                        
                        _logger.info("MAGASIN GOLD < %s >"%(data_all['code_magasin']), exc_info=True) 
                        magasin = self.env['oscar.site'].search([('code', '=', data_all['code_magasin'])], limit=1)
                        magasin_id = magasin.id
                        _logger.info("MAGASIN OSCAR < %s >"%(magasin.code), exc_info=True)
                        
                        _logger.info("CAISSIER GOLD < %s >"%(data_all['code_caissier']), exc_info=True)
                        caissier = self.env['hr.employee'].search([('code', '=', data_all['code_caissier'])], limit=1)
                        caissier_id = caissier.id
                        _logger.info("CAISSIER OSCAR < %s >"%(caissier.name), exc_info=True)
                        
                        _logger.info("MOYEN PAIEMENT GOLD < %s >"%(data_all['code_paiement']), exc_info=True)
                        moyen_paiement = self.env['moyen.paiement'].search([('code', '=', data_all['code_paiement'])], limit=1)
                        moyen_paiement_id = moyen_paiement.id
                        _logger.info("MOYEN PAIEMENT OSCAR < %s >"%(moyen_paiement.name), exc_info=True)
                        
                        _logger.info("FOURNISSEUR GOLD < %s >"%(data_all['code_fournisseur']), exc_info=True)
                        fournisseur = self.env['res.partner'].search([('code', '=', data_all['code_fournisseur'])], limit=1)
                        fournisseur_id = fournisseur.id
                        _logger.info("FOURNISSEUR OSCAR < %s >"%(fournisseur.name), exc_info=True)
                        
                        vals_journee = {
                                    'date_journee': data_all['date_journee'],
                                    'magasin_id': magasin_id,
                                    'user_id': 2,
                                    'state': 'new',
                                    }
                         
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
                            today = datetime.datetime.today().date()
                            if journee_line.create_date.date() == today: 
                                vals_paiement = (
                                            data_all['date_journee'].isoformat(),
                                            magasin_id or None,
                                            caissier_id or None,
                                            moyen_paiement_id or None,
                                            data_all['cin_client'] or None,
                                            fournisseur_id or None,
                                            data_all['valeur_tr'],
                                            data_all['nombre_tr'],
                                            data_all['montant'],
                                            2,
                                            journee_line.id,
                                            'new',
                                            True
                                            )
        
                                obj_mode = obj_mode + str(vals_paiement) + ','
                            
                self.printProgressBar(i,len_journee,prefix = 'Progress:',suffix = 'Complete', length = 50)
                if index >= 1000 and obj_mode:
                    sql_mode_paiement = ("INSERT INTO oscar_mode_paiement (date_journee,magasin_id,caissier_id,moyen_paiement_id,cin,fournisseur_id,valeur,nombre_gold,montant_gold,user_id,journee_line_id,state,active) VALUES %s;" %(obj_mode[:-1].replace("None", "NULL")) )
                    try:
                        self._cr.execute(sql_mode_paiement)
                        self._sleeper()
                        index = 0
                        obj_mode = ''
                    except IOError:
                        print("Erreur d'integration des journees")
            if index > 0 and obj_mode:
                sql_mode_paiement = ("INSERT INTO oscar_mode_paiement (date_journee,magasin_id,caissier_id,moyen_paiement_id,cin,fournisseur_id,valeur,nombre_gold,montant_gold,user_id,journee_line_id,state,active) VALUES %s;" %(obj_mode[:-1].replace("None", "NULL")) )
                try:
                    self._cr.execute(sql_mode_paiement)
                    self._sleeper()
                except IOError:
                    print("Erreur d'integration des journees")
                
                    
        else: raise ValidationError("la journée (%s) n'existe pas dans la table d'interface" %(self.date_journee.strftime('%m/%d/%Y')))
        message = _("L'intégration a été effectuée avec succès!")         
        return {
                'effect': {
                    'fadeout': 'slow',
                    'message': message,
                    'type': 'rainbow_man',
                }
            }
