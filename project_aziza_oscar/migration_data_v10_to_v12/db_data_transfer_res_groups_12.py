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

db_1_users = models_12.execute_kw(db_2, uid_db2, password_db_2, 'res.users', 'search_read', [['|',['active','=',True],['active','=',False]]], {'fields': ['id', 'name','code_user','login','password','profil','active','create_date','password_crypt']})
print(db_1_users)
total_count = 0
for user in db_1_users:
    print('User---:', user)
    total_count += 1
    if user['id'] not in [1,2,3,4,5]:
        
        if user['profil'] in ["RESPMAG","ADMAG"]:
            
#             search_groups = models_12.execute_kw(db_2, uid_db2, password_db_2, 'res.groups', 'search_read', [[['name','=','Responsable Magasin / Adjoint']]],
#                {'fields': ['id', 'name']})
#             print("search_groups------",search_groups)
            
            update_user = models_12.execute_kw(db_2, uid_db2, password_db_2, 'res.users', 'write', [[user['id']], {
                    'groups_id': [(6, 0, [1,7,8,12,34,19])]
                }])
            
        if user['profil'] == "RESPZONE":
#             search_groups = models_12.execute_kw(db_2, uid_db2, password_db_2, 'res.groups', 'search_read', [[['name','=','Responsable Zone']]],
#                {'fields': ['id', 'name']})
#             print("search_groups------",search_groups)
            
            update_user = models_12.execute_kw(db_2, uid_db2, password_db_2, 'res.users', 'write', [[user['id']], {
                    'groups_id': [(6, 0, [1,7,8,12,34,20])]
                }])
            
        if user['profil'] == "DRE":
            
#             search_groups = models_12.execute_kw(db_2, uid_db2, password_db_2, 'res.groups', 'search_read', [[['name','=','DRE']]],
#                {'fields': ['id', 'name']})
#             print("search_groups------",search_groups)
            
            update_user = models_12.execute_kw(db_2, uid_db2, password_db_2, 'res.users', 'write', [[user['id']], {
                    'groups_id': [(6, 0, [1,7,8,12,34,22])]
                }])
            

logging.info("______________________END CRON JOBS__________________________")
print('****Total Created Users***', total_count)