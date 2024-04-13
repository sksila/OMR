# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models


class RowDisplayColumns(models.TransientModel):
    _name = 'row.columns.display'
    _description = 'Wizard pour choisir les colonnes a afficher par ligne'

    columns_ids = fields.Many2many('survey.label', string="Columns to display per row")
    line = fields.Char('Line')

    def add_columns(self):
        current_row = self.env.context.get('active_id')
        display_cols_text = display_cols = ''
        for rec in self.columns_ids:
            display_cols_text = display_cols_text + rec.value + ','
            display_cols = display_cols + str(rec.id) + ','
        display_cols_text = display_cols_text[:-1] #remove lase comma
        display_cols = display_cols[:-1]
        self.env['survey.label'].search([('id', '=', current_row)]).write({
            'display_cols_text' : display_cols_text,
            'display_cols' : display_cols
        })

