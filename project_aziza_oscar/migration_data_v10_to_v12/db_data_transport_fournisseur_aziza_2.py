import xmlrpc.client
import logging

_logger = logging.getLogger(__name__)


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
_logger.info("______________________StART CRON JOBS__________________________", exc_info=True)

db_1_supplier_ids = models_10.execute_kw(db_1, uid_db1, password_db_1, 'fournisseur.aziza', 'search_read', [[]],
            {'fields': ['id', 'code', 'code_fournisseur', 'name', 'phone', 'address']})
print('db_1_users', db_1_supplier_ids)
total_count = 0
for supplier in db_1_supplier_ids:
    print('supplier---:', supplier)
    total_count += 1
    new_user = models_12.execute_kw(db_2, uid_db2, password_db_2, 'res.partner', 'create',
    [{'code': supplier['code'], 'code_partner': supplier['code_fournisseur'],
       'name': supplier['name'],'phone': supplier['phone'], 'city': supplier['address'], 'supplier': True, 'active': True}])
  #, 'type': supplier['type'], // il existe un champs selection type
  #'active': record['active']

_logger.info("______________________END CRON JOBS__________________________", exc_info=True)
print('****Total Created Fournissuers***', total_count)