import xmlrpc.client

url_db1 = "http://localhost-10:8070"
db_1 = "aziza_backup_17_09"
username_db_1 = "admin"
password_db_1 = "Spectrum@20$20$"

common_10 = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url_db1))
models_10 = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url_db1))
version_db1 = common_10.version()
print('details of first database v10....', version_db1)
print('**********************************')

url_db2 = "http://localhost:8071"
db_2 = "v12_empty_db_v3"
username_db_2 = "admin12"
password_db_2 = "admin"

common_12 = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url_db2))
models_12 = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url_db2))
version_db2 = common_12.version()
print('details of second database v12....', version_db2)

uid_db1 = common_10.authenticate(db_1, username_db_1, password_db_1, {})
uid_db2 = common_12.authenticate(db_2, username_db_2, password_db_2, {})
print('uid_db1', uid_db1)
print('uid_db2', uid_db2)

db_1_categ_product = models_10.execute_kw(db_1, uid_db1, password_db_1, 'sav.product.category', 'search_read', [[]],
                                  {'fields':['id', 'name', 'code_product_category']})
# print('db_1_magasin', db_1_site)
total_count = 0
for record in db_1_categ_product:
    total_count += 1
    new_user = models_12.execute_kw(db_2, uid_db2, password_db_2, 'product.category', 'create',
    [{'name': record['name'], 'code_product_category': record['code_product_category']}])

print('****Total Created Product Categories****', total_count)