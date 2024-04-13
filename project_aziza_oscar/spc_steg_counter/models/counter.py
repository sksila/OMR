# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CounterSteg(models.Model):
    _name = 'oscar.counter.steg'
    _description = 'Compteur STEG'
    _rec_name = "index"

    # region Fields Declaration
    name = fields.Char('Nom de compteur', required=True, index=True)
    index = fields.Char('Index de compteur', index=True, required=True)
    reading_counter_ids = fields.Many2many('oscar.reading.counter.steg','oscar_reading_counter_steg_rel', 'counter_id', 'reading_id', string='Relevés compteur')
    magasin_id = fields.Many2one('oscar.site', string='Magasin', index=True)
    active = fields.Boolean(string='Activé', default=True)
    # endregion

