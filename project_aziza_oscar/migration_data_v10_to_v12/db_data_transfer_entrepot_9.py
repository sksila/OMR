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


db_1_entrepot = models_10.execute_kw(db_1, uid_db1, password_db_1, 'entrepot.aziza', 'search_read', [[]],
                                  {'fields':['id', 'name','code','code_entrepot',
                                             'date_ouverture','zone','region','user_id','active']})
# print('db_1_magasin', db_1_site)
total_count = 0
for record in db_1_entrepot:
    # print('Entrepot---:', record)
    if not record['user_id']:
        user_id = False
    else:
        user = models_10.execute_kw(db_1, uid_db1, password_db_1, 'res.users', 'read', [record['user_id'][0]],
                 {'fields': ['code_user']})
        user_10 = user[0]['code_user']
        user_12 = models_12.execute_kw(db_2, uid_db2, password_db_2, 'res.users', 'search_read', [[['code_user', '=', user_10]]], {'fields': ['id', 'login', 'code_user']})
        print('user_12-----',user_12)
        user_id = user_12[0]['id']
    
    if user_id:
        user_ids = [(6, 0, [user_id])]
    else:
        user_ids = False

    total_count += 1
    new_user = models_12.execute_kw(db_2, uid_db2, password_db_2, 'oscar.site', 'create',
    [{'name': record['name'], 'code': record['code'], 'code_site': record['code_entrepot'] ,'date_ouverture': record['date_ouverture'],
      'zone': record['zone'], 'region': record['region'],
      'user_id': user_id, 'site_type': 'ENTREPOT', 'user_ids': user_ids, 'active':True}])

    #'bank_id': user['bank_id'][0], 'adjoint_id': user['adjoint_id'][0],
    #'resp_zone_id': user['resp_zone_id'][0], 'dre_id': user['dre_id']

print('****Total Created Entrepots***', total_count)