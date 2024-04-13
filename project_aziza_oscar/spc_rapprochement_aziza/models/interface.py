# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class InterBrv(models.Model):
    _name = 'inter.brv'
    _description = 'BRV (interface)'
    _rec_name = 'num_brv'

    num_brv = fields.Char('Numéro BRV', required=True, index=True)
    num_cmd = fields.Char('Numéro Commande', index=True)
    date_brv = fields.Datetime('Date BRV', index=True)
    code_site = fields.Char('Code site', index=True)
    code_fournisseur = fields.Char('Code fournisseur', index=True)
    lib_fournisseur = fields.Char('Fournisseur')
    code_article = fields.Char('Code article', index=True)
    lib_article = fields.Char('Article')
    qte_recue = fields.Float('Qté reçue')
    unite_recue = fields.Char('Unité reçue')

    def get_supplier_id(self, code):
        supplier_id = False
        sql_supplier = """
                            SELECT id FROM res_partner 
                            WHERE code = '%s' LIMIT 1;
                    """ % (code)
        self.env.cr.execute(sql_supplier)
        result = self.env.cr.fetchone()
        if result:
            supplier_id = result[0]
        else:
            raise ValidationError(_("Le fournisseur <%s> n'est pas trouvé!"%(code)))
        return supplier_id

    def get_site_id(self, code):
        site_id = False
        sql_site = """
                            SELECT id FROM oscar_site 
                            WHERE code = '%s' LIMIT 1;
                    """ % (code)
        self.env.cr.execute(sql_site)
        result = self.env.cr.fetchone()
        if result:
            site_id = result[0]
        else:
            raise ValidationError(_("Le site <%s> n'est pas trouvé!" % (code)))
        return site_id

    def get_product_id(self, code):
        product_id = False
        sql_product = """
                            SELECT id FROM product_template 
                            WHERE default_code = '%s' LIMIT 1;
                    """ % (code)
        self.env.cr.execute(sql_product)
        result = self.env.cr.fetchone()
        if result:
            product_id = result[0]
        else:
            raise ValidationError(_("L'article <%s> n'est pas trouvé!" % (code)))
        return product_id

    def printProgressBar(self, iteration, total, prefix='', suffix='', decimals=1, length=100, fill='#'):
        """
        Call in a loop to create terminal progress bar
        @params:
            iteration   - Required  : current iteration (Int)
            total       - Required  : total iterations (Int)
            prefix      - Optional  : prefix string (Str)
            suffix      - Optional  : suffix string (Str)
            decimals    - Optional  : positive number of decimals in percent complete (Int)
            length      - Optional  : character length of bar (Int)
            fill        - Optional  : bar fill character (Str)
        """
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        _logger.info("\r%s |%s| %s%% %s", prefix, bar, percent, suffix)
        if iteration == total:
            return

    def create_new_brv_action(self):
        sql_num_brv = """
                        SELECT num_brv,date_brv,num_cmd,code_site,code_fournisseur FROM public.inter_brv GROUP BY num_brv,date_brv,num_cmd,code_site,code_fournisseur;
                    """
        self.env.cr.execute(sql_num_brv)
        result = self.env.cr.dictfetchall()
        len_brv = len(result)
        i = 0
        l = 0
        for line in result:
            i += 1
            vals = {
                'name': line['num_brv'],
                'num_cmd': line['num_cmd'],
                'date_brv': str(line['date_brv']) or datetime.now(),
                'supplier_id': self.get_supplier_id(line['code_fournisseur']),
                'site_id': self.get_site_id(line['code_site']),
                'state': 'new',
            }
            brv = self.env['oscar.brv'].create(vals)
            if brv:
                sql_details_brv = """
                                SELECT * FROM public.inter_brv WHERE num_brv = '%s';
                            """ % (line['num_brv'])
                self.env.cr.execute(sql_details_brv)
                details = self.env.cr.dictfetchall()
                obj = ''
                for detail in details:
                    l += 1
                    vals_details = (
                        self.get_product_id(detail['code_article']),
                        detail['qte_recue'],
                        detail['unite_recue'],
                        brv.id
                    )
                    obj = obj + str(vals_details) + ','
                    _logger.info("LINE %s : INSERT BRV # %s | PRODUCT # %s", l, line['num_brv'], detail['code_article'])
                insert_details_brv = """
                                    INSERT INTO oscar_brv_line (product_id,qte_recue,unite_recue,brv_id) VALUES %s;
                                """ % (obj[:-1].replace("None", "NULL"))
                self.env.cr.execute(insert_details_brv)
            self.printProgressBar(i, len_brv, prefix='Progress:', suffix='Complete', length=50)


