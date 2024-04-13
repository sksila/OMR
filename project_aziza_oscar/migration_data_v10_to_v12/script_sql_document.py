import psycopg2
import psycopg2.extensions
import psycopg2.extras
import xmlrpc.client
import logging
logging.basicConfig(format='Date-Time : %(asctime)s : Line No. : %(lineno)d - %(message)s', level = logging.INFO)
_logger = logging.getLogger(__name__)


try:
    connection_10 = psycopg2.connect(user="odoo", password="odoo", host="127.0.0.1", port="5432", database="aziza_backup_17_09")
    cursor_10 = connection_10.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor_10.execute('SELECT name, type, user_id, date_insertion,magasin_id,numero_piece, date_piece,total_ht,total_ttc,fournisseur,state,code_magasin,code_fournisseur,state FROM document_aziza')
    records_10 = cursor_10.fetchall()

    url_db1 = "http://localhost-10:8070"
    db_1 = "aziza_backup_17_09"
    username_db_1 = "admin"
    password_db_1 = "Spectrum@20$20$"

    common_10 = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url_db1))
    models_10 = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url_db1))
    url_db2 = "http://localhost:8071"
    db_2 = "v12_oscar_mig_v1"
    username_db_2 = "admin"
    password_db_2 = "Spectrum@20$20$"
    common_12 = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url_db2))

    models_12 = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url_db2))
    uid_db1 = common_10.authenticate(db_1, username_db_1, password_db_1, {})
    uid_db2 = common_12.authenticate(db_2, username_db_2, password_db_2, {})

    _logger.info("______________________START CRON JOBS__________________________", exc_info=True)
    total_row = 0
    for record in records_10:
        print('DOCUMENT---:', record)
        total_row += 1

        if record['type']:
            type_id_v10 = record['type']
            print('type_id_v10', type_id_v10)
            type_10 = models_10.execute_kw(db_1, uid_db1, password_db_1, 'document.type', 'read', [[type_id_v10]],
                                           {'fields': ['name', 'code']})
            print('type_10', type_10)
            code_type_doc = type_10[0]['code']
            print('name_type_doc---', code_type_doc)
            type_12 = models_12.execute_kw(db_2, uid_db2, password_db_2, 'document.type', 'search_read',
                                           [[['code', '=', code_type_doc]]], {'fields': ['id', 'name']})
            print('type_12-----', type_12)
            type_id = False
            if type_12:
                type_id = type_12[0]['id']
                print('type_id---', type_id)

        magasin_v10 = record['code_magasin']
        # print('magasin_v10----', magasin_v10)
        # magasin_10 = models_10.execute_kw(db_1, uid_db1, password_db_1, 'magasin.aziza', 'read', [[magasin_v10]],
        #                                   {'fields': ['code_magasin']})
        # print('magasin_10----', magasin_10)
        # code_magasin = magasin_10[0]['code_magasin']
        # print('code_magasin---', code_magasin)
        magasin_12 = models_12.execute_kw(db_2, uid_db2, password_db_2, 'oscar.site', 'search_read',
                                          [[['code_site', '=', magasin_v10]]],
                                          {'fields': ['id', 'code_site']})
        print('magasin_12----', magasin_12)
        magasin_id_v12 = False
        if magasin_12:
            magasin_id_v12 = magasin_12[0]['id']
            print('magasin_id_v12---', magasin_id_v12)

        # if record['fournisseur']:
        fournisseur_v10 = record['code_fournisseur']
        fournisseur_12 = models_12.execute_kw(db_2, uid_db2, password_db_2, 'res.partner', 'search_read',
                                              [[['code_partner', '=', fournisseur_v10]]],
                                              {'fields': ['id', 'code_partner']})
        print('fournisseur_12----', fournisseur_12)
        fournisseur_id_v12 = False
        if fournisseur_12:
            fournisseur_id_v12 = fournisseur_12[0]['id']
            print('fournisseur_id_v12---', fournisseur_id_v12)

        user_v10 = record['code_user']
        user_12 = models_12.execute_kw(db_2, uid_db2, password_db_2, 'res.users', 'search_read',
                                       [[['code_user', '=', user_v10]]],
                                       {'fields': ['id', 'code_user']})
        print('user_12----', user_12)
        user_id_v12 = False
        if user_12:
            user_id_v12 = user_12[0]['id']
            print('user_id_v12---', user_id_v12)

        _logger.info("______________________START COMMANDE__________________________", exc_info=True)
        command_ids =models_10.execute_kw(db_1, uid_db1, password_db_1, 'document.aziza', 'search_read', [[]],
                                  {'fields':['commande_ids',]})
        if not record['commande_ids'] or None:
            pass
        if record['commande_ids']:
            tab = []
            for cmd_id in record['commande_ids']:
                command = models_10.execute_kw(db_1, uid_db1, password_db_1, 'commande.gold', 'read', [cmd_id],
                                               {'fields': ['name']})
                # print('code_user----', user[0]['code_user'])
                cmd_10 = command[0]['name']
                print('cmd_10------', cmd_10)
                cmd_12 = models_12.execute_kw(db_2, uid_db2, password_db_2, 'commande.gold', 'search_read',
                                              [[['name', '=', cmd_10]]], {'fields': ['id', 'name']})
                print('commande_12-----', cmd_12)
                if cmd_12:
                    tab.append(cmd_12[0]['id'])
                    command_ids = [(6, 0, tab)]
                    print('tab-----', tab)
                else:
                    command_ids = False
        new_document = models_12.execute_kw(db_2, uid_db2, password_db_2, 'ir.attachment', 'create',
                                        [{'name': record['name'], 'document_type_id': type_id,
                                           'site_id': magasin_id_v12,'user_id': user_id_v12,
                                          'numero_piece': record['numero_piece'], 'state': record['state'],'datas':record['attachment'],
                                          'fournisseur': fournisseur_id_v12,'date_insertion': record['date_insertion'],
                                          'total_ht': record['total_ht'], 'total_ttc': record['total_ttc'],
                                          'date_piece': record['date_piece'],
                                          'commande_ids': command_ids}])

    print('----total_row----', total_row)

except (Exception, psycopg2.Error) as error:
    print("Error while connecting to PostgreSQL", error)

    #'date_insertion': record['date_insertion'], 'total_ht': record['total_ht'], 'total_ttc': record['total_ttc'],'date_piece': record['date_piece'],