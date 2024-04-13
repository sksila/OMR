# -*- coding: utf-8 -*-

from num2words import num2words
from odoo import api, fields, models, _


class Versement(models.Model):
    _inherit = "oscar.versement"

    montant_lettre = fields.Char(string="Montant en lettre", required=False, compute="amount_to_words" )

    def lettrer(self, montant):

        total_lettre = ''
        apres_virgule = ''
        split_num = str(montant).split('.')
        int_part = int(split_num[0])
        # si dec / 10 <1 ==> *100
        # si dec /10 <10 ==> * 10
        # si dec /10 >10 ==> * 1

        decimal_part = int(split_num[1])
        if int(split_num[1][0]) != 0:
            if (decimal_part / 10) < 1:
                decimal_part = decimal_part * 100
            elif (decimal_part / 10) < 10:
                decimal_part = decimal_part * 10

        total_lettre = num2words(int_part, lang='fr').title()

        if self.currency_id.name == 'TND':
            total_lettre += ' Dinars'
            apres_virgule = ' Millimes'
        elif self.currency_id.name == 'EUR':
            total_lettre += ' Euros'
            apres_virgule = ' Centimes'

        if decimal_part:
            total_lettre += ' et ' + num2words(decimal_part, lang='fr') + apres_virgule
        else:
            return total_lettre

        return total_lettre

    @api.depends('montant_versement','reste_a_verser','state')
    def amount_to_words(self):
        if self.state == 'draft':
            self.montant_lettre = self.lettrer(self.reste_a_verser)
        else:
            self.montant_lettre = self.lettrer(self.montant_versement)