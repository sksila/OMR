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

db_2_users = models_12.execute_kw(db_2, uid_db2, password_db_2, 'res.users', 'search_read', [['|',['active','=',True],['active','=',False]]], {'fields': ['id', 'name','email','code_user','login']})
print(db_2_users)
total_count = 0
for user in db_2_users:
    print('User12---:', user)
    total_count += 1
    if user['id'] not in [1,2,3,4,5]:
        
        user_10 = models_10.execute_kw(db_1, uid_db1, password_db_1, 'res.users', 'search_read', [[['code_user','=',user['code_user']]]], {'fields': ['id', 'name','email','code_user']})
        print('User10---:', user_10)
        if user_10 and user_10[0]['email']:
            print("email---:", user_10[0]['email'])
            update_user = models_12.execute_kw(db_2, uid_db2, password_db_2, 'res.users', 'write', [[user['id']], {
                    'email': user_10[0]['email']
                }])
            

logging.info("______________________END CRON JOBS__________________________")
print('****Total Created Users***', total_count)