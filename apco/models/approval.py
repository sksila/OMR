from curses.ascii import US
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'
    social_post_id = fields.Many2one('social.post')