from curses.ascii import US
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class SocialPost(models.Model):
    _inherit = 'social.post'
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pendingapproval', 'Pending Approval'),
        ('scheduled', 'Scheduled'),
        ('posting', 'Posting'),
        ('posted', 'Approved'),('refuse','Refused')],
        string='Status', default='draft', readonly=True, required=True,
        help="The post is considered as 'Posted' when all its sub-posts (one per social account) are either 'Failed' or 'Posted'")
    
    approval_id = fields.Many2one('approval.request','Related Approval')
    

    def request_approval(self):
        if not self.approval_id:
            approval = self.env['approval.request'].sudo().create({
                'name': 'Approval For Post ' + self.message,
                'request_owner_id': self.env.user.id,
                'social_post_id': self.id,
                'category_id': self.env.ref('apco.approval_social_post_category').id
            })
            approval.action_confirm()
            self.approval_id = approval.id
        
        self.write({"state": "pendingapproval"})

    def refuse(self):
        self.write({"state": "refuse"})

    def action_draft(self):
        self.write({"state": "draft"})