class InterBL(models.Model):
    _name = 'inter.bl'
    _description = 'BL (interface)'
    _rec_name = 'num_bl'

    num_bl = fields.Char('Numéro BL', required=True, index=True)
    date_bl = fields.Date('Date BL', index=True)
    code_societe = fields.Char('Code société', index=True)
    lib_societe = fields.Char('Société')
    code_client = fields.Char('Code client', index=True)
    lib_client = fields.Char('Client')
    adresse_client = fields.Char('Adresse client')
    code_article = fields.Char('Code article', index=True)
    lib_article = fields.Char('Article')
    qte_livree = fields.Float('Qté livrée')
    unite_livree = fields.Char('Unité livrée')

    def get_site(self, code_extern, code_fr):
        site_id = False
        sql_transcodage = """
                                SELECT code_interne FROM transcodage_site 
                                WHERE code_externe = '%s' AND code_fournisseur = '%s' LIMIT 1;
                        """ % (code_extern, code_fr)
        self.env.cr.execute(sql_transcodage)
        result = self.env.cr.fetchone()
        if result:
            sql_site = """
                        SELECT id FROM oscar_site 
                        WHERE code = '%s' LIMIT 1;
                """ % (result[0])
            self.env.cr.execute(sql_site)
            site_id = self.env.cr.fetchone()
        return site_id[0]

    def get_fournisseur(self, code_extern):
        fournisseur_id = False
        sql_transcodage = """
                                SELECT code_interne FROM transcodage_fournisseur 
                                WHERE code_externe = '%s' LIMIT 1;
                        """ % (code_extern)
        self.env.cr.execute(sql_transcodage)
        result = self.env.cr.fetchone()
        if result:
            sql_site = """
                        SELECT id FROM res_partner 
                        WHERE code = '%s' LIMIT 1;
                """ % (result[0])
            self.env.cr.execute(sql_site)
            fournisseur_id = self.env.cr.fetchone()
        return fournisseur_id[0]

    def get_article(self, code_extern, code_fr):
        article_id = False
        sql_transcodage = """
                                SELECT code_interne FROM transcodage_article 
                                WHERE code_externe = '%s' AND code_fournisseur = '%s' LIMIT 1;
                        """ % (code_extern, code_fr)
        self.env.cr.execute(sql_transcodage)
        result = self.env.cr.fetchone()
        if result:
            sql_site = """
                        SELECT id FROM product_template 
                        WHERE default_code = '%s' LIMIT 1;
                """ % (result[0])
            self.env.cr.execute(sql_site)
            article_id = self.env.cr.fetchone()
        return article_id[0]

    def create_new_bl_action(self):
        four_id = self.get_fournisseur(self.code_societe)
        client_id = self.get_site(self.code_client, self.code_societe)
        article_id = self.get_article(self.code_article, self.code_societe)
        create = False
        update = False
        sql_site = """
                        SELECT id FROM oscar_bl 
                        WHERE name = '%s' LIMIT 1;
                """ % (self.num_bl)
        self.env.cr.execute(sql_site)
        bl_id = self.env.cr.fetchone()
        if bl_id:
            update = True
        else:
            create = True
        if create:
            vals = {
                'name': self.num_bl,
                'date_bl': datetime.combine(self.date_bl, datetime.now().time()),
                'client_id': client_id,
                'partner_id': four_id,
                'state': 'new',
                'bl_line_ids': [(0, 0, {
                    'product_id': article_id,
                    'qte_livree': self.qte_livree,
                    'unite_livree': self.unite_livree,
                })],
            }
            self.env['oscar.bl'].create(vals)
        elif update:
            vals = {
                'product_id': article_id,
                'qte_livree': self.qte_livree,
                'unite_livree': self.unite_livree,
            }
            bl = self.env['oscar.bl'].browse(bl_id)
            bl_line = bl.bl_line_ids.filtered(lambda bl_line: bl_line.product_id.id == article_id)
            if bl_line:
                bl_line.write(vals)
            else:
                bl.write({'bl_line_ids': [(0, 0, vals)]})


class ZInvoice(models.Model):
    _name = 'zinvoice'
    _description = 'Invoice (interface)'
    _rec_name = 'ZINVOICE_CODE'

    ZINVOICE_CODE = fields.Char('Code', required=True, index=True)
    BRANCH_CODE = fields.Char('Branch code')
    PARTNER_CODE = fields.Char('Partner code', required=True, index=True)
    AMOUNT = fields.Float('Amount')
    THEDATE = fields.Datetime('Date')
    ROLE_CODE = fields.Char('Role Code')
    PERSON_CODE = fields.Char('Person Code')
    DESCRIPTION = fields.Text('Description')
    DISCOUNT = fields.Float('Discount')
    CANCELED = fields.Boolean('Canceled')
    PROGRESSLEVEL = fields.Integer('Progress Level')
    TRACKINGKEY = fields.Char('Tracking Key')
    SORDER_CODE = fields.Char('Sorder Code')
    CLOSED = fields.Boolean('Closed')
    USER_CODE = fields.Char('User code')
    ZINVOICE_LINES = fields.One2many('zinvoice_line', 'ZINVOICE_ID', string='Invoice Lines')

    _sql_constraints = [
        ("ZINVOICE_CODE_UNIQ", 'UNIQUE ("ZINVOICE_CODE")', "You can not have two invoices with the same code !")
    ]


