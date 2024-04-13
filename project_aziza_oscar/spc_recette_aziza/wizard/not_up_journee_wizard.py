# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import datetime,timedelta
from odoo.exceptions import ValidationError

class NotUpJournee(models.TransientModel):
    _name = 'notup.journee.wizard'
    _description = "Journee non remontee"
    _rec_name = "date_start"
    
    date_start = fields.Date(string='Du', required="True", default=datetime.today().date() - timedelta(days=1))
    date_end = fields.Date(string='Au', required="True", default=datetime.today().date() - timedelta(days=1))
    notup_journee_line_ids = fields.One2many('notup.journee.wizard.line', 'notup_journee_id', string='Journées')
    
    @api.model
    @api.onchange('date_start','date_end')
    def compute_notup_journee(self):
        vals = {}
        data = []
        start = self.date_start
        end = self.date_end
        delta = end - start  
        if (start <= datetime.today().date() - timedelta(days=1)):

            for date in range(delta.days + 1):
                sql_magasin ='''
                            SELECT name,code,date_ouverture 
                                FROM oscar_site
                                WHERE id NOT IN (SELECT magasin_id FROM oscar_journee WHERE date_journee='%s') 
                                AND user_id IS NOT NULL AND date_ouverture <= '%s';
                            ''' %((start + timedelta(date)),(start + timedelta(date)))
                self._cr.execute(sql_magasin)
                journees = self._cr.dictfetchall()
                for journee in journees:
                    vals = {
                        'date_journee': start + timedelta(date),
                        'magasin_code': journee['code'],
                        'magasin_lib': journee['name'],
                        'notup_journee_id': self.id,
                        'state': 'notup',
                        }
                    data.append(vals)
            
            self.notup_journee_line_ids = data
                    
        else:
            raise ValidationError('Veuillez vérifier la date de la journée!')
                
        

class NotUpJourneeLine(models.TransientModel):
    _name = 'notup.journee.wizard.line'
    _description = "Detail journee non remontee"
    _rec_name = "date_journee"
    _order = "magasin_code asc"
    
    date_journee = fields.Date(string='Date journée')
    magasin_code = fields.Char(string='Code Magasin')
    magasin_lib = fields.Char(string='Magasin')
    notup_journee_id = fields.Many2one('notup.journee.wizard', string='Journee non remontee')
    state = fields.Selection([
        ('notup', 'Non remontée'),
        ], string='Statut', readonly=True, copy=False, index=True, default='notup')