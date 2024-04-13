import xmlrpc.client
import logging
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

db_1_driver_ids = models_10.execute_kw(db_1, uid_db1, password_db_1, 'chauffeur.aziza', 'search_read', [[]],
            {'fields': ['id','code_chauffeur', 'name', 'tel', 'type']})
print('db_1_driver_ids', db_1_driver_ids)
total_count = 0
for record in db_1_driver_ids:
    print('chauffeur---:', record)
    total_count += 1
    search_driver = models_12.execute_kw(db_2, uid_db2, password_db_2, 'res.partner', 'search_read', [[['code_partner','=',record['code_chauffeur']]]],
            {'fields': ['code_partner']})
    print(search_driver)
    if search_driver and not search_driver[0]['code_partner']:
        print(total_count)
        new_driver = models_12.execute_kw(db_2, uid_db2, password_db_2, 'res.partner', 'create',
        [{'code_partner': record['code_chauffeur'], 'name': record['name'] or record['tel'],
           'phone': record['tel'], 'driver_type': record['type'], 'driver': True, 'active': True}])

logging.info("______________________END CRON JOBS__________________________")
print('****Total Created Chauffeurs***', total_count)