class ZInvoiceLine(models.Model):
    _name = 'zinvoice_line'
    _description = 'Invoice Lines (interface)'

    ZINVOICE_CODE = fields.Char('Code Invoice', index=True)
    ZINVOICE_LINE_NUMBER = fields.Char('Line number', required=True, index=True)
    PRODUCT_CODE = fields.Char('Product code')
    BARCODE = fields.Char('Barcode')
    NAME = fields.Char('Name')
    QUANTITY = fields.Float('Quantity')
    DISCOUNT = fields.Float('Discount')
    FREEGOODLINE = fields.Boolean('Free')
    UNITPRICE = fields.Float('Unit price')
    ZINVOICE_ID = fields.Many2one('zinvoice', string='Invoice', index=True, ondelete='cascade')

    def get_site(self, code_extern, code_fr):
        site_id = False
        sql_transcodage = """
                                SELECT code_interne FROM transcodage_site
                                WHERE code_externe = '%s' AND code_fournisseur = '%s' LIMIT 1;
                        """ % (code_extern, code_fr)
        self.env.cr.execute(sql_transcodage)
        result = self.env.cr.fetchone()
        if result:
            sql_site = """
                        SELECT id FROM oscar_site
                        WHERE code = '%s' LIMIT 1;
                """ % (result[0])
            self.env.cr.execute(sql_site)
            site_id = self.env.cr.fetchone()
        return site_id[0]

    def get_fournisseur(self, code_extern):
        fournisseur_id = False
        sql_transcodage = """
                                SELECT code_interne FROM transcodage_fournisseur 
                                WHERE code_externe = '%s' LIMIT 1;
                        """ % (code_extern)
        self.env.cr.execute(sql_transcodage)
        result = self.env.cr.fetchone()
        if result:
            sql_site = """
                        SELECT id FROM res_partner 
                        WHERE code = '%s' LIMIT 1;
                """ % (result[0])
            self.env.cr.execute(sql_site)
            fournisseur_id = self.env.cr.fetchone()
        return fournisseur_id[0]

    def get_article(self, code_extern, code_fr):
        article_id = False
        sql_transcodage = """
                                SELECT code_interne FROM transcodage_article 
                                WHERE code_externe = '%s' AND code_fournisseur = '%s' LIMIT 1;
                        """ % (code_extern, code_fr)
        self.env.cr.execute(sql_transcodage)
        result = self.env.cr.fetchone()
        if result:
            sql_site = """
                        SELECT id FROM product_template 
                        WHERE default_code = '%s' LIMIT 1;
                """ % (result[0])
            self.env.cr.execute(sql_site)
            article_id = self.env.cr.fetchone()
        return article_id[0]

    def create_new_bl_action(self):
        print("self.ZINVOICE_ID : ", self.ZINVOICE_ID)
        four_id = self.get_fournisseur(self.ZINVOICE_ID.PARTNER_CODE)
        client_id = self.get_site(self.ZINVOICE_ID.BRANCH_CODE, self.ZINVOICE_ID.PARTNER_CODE)
        article_id = self.get_article(self.PRODUCT_CODE, self.ZINVOICE_ID.PARTNER_CODE)
        create = False
        update = False
        sql_bl = """
                        SELECT id FROM oscar_bl 
                        WHERE name = '%s' LIMIT 1;
                """ % (self.ZINVOICE_CODE)
        self.env.cr.execute(sql_bl)
        bl_id = self.env.cr.fetchone()
        if bl_id:
            update = True
        else:
            create = True
        if create:
            vals = {
                'name': self.ZINVOICE_CODE,
                'date_bl': self.ZINVOICE_ID.THEDATE or datetime.now(),
                'client_id': client_id,
                'partner_id': four_id,
                'state': 'new',
                'bl_line_ids': [(0, 0, {
                    'product_id': article_id,
                    'qte_livree': self.QUANTITY,
                    # 'unite_livree': self.unite_livree,
                })],
            }
            self.env['oscar.bl'].create(vals)
        elif update:
            vals = {
                'product_id': article_id,
                'qte_livree': self.QUANTITY,
                # 'unite_livree': self.unite_livree,
            }
            bl = self.env['oscar.bl'].browse(bl_id)
            bl_line = bl.bl_line_ids.filtered(lambda bl_line: bl_line.product_id.id == article_id)
            if bl_line:
                bl_line.write(vals)
            else:
                bl.write({'bl_line_ids': [(0, 0, vals)]})


class ZPerson(models.Model):
    _name = 'zperson'
    _description = 'ZPerson (interface)'

    ZPERSON_CODE = fields.Char('Code Person', index=True)
    NAME = fields.Char('Name')
    FIRSTNAME = fields.Char('First Name')
    PHONE = fields.Char('Phone')
    LOGIN = fields.Char('Login')
    PASSWORD = fields.Char('Password')
    HOLD = fields.Boolean('Hold')
    BRANCH_CODE = fields.Char('Branch code')


class CompanyPartnerBranche(models.Model):
    _name = 'company_partner_branch'
    _description = 'Company Branch (interface)'

    COMPANY_CODE = fields.Char('Company code', index=True)
    PARTNER_CODE = fields.Char('Partner code', index=True)
    BRANCH_CODE = fields.Char('Branch code', index=True)
