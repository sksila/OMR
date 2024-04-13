# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
import logging

_logger = logging.getLogger(__name__)


class Fournisseur(models.Model):
    _name = "oscar.fournisseur.inter"
    _description = "Table Fournisseur Gold"

    code = fields.Char('Code', required=True, index=True)
    name = fields.Char('Nom', required=True)
    code_article = fields.Char("Code Article", required=True, index=True)
    lib_article = fields.Char("Nom d'article")

    def planned_supplier_integration(self):
        _logger.info("______________________Insert supplier if not exists in table res_partner_________________________",exc_info=True)
        sql_difference_data = """
                SELECT DISTINCT ON (code) code,name FROM oscar_fournisseur_inter fi 
                WHERE NOT EXISTS (SELECT 1 FROM res_partner rp WHERE rp.code = fi.code AND rp.code IS NOT NULL);
        """
        self.env.cr.execute(sql_difference_data)
        result = self.env.cr.fetchall()
        for fr in result:

            vals = {
                'code': fr[0],
                'name': fr[1],
                'type': 'contact',
                'supplier': True
            }
            print(vals)
            self.env['res.partner'].create(vals)
        sql_insert_fr_product = """
                INSERT INTO product_template_res_partner_rel (product_template_id,res_partner_id) 
                SELECT (SELECT id FROM product_template pt WHERE pt.default_code = fi.code_article),
                (SELECT id FROM res_partner rp WHERE rp.code = fi.code) 
                FROM (SELECT code, code_article FROM oscar_fournisseur_inter) fi 
                ON CONFLICT (product_template_id,res_partner_id) DO NOTHING;
                """
        self.env.cr.execute(sql_insert_fr_product)
        self.env.cr.commit()



