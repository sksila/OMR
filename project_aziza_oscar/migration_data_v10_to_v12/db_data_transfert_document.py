import psycopg2
import psycopg2.extras
import xmlrpc.client
import logging
import time

logging.basicConfig(format='Date-Time : %(asctime)s : Line No. : %(lineno)d - %(message)s', \
                    level = logging.INFO)


url_db1 = "http://172.17.1.47:8069"
db_1 = "aziza"
username_db_1 = "admin"
password_db_1 = "Spectrum@20$20$"

common_10 = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url_db1))
models_10 = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url_db1))
version_db1 = common_10.version()
print('details of first database v10....', version_db1)
print('**********************************')

url_db2 = "http://172.17.1.53"
db_2 = "oscar_v12"
username_db_2 = "admin"
password_db_2 = "Spectrum@20$20$"

common_12 = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url_db2))
models_12 = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url_db2))
version_db2 = common_12.version()
print('details of second database v12....', version_db2)

uid_db1 = common_10.authenticate(db_1, username_db_1, password_db_1, {})
uid_db2 = common_12.authenticate(db_2, username_db_2, password_db_2, {})
print('uid_db1', uid_db1)
print('uid_db2', uid_db2)
logging.info("______________________StART CRON JOBS__________________________")

# Commenter les @api.constrains('commande_ids', 'total_ttc', 'total_ht') avant la migration

# lot1 = ('1070','1098','1306') 10/12
# lot2 = ('1176','1181','1357','1180') 14/12
# lot3 = ('1090','1124','1194','1183','1277','1299','1305') 17/12
# lot4 = ('1182','1206','1093','1107','1379'), ('1175','1163','1114','1137','1147','1208') 24/12
# lot5 = ('1075','1106','1109','1126'),('1198','1195','1259','1311','1312') 25/12
# lot6 = ('1102','1023','1218','1050','1027','1105') 13/01
# lot7 = ('1021','1125','1276','1144') 16/01
# lot8 = ('1283','1029','1193','1149','1249') 04/02 NOT OK
# lot9 = ('1148','1363','1041','1136','1263','1272') 08/02 NOT OK
# lot10 = ('1025','1082','1099','1108','1131','1179'),('1293','1393','1057','1039','1076','1220') 11/02 NOT OK
# lot11 = ('1007','1005','1034','1213','1264','1160'),('1337','1325','1015','1053','1123','1092','1287') 15/02 NOT OK
# lot12 = ('1006','1009','1014','1054','1068','1284'),('1132','1060','1228','1096','1258') 18/02 NOT OK
# lot13 = ('1006','1009','1014','1054','1068','1284'),('1132','1060','1228','1096','1258') 18/02 NOT OK


connection_10 = psycopg2.connect(user="odoo", password="Aziza21022018", host="172.17.1.47", port="5432", database="aziza")
cursor_10 = connection_10.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
cursor_10.execute("SELECT id FROM document_aziza WHERE magasin_id in (SELECT id FROM magasin_aziza WHERE code IN ('1021','1125','1276','1144'))")
ids_doc_10 = cursor_10.fetchall()

connection_12 = psycopg2.connect(user="odoo12", password="Aziza22072019", host="172.17.1.53", port="5432", database="oscar_v12")
cursor_12 = connection_12.cursor()

