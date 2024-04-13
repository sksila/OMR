from curses.ascii import US
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class PlanningSlot(models.Model):
    _inherit = 'planning.slot'
    allocated_percentage = fields.Float('Estimated Time (%)')
    allocated_hours = fields.Float('Estimated Hours')