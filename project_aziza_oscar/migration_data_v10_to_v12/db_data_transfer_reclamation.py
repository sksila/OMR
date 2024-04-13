#==========================================================
#REMARQUE: Avant de lancer ce script, il faut savoir qu'on pas pu trouver un identifiant unique pour le produit,
#c'est pour cela que je le met une valeur statique
#==========================================================

import xmlrpc.client

url_db1 = "http://localhost-10:8070"
db_1 = "aziza_backup_17_9"
username_db_1 = "admin"
password_db_1 = "Spectrum@20$20$"

common_10 = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url_db1))
models_10 = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url_db1))
version_db1 = common_10.version()
print('details of first database v10....', version_db1)
print('**********************************')

url_db2 = "http://localhost:8071"
db_2 = "v12_oscar_v1"
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

db_1_reclamation = models_10.execute_kw(db_1, uid_db1, password_db_1, 'sav.claim', 'search_read', [[]],
                                  {'fields':['id', 'name', 'code', 'customer_id','code_customer','code_magasin',
                                             'code_problem','code_user',
                                             'magasin_id','date_claim','date_purchase','product_id', 'problem_id',
                                             'is_fixed','is_refused','is_back','type', 'barcode',
                                             'is_receive', 'state','has_guarantee', 'has_receipt', 'has_accessories',
                                             'user_id']})
# print('db_1_reclamation---',db_1_reclamation)
total_count = 0
for record in db_1_reclamation:
    print('********import client**********')
    customer_id = record['customer_id']
    print('customer_id----', customer_id)
    if customer_id:
        customer_v10 = record['customer_id'][0]
        print('customer_v10', customer_v10)
        customer_v10 = models_10.execute_kw(db_1, uid_db1, password_db_1, 'sav.customer', 'read', [[customer_v10]],
                                       {'fields': ['code_customer']})
        print('customer_v10', customer_v10)
        code_customer = customer_v10[0]['code_customer']
        print('code_customer---', code_customer)
    # customer_v10 = record['code_customer']
    # print('customer_v10---', customer_v10)
    customer_12 = models_12.execute_kw(db_2, uid_db2, password_db_2, 'res.partner', 'search_read', [[['code_partner', '=', code_customer]]],
                                       {'fields': ['id', 'code_partner']})
    print('customer_12----',customer_12)
    customer_id_v12 = False
    if customer_12:
        customer_id_v12 = customer_12[0]['id']
        print('customer_id_v12----', customer_id_v12)

    print('*********import product***********')
    product_id = record['product_id']
    print('product_id----', product_id)
    if product_id:
        product_v10 = record['product_id'][0]
        print('product_v10----', product_v10)
        product_10 = models_10.execute_kw(db_1, uid_db1, password_db_1, 'sav.product', 'read', [[product_v10]],
                                       {'fields': ['name']})
        print('product_10----', product_10)
        name_product = product_10[0]['name']
        print('name_product---', name_product)
    product_12 = models_12.execute_kw(db_2, uid_db2, password_db_2, 'product.template', 'search_read',
                                       [[['name', 'like', name_product]]],
                                       {'fields': ['id', 'name']})
    print('product_12----', product_12)
    product_id_v12 = False
    if product_12:
        product_id_v12 = product_12[0]['id'] or False or '' or 4551
        print('product_id_v12---', product_id_v12)
    print('*********import magasin***********')
    # magasin_10 = record['code_magasin']
    magasin_10 = record['magasin_id']
    print('magasin_10----', magasin_10)
    if magasin_10:
        magasin_v10 = record['magasin_id'][0]
        print('magasin_v10----------', magasin_v10)
    magasin_10 = models_10.execute_kw(db_1, uid_db1, password_db_1, 'magasin.aziza', 'read', [[magasin_v10]],
                                      {'fields': ['code_magasin','name']})
    print('magasin_10----', magasin_10)
    code_magasin = magasin_10[0]['code_magasin']
    print('code_magasin---', code_magasin)
    magasin_12 = models_12.execute_kw(db_2, uid_db2, password_db_2, 'oscar.site', 'search_read',
                                       [[['code_site', '=', code_magasin]]],
                                       {'fields': ['id', 'code_site','name']})
    print('magasin_12----', magasin_12)
    magasin_id_v12 = False
    if magasin_12:
        magasin_id_v12 = magasin_12[0]['id']
        print('magasin_id_v12---', magasin_id_v12)
    print('************Import Problem Claim*************')
    problem_10 = record['problem_id']
    print('problem_10----', problem_10)

    if problem_10:
        problem_v10 = record['problem_id'][0]
        print('problem_v10----------', problem_v10)
    problem_10 = models_10.execute_kw(db_1, uid_db1, password_db_1, 'sav.problem', 'read', [[problem_v10]],
                                      {'fields': ['code_problem']})
    print('problem_10----', problem_10)
    code_problem = problem_10[0]['code_problem']
    print('code_problem---', code_problem)

    # problem_10 = record['code_problem']
    # print('problem_10----', problem_10)
    problem_12 = models_12.execute_kw(db_2, uid_db2, password_db_2, 'oscar.sav.problem', 'search_read',
                                       [[['code_problem', '=', code_problem]]],
                                       {'fields': ['id', 'code_problem']})
    print('problem_12----', problem_12)
    problem_id_v12 = False
    if problem_12:
        problem_id_v12 = problem_12[0]['id'] or False
        print('problem_id_v12---', problem_id_v12)

    print('*******import Réceptionné par *************')
    code_user = record['code_user']
    user_12 = models_12.execute_kw(db_2, uid_db2, password_db_2, 'res.users', 'search_read',
                                       [[['code_user', '=', code_user]]],
                                       {'fields': ['id', 'code_user']})
    print('user_12----', user_12)
    user_id_v12 = False
    if user_12:
        user_id_v12 = user_12[0]['id']
        print('user_id_v12---', user_id_v12)

        total_count += 1

    new_claim = models_12.execute_kw(db_2, uid_db2, password_db_2, 'oscar.sav.claim', 'create',
                                                 [{'name': record['name'],'product_id': 4551,
                                                   'customer_id': customer_id_v12,'magasin_id': magasin_id_v12,
                                                   'user_id': user_id_v12, 'problem_id': problem_id_v12,
                                                   'date_purchase': record['date_purchase'], 'code': record['code'],
                                                   'barcode': record['barcode'],
                                                   'date_claim': record['date_claim'],
                                                   'state': record['state'],
                                                   'is_fixed': record['is_fixed'],'is_refused': record['is_refused'], 'is_back': record['is_back'],
                                                   'type': record['type'],'is_receive': record['is_receive'], 'has_guarantee':record['has_guarantee'],
                                                   'has_receipt': record['has_receipt'],
                                                   'has_accessories': record['has_accessories']
                                                   }])

print('****Total Created Réclamations***', total_count)