class InterProduct(models.Model):
    _name = "inter.product"
    _description = "Article (Table d'interface)"

    code = fields.Char('Code article', required=True)
    name = fields.Char('libellé', required=True)
    barcode = fields.Char(string='Code Barre')
    code_category = fields.Char('Code categorie')
    category = fields.Char('Categorie')  # we will use family instead
    code_family = fields.Char('Code Famille')
    family = fields.Char('Famille')  # many2one object : product_category
    code_subfamily = fields.Char('Code sous Famille')
    subfamily = fields.Char('Sous Famille')  # many2one object : product_category
    appro = fields.Char('Identifiant Appro')
    spot = fields.Char('Spot')  # many2one object : oscar_product_spot

    def planned_product_integration(self):
        _logger.info("______________________Integration Product__________________________", exc_info=True)

        sql_category = """
            INSERT INTO product_category(name,code) SELECT category,code_category 
            FROM inter_product WHERE code_category IS NOT NULL GROUP BY category,code_category ON CONFLICT (code) DO NOTHING;
        """

        self.env.cr.execute(sql_category)
        self.env.cr.commit()

        sql_family = """
            INSERT INTO product_category(name,code,parent_id) 
            SELECT family,code_family,(SELECT id FROM product_category pc WHERE pc.code = ip.code_category lIMIT 1) as category_id 
            FROM inter_product ip WHERE code_family IS NOT NULL GROUP BY family,code_family,category_id ON CONFLICT (code) DO NOTHING;
                """

        self.env.cr.execute(sql_family)
        self.env.cr.commit()

        sql_sub_family = """
            INSERT INTO product_category(name,code,parent_id) 
            SELECT subfamily,code_subfamily,(SELECT id FROM product_category pc WHERE pc.code = ip.code_family lIMIT 1) as family_id 
            FROM inter_product ip WHERE code_subfamily IS NOT NULL GROUP BY subfamily,code_subfamily,family_id ON CONFLICT (code) DO NOTHING;
                """

        self.env.cr.execute(sql_sub_family)
        self.env.cr.commit()

        sql = '''
        INSERT INTO product_template(name, default_code, categ_id, spot_id, type, uom_id, uom_po_id, active) 
        SELECT ip.name, ip.code, (SELECT id FROM product_category pc WHERE pc.code = ip.code_subfamily or pc.code = ip.code_family ORDER BY pc.id DESC lIMIT 1),(SELECT id FROM oscar_product_spot ops WHERE ops.name = ip.spot lIMIT 1),'consu',1,1,True FROM inter_product ip 
        ON CONFLICT (default_code) DO UPDATE SET 
            to_update = 1
        '''
        self.env.cr.execute(sql)
        self.env.cr.commit()

        to_update_records = '''
        UPDATE product_template
        SET name = ip.name,
            categ_id = (SELECT id FROM product_category pc WHERE pc.code = ip.code_subfamily or pc.code = ip.code_family ORDER BY pc.id DESC lIMIT 1),
            spot_id = (SELECT id FROM oscar_product_spot ops WHERE ops.name = ip.spot lIMIT 1),
            to_update = 0
        FROM inter_product ip
        WHERE ip.code = default_code and to_update = 1
        '''
        self.env.cr.execute(to_update_records)
        self.env.cr.commit()

        sql_appro = """
                    INSERT INTO approvisionneur_product_rel(product_template_id,res_users_id) 
                    SELECT (SELECT id FROM product_template pt WHERE pt.default_code = ip.code lIMIT 1) as product_template_id,(SELECT id FROM res_users ru WHERE ru.login = ip.appro lIMIT 1) as res_user_id 
                    FROM inter_product ip WHERE appro IS NOT NULL GROUP BY code,appro ON CONFLICT (product_template_id,res_users_id) DO NOTHING;
                        """
        print("sql_appro")
        logging.info("sql_appro")
        self.env.cr.execute(sql_appro)
        self.env.cr.commit()
        print("END : sql_appro")
        logging.info("END : sql_appro")

    def planned_product_types_integration(self):
        clean_spc_product_detail = '''
            DELETE FROM spc_product_detail WHERE product_id IS NULL;
        '''
        self.env.cr.execute(clean_spc_product_detail)
        self.env.cr.commit()

        # PlanoFacing
        plano_facing_id = self.env.ref('spc_product.planogramme_type').id
        plano_sql = '''
                            INSERT INTO spc_product_detail(product_type,product_id)
                            SELECT  %s,
                                   (SELECT id from product_template p WHERE p.default_code = ipf.code_article)
                            FROM inter_plano_facing ipf
                            ON CONFLICT (product_type,product_id) DO NOTHING;
                            ''' % plano_facing_id
        self.env.cr.execute(plano_sql)
        self.env.cr.commit()

        # update plano cols

        update_plano_cols = '''
                    UPDATE product_template
                    SET facing_prevue = ipf.facing,
                        marque = ipf.marque,
                        niveau = ipf.niveau,
                        classement = ipf.classement
                    FROM inter_plano_facing ipf
                    WHERE default_code = ipf.code_article;
                '''
        self.env.cr.execute(update_plano_cols)


        # delete_all_plano_facing_rows_from_rel_sites_product_details
        delete_all_plano_facing_rows_from_rel_sites_product_details = '''
                    DELETE FROM rel_sites_product_details WHERE EXISTS (
                        SELECT d.id FROM spc_product_detail d
                        WHERE d.product_type = %s and spc_product_detail_id = d.id
                    )
                ''' % plano_facing_id
        self.env.cr.execute(delete_all_plano_facing_rows_from_rel_sites_product_details)
        self.env.cr.commit()

        # delete_not_keeped_rows_plano_facing = '''
        #                                             DELETE FROM rel_sites_product_details
        #                                             WHERE NOT EXISTS (
        #                                                 SELECT d.id AS detail_id,o.id AS site_id FROM inter_plano_facing i
        #                                                 JOIN product_template p ON p.default_code = i.code_article
        #                                                 JOIN spc_product_detail d ON d.product_id = p.id and d.product_type = %s
        #                                                 JOIN oscar_site o ON o.code = i.code_site
        #                                                 WHERE spc_product_detail_id = d.id AND oscar_site_id = o.id
        #                                             )
        #                                             ''' % plano_facing_id
        # self.env.cr.execute(delete_not_keeped_rows_plano_facing)

        # in plano we dont need sites it's applied for all
        # plano_sites_sql = '''
        #                     INSERT INTO rel_sites_product_details(spc_product_detail_id,oscar_site_id)
        #                     SELECT (SELECT id from spc_product_detail spd WHERE spd.product_type = %s AND spd.product_id = (select id from product_template p where p.default_code = ipf.code_article) ),
        #                            (SELECT id from oscar_site os WHERE os.code = ipf.code_site)
        #                     FROM inter_plano_facing ipf
        #                     ON CONFLICT (spc_product_detail_id,oscar_site_id) DO NOTHING;
        #                     ''' % plano_facing_id
        # self.env.cr.execute(plano_sites_sql)

        # top_articles
        top_articles_id = self.env.ref('spc_product.top_articles_type').id
        top_articles_sql = '''
            INSERT INTO spc_product_detail(product_type,product_id)
            SELECT  %s,
                    (SELECT id from product_template p WHERE p.default_code = ita.code_article)
            FROM inter_top_articles ita
            ON CONFLICT (product_type,product_id) DO NOTHING;
            ''' % top_articles_id
        self.env.cr.execute(top_articles_sql)
        self.env.cr.commit()

        # delete_all_top_articles_rows_from_rel_sites_product_details
        delete_all_top_articles_rows_from_rel_sites_product_details = '''
            DELETE FROM rel_sites_product_details WHERE EXISTS (
                SELECT d.id FROM spc_product_detail d
                WHERE d.product_type = %s and spc_product_detail_id = d.id
            )
        ''' % top_articles_id
        self.env.cr.execute(delete_all_top_articles_rows_from_rel_sites_product_details)
        self.env.cr.commit()

        # sghaier wanted : delete not keeped rows in top_articles
        # delete_not_keeped_rows_top_articles = '''
        #             DELETE FROM rel_sites_product_details
        #             WHERE NOT EXISTS (
        #                 SELECT d.id AS detail_id,o.id AS site_id FROM inter_top_articles i
        #                 JOIN product_template p ON p.default_code = i.code_article
        #                 JOIN spc_product_detail d ON d.product_id = p.id and d.product_type = %s
        #                 JOIN oscar_site o ON o.code = i.code_site
        #                 WHERE spc_product_detail_id = d.id AND oscar_site_id = o.id
        #             )
        #             ''' % top_articles_id
        # self.env.cr.execute(delete_not_keeped_rows_top_articles)

        top_articles_sites_sql = '''
            INSERT INTO rel_sites_product_details(spc_product_detail_id,oscar_site_id)
            SELECT (SELECT id from spc_product_detail spd WHERE spd.product_type = %s AND spd.product_id = (select id from product_template p where p.default_code = ita.code_article) ),
                   (SELECT id from oscar_site os WHERE os.code = ita.code_site)
            FROM inter_top_articles ita
            ON CONFLICT (spc_product_detail_id,oscar_site_id) DO NOTHING;
            ''' % top_articles_id
        self.env.cr.execute(top_articles_sites_sql)
        self.env.cr.commit()

        # articles_aleatoires
        articles_aleatoires_id = self.env.ref('spc_product.articles_aleatoires_type').id
        articles_aleatoires_sql = '''
            INSERT INTO spc_product_detail(product_type,product_id)
            SELECT  %s,
                    (SELECT id from product_template p WHERE p.default_code = iaa.code_article)
            FROM inter_articles_aleatoires iaa
            ON CONFLICT (product_type,product_id) DO NOTHING;
            ''' % articles_aleatoires_id
        self.env.cr.execute(articles_aleatoires_sql)
        self.env.cr.commit()

        delete_all_articles_aleatoires_rows_from_rel_sites_product_details = '''
                    DELETE FROM rel_sites_product_details WHERE EXISTS (
                        SELECT d.id FROM spc_product_detail d
                        WHERE d.product_type = %s and spc_product_detail_id = d.id
                    )
                ''' % articles_aleatoires_id
        self.env.cr.execute(delete_all_articles_aleatoires_rows_from_rel_sites_product_details)
        self.env.cr.commit()

        # delete_not_keeped_rows_articles_aleatoires = '''
        #                     DELETE FROM rel_sites_product_details
        #                     WHERE NOT EXISTS (
        #                         SELECT d.id AS detail_id,o.id AS site_id FROM inter_articles_aleatoires i
        #                         JOIN product_template p ON p.default_code = i.code_article
        #                         JOIN spc_product_detail d ON d.product_id = p.id and d.product_type = %s
        #                         JOIN oscar_site o ON o.code = i.code_site
        #                         WHERE spc_product_detail_id = d.id AND oscar_site_id = o.id
        #                     )
        #                     ''' % articles_aleatoires_id
        # self.env.cr.execute(delete_not_keeped_rows_articles_aleatoires)

        articles_aleatoires_sites_sql = '''
            INSERT INTO rel_sites_product_details(spc_product_detail_id,oscar_site_id)
            SELECT (SELECT id from spc_product_detail spd WHERE spd.product_type = %s AND spd.product_id = (select id from product_template p where p.default_code = iaa.code_article) ),
                   (SELECT id from oscar_site os WHERE os.code = iaa.code_site)
            FROM inter_articles_aleatoires iaa
            ON CONFLICT (spc_product_detail_id,oscar_site_id) DO NOTHING;
            ''' % articles_aleatoires_id
        self.env.cr.execute(articles_aleatoires_sites_sql)
        self.env.cr.commit()

        # article_promo
        article_promo_id = self.env.ref('spc_product.promo_type').id
        article_promo_sql = '''
            INSERT INTO spc_product_detail(product_type,product_id)
            SELECT  %s,
                    (SELECT id from product_template p WHERE p.default_code = iap.code_article)
            FROM inter_article_promo iap
            ON CONFLICT (product_type,product_id) DO NOTHING;
            ''' % article_promo_id
        self.env.cr.execute(article_promo_sql)
        self.env.cr.commit()


        #update prix_promo
        update_prix_promo = '''
            UPDATE product_template
            SET list_price = iap.prix_promo::real
            from inter_article_promo iap
            WHERE default_code = iap.code_article;
        '''
        self.env.cr.execute(update_prix_promo)
        self.env.cr.commit()

        # delete_all_article_promo_rows_from_rel_sites_product_details
        delete_all_article_promo_rows_from_rel_sites_product_details = '''
                            DELETE FROM rel_sites_product_details WHERE EXISTS (
                                SELECT d.id FROM spc_product_detail d
                                WHERE d.product_type = %s and spc_product_detail_id = d.id
                            )
                        ''' % article_promo_id
        self.env.cr.execute(delete_all_article_promo_rows_from_rel_sites_product_details)
        self.env.cr.commit()



        # delete_not_keeped_rows_article_promo = '''
        #                             DELETE FROM rel_sites_product_details
        #                             WHERE NOT EXISTS (
        #                                 SELECT d.id AS detail_id,o.id AS site_id FROM inter_article_promo i
        #                                 JOIN product_template p ON p.default_code = i.code_article
        #                                 JOIN spc_product_detail d ON d.product_id = p.id and d.product_type = %s
        #                                 JOIN oscar_site o ON o.code = i.code_site
        #                                 WHERE spc_product_detail_id = d.id AND oscar_site_id = o.id
        #                             )
        #                             ''' % article_promo_id
        # self.env.cr.execute(delete_not_keeped_rows_article_promo)

        article_promo_sites_sql = '''
            INSERT INTO rel_sites_product_details(spc_product_detail_id,oscar_site_id)
            SELECT (SELECT id from spc_product_detail spd WHERE spd.product_type = %s AND spd.product_id = (select id from product_template p where p.default_code = iap.code_article) ),
                    (SELECT id from oscar_site os WHERE os.code = iap.code_site)
            FROM inter_article_promo iap
            ON CONFLICT (spc_product_detail_id,oscar_site_id) DO NOTHING;
            ''' % article_promo_id
        self.env.cr.execute(article_promo_sites_sql)
        self.env.cr.commit()

