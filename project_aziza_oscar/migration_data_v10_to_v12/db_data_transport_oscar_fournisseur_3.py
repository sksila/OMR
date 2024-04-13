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
username_db_2 = "admin"
password_db_2 = "admin"

common_12 = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url_db2))
models_12 = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url_db2))
version_db2 = common_12.version()
print('details of second database v12....', version_db2)

uid_db1 = common_10.authenticate(db_1, username_db_1, password_db_1, {})
uid_db2 = common_12.authenticate(db_2, username_db_2, password_db_2, {})
print('uid_db1', uid_db1)
print('uid_db2', uid_db2)

db_1_supplier_oscar_ids = models_10.execute_kw(db_1, uid_db1, password_db_1, 'oscar.fournisseur', 'search_read', [[]],
            {'fields':['id', 'code', 'code_fournisseur_oscar', 'name', 'type']})
print('db_1_supplier_ids', db_1_supplier_oscar_ids)
total_count = 0
for supplier in db_1_supplier_oscar_ids:
    print('supplier_oscar---:', supplier)
    total_count += 1
    new_supplier_oscar = models_12.execute_kw(db_2, uid_db2, password_db_2, 'res.partner', 'create',
    [{'code': supplier['code'], 'code_partner': supplier['code_fournisseur_oscar'],
       'name': supplier['name'], 'supplier': True}])
  #, 'type': supplier['type'], // il existe un champs selection type
    #'active': record['active']
print('****Total Created Fournissuers Oscar***', total_count)