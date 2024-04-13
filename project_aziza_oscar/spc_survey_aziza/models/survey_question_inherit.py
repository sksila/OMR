import logging

from odoo import fields, models, api


class SpcSurveyAzizaQuestion (models.Model):
    _inherit = 'survey.question'

    site = fields.Boolean('Apply per site')
    apply_per = fields.Selection([
        ('site', 'Site'),
        ('user', 'Utilisateur'),
        ], string='Appliquer par :')
    product_type_ids = fields.Many2many('spc_product.type', 'rel_product_type_ids_question_aziza', string="Type")
    is_product_model = fields.Boolean(compute='get_product_type_id')
    column_name = fields.Many2one('ir.model.fields', string="Colonne concernée")
    is_plano_facing_model = fields.Boolean(compute='check_if_model_is_plano_facing')
    plano_facing_category_id = fields.Many2one('product.category')
    plano_facing_family = fields.Char('Family')

    @api.multi
    @api.depends('model_id')
    def check_if_model_is_plano_facing(self):
        if self.model_id.id == self.env['ir.model'].search([('model', '=', 'inter.plano_facing')]).id:
            self.is_plano_facing_model = True

    @api.multi
    @api.depends('model_id')
    def get_product_type_id(self):
        if self.model_id.id == self.env['ir.model'].search([('model','=','product.template')]).id:
            self.is_product_model = True
        else:
            self.is_product_model = False

    def get_products_by_article_site(self,article_types,site,token):
        survey_session_info = self.env['survey.user_input'].search([('token','=',token)]).survey_session_info_id
        products_list_ids = []
        if not article_types and not site:
            return products_list_ids
        elif not article_types and site:
            for rec in self.env['spc_product.detail'].filtered(lambda line: survey_session_info.site_id.id in line.site_ids.ids):
                products_list_ids.append(rec.product_id.id)
            return self.env['product.template'].search([('id','in',products_list_ids)])
        elif article_types and not site:
            for rec in self.env['spc_product.detail'].search([('product_type','in',article_types.ids)]):
                products_list_ids.append(rec.product_id.id)
            return self.env['product.template'].search([('id','in',products_list_ids)])
        elif article_types and site:
            for rec in self.env['spc_product.detail'].search([('product_type','in',article_types.ids)]).filtered(lambda line: survey_session_info.site_id.id in line.site_ids.ids):
                products_list_ids.append(rec.product_id.id)
            return self.env['product.template'].search([('id','in',products_list_ids)])
        else:
            return products_list_ids

    def get_records_by_site(self, model_id, site_column, site, token):
        records = []
        survey_session_info = self.env['survey.user_input'].search([('token', '=', token)]).survey_session_info_id
        if site:
            records = self.env[model_id.model].search([(site_column.name, '=', survey_session_info.site_id.code)])
        return records

    def get_records_by_categ_element_level(self, model_id, token):
        records = []
        element_level = ""
        survey_session_info = self.env['survey.user_input'].search([('token', '=', token)]).survey_session_info_id
        site_id = survey_session_info.site_id
        for rec in site_id.plano_facing_site_ids:
            if rec.category_name == self.plano_facing_family:
                element_level = rec.element_level
                break
        records = self.env[model_id.model].search([('category_name', '=', self.plano_facing_family),('element_level', '=', element_level)])
        return records

    def get_records_by_user(self, model_id, eq_column, applied_per_user, token):
        records = []
        survey_session_info = self.env['survey.user_input'].search([('token', '=', token)]).survey_session_info_id
        if applied_per_user:
            records = self.env[model_id.model].search([(eq_column.name, '=', survey_session_info.auditor_id.id)])
        return records