class PlanoFacingInterface(models.Model):
    _name = "inter.plano_facing"
    _description = "Plano Facing (Table d'interface)"

    code_article = fields.Char("Code Article")
    code_sousfamille = fields.Char("Code sous Famille")
    sous_famille = fields.Char("Sous Famille")
    name = fields.Char("Article")
    element_level = fields.Char('Plano type')
    facing = fields.Char("Facing")
    # code_site = fields.Char("Code site")

    marque = fields.Char('Marque')
    niveau = fields.Char('Niveau')
    classement = fields.Char('Classement')

    category_name = fields.Char('Plano category')

class TopArticlesInterface(models.Model):
    _name = "inter.top_articles"
    _description = "Top articles (Table d'interface)"

    code_article = fields.Char("Code Article")
    name = fields.Char("Article")
    stock_min = fields.Char("Stock Min")
    code_site = fields.Char("Code site")
    lib_site = fields.Char("Site")


class ArticlesAleatoiresInterface(models.Model):
    _name = "inter.articles_aleatoires"
    _description = "Articles Aleatoires (Table d'interface)"

    code_article = fields.Char("Code Article")
    name = fields.Char("Article")
    code_site = fields.Char("Code site")
    lib_site = fields.Char("Site")


class PromoInterface(models.Model):
    _name = "inter.article_promo"
    _description = "Articles Promo (Table d'interface)"

    code_article = fields.Char("Code Article")
    nature = fields.Char("Nature")
    name = fields.Char("Article")
    type_article = fields.Char("Type d'article")
    prix_promo = fields.Char('Prix promo')
    code_site = fields.Char("Code site")
    lib_site = fields.Char("Site")
