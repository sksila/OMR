# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    dispatch_approbateurs = fields.Many2many(comodel_name='res.users', relation="users", column1="dispatch_approbateurs",
                                           culomn2="user_id", string="Approbateurs dispatch")