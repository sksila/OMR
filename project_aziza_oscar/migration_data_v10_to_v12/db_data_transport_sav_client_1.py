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

db_1_customer = models_10.execute_kw(db_1, uid_db1, password_db_1, 'sav.customer', 'search_read', [[]],
            {'fields': ['id', 'code_customer', 'name', 'last_name', 'cin', 'email', 'phone', 'address', 'active']})
print('db_1_customer', db_1_customer)
total_count = 0
_logger.info("______________________StART CRON JOBS__________________________", exc_info=True)
for record in db_1_customer:
    print('customer---:', record)
    total_count += 1
    if not record['name'] and not record['last_name']:
        full_name = False
    if record['name'] and record['last_name']:
        full_name = record['name'] + ' ' + record['last_name']
        print('full_name', full_name)
    if record['name']:
        full_name = record['name']

    new_customer = models_12.execute_kw(db_2, uid_db2, password_db_2, 'res.partner', 'create',
    [{'code_partner': record['code_customer'], 'name': full_name,
      'cin': record['cin'] , 'email': record['email'], 'phone': record['phone'],  'city': record['address'],
      'active': record['active'], 'customer': True}])
    #'commercial_partner_id': user['commercial_partner_id'][0],'country_id': user['country_id'][0] or False,'parent_id': user['parent_id'][0] or False,
    #'title': user['title'][0],
_logger.info("______________________END CRON JOBS__________________________", exc_info=True)
print('****Total Created Customers***', total_count)