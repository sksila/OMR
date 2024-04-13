from odoo import api, fields, models



class ArticleModifWizard(models.TransientModel):
    _name="oscar.sav.modif.article.wizard"
    _description = "Modifier un article" 
    
    @api.model
    def _get_reclamation(self):
        return self.env['oscar.sav.claim'].browse(self.env.context.get('active_id'))
    
    reclamation_id = fields.Many2one('oscar.sav.claim',default=_get_reclamation)
    product_id = fields.Many2one('product.template',string='Article', domain=[('is_sav_product', '=', True)],required=True)
    
    @api.multi
    def set_name_article(self):
        self.reclamation_id.write({'product_id' : self.product_id.id})