count = 0
c = 0
for record in ids_doc_10:
    count += 1
    try:
        logging.info("SEARCH DOC ID : %s" % (record['id']))
        db_1_document = models_10.execute_kw(db_1, uid_db1, password_db_1, 'document.aziza', 'search_read', [[['id','=',record['id']]]],
                                          {'fields':['id', 'name', 'type', 'user_id',
                                                     'date_insertion','magasin_id','numero_piece', 'date_piece',
                                                     'total_ht','total_ttc','attachment','attachment_name',
                                                     'fournisseur','state','code_magasin','code_fournisseur',
                                                     'commande_ids','state','type_transfert','is_uploaded']})
    except Exception as error:
        print("Error RPC : ", error)
        pass

    name = ''
    if db_1_document[0]['name']:
        name = db_1_document[0]['name']

    query = '''SELECT id FROM public.ir_attachment WHERE name='%s';'''%(name)
    name_query = cursor_12.execute(query)
    doc_12 = cursor_12.fetchone()
    if doc_12:
        logging.info("------> %s break<------"%(count))
    else:
        c += 1
        logging.info("------> %s done<------"%(count))
        if db_1_document[0]['type']:

            type_id_v10 = db_1_document[0]['type'][0]
            type_10 = models_10.execute_kw(db_1, uid_db1, password_db_1, 'document.type', 'read', [[type_id_v10]],
                                               {'fields': ['name','code']})
            code_type_doc = type_10[0]['code']
            type_12 = models_12.execute_kw(db_2, uid_db2, password_db_2, 'document.type', 'search_read',
                                           [[['code', '=', code_type_doc]]], {'fields': ['id', 'name']})
            type_id = False
            if type_12:
                type_id = type_12[0]['id']

        magasin_id_v12 = False
        if db_1_document[0]['magasin_id']:
            code_magasin = db_1_document[0]['code_magasin']
            magasin_12 = models_12.execute_kw(db_2, uid_db2, password_db_2, 'oscar.site', 'search_read',
                                               [[['code_site', '=', code_magasin]]],
                                               {'fields': ['id', 'code_site']})
            if magasin_12:
                magasin_id_v12 = magasin_12[0]['id']

        fournisseur_id_v12 = False
        if db_1_document[0]['code_fournisseur']:
            fournisseur_v10 = db_1_document[0]['code_fournisseur']
            fournisseur_12 = models_12.execute_kw(db_2, uid_db2, password_db_2, 'res.partner', 'search_read',
                                               [[['code_partner', '=', fournisseur_v10]]],
                                               {'fields': ['id', 'code_partner']})
            if fournisseur_12:
                fournisseur_id_v12 = fournisseur_12[0]['id']

        user_id = False
        if db_1_document[0]['user_id']:
            user = models_10.execute_kw(db_1, uid_db1, password_db_1, 'res.users', 'read', [db_1_document[0]['user_id'][0]],
                                                 {'fields': ['login']})
            if user:
                code_user_10 = user[0]['login']
                user_12 = models_12.execute_kw(db_2, uid_db2, password_db_2, 'res.users', 'search_read', [[['login', '=', code_user_10],'|',['active','=',True],['active','=',False]]], {'fields': ['id', 'login', 'code_user']})
                if user_12:
                    user_id = user_12[0]['id']

        command_ids = False
        if db_1_document[0]['commande_ids']:

            tab = []
            for cmd_id in db_1_document[0]['commande_ids']:
                command = models_10.execute_kw(db_1, uid_db1, password_db_1, 'commande.gold', 'read', [cmd_id],
                                            {'fields': ['name']})
                cmd_10 = command[0]['name']
                cmd_12 = models_12.execute_kw(db_2, uid_db2, password_db_2, 'commande.gold', 'search_read',
                                               [[['name', '=', cmd_10]]], {'fields': ['id', 'name']})
                if cmd_12:
                    tab.append(cmd_12[0]['id'])
                    command_ids = [(6, 0, tab)]

        attachment = ''
        if db_1_document[0]['attachment']:
            attachment = db_1_document[0]['attachment']


        vals = [{'code': name,
                'document_type_id': type_id,
                'date_insertion': db_1_document[0]['date_insertion'],
                'site_id': magasin_id_v12,
                'user_id': user_id,
                'numero_piece': db_1_document[0]['numero_piece'],
                'state':db_1_document[0]['state'],
                'datas_fname':db_1_document[0]['attachment_name'],
                'fournisseur': fournisseur_id_v12,
                'date_piece': db_1_document[0]['date_piece'],
                'total_ht': db_1_document[0]['total_ht'],
                'total_ttc': db_1_document[0]['total_ttc'],
                'commande_ids':command_ids,
                'type_transfert': db_1_document[0]['type_transfert'],
                'is_uploaded': db_1_document[0]['is_uploaded'],
                'active': True}]


        new_document = models_12.execute_kw(db_2, uid_db2, password_db_2, 'ir.attachment', 'create', vals)
        query = '''UPDATE public.ir_attachment SET db_datas='%s', name='%s' WHERE id=%s;'''%(attachment,name,new_document)
        mg_query = cursor_12.execute(query)
        connection_12.commit()


logging.info("------> %s RECORDS CREATED<------" % (c))

logging.info("______________________END CRON JOBS__________________________")
