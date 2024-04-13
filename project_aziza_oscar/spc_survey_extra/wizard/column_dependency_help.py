# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models


class ColumnDependencyHelp(models.TransientModel):
    _name = 'column.dependency.help'
