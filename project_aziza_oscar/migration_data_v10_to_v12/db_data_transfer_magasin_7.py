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


db_1_magasin = models_10.execute_kw(db_1, uid_db1, password_db_1, 'magasin.aziza', 'search_read', [[]],
                                  {'fields':['id', 'name', 'code', 'code_magasin',
                                             'date_ouverture','zone','region','type_versement', 'user_id',
                                             'bank_id','adjoint_id','resp_zone_id','dre_id', 'user_ids','active']})
print('db_1_magasin', db_1_magasin)
total_count = 0
for record in db_1_magasin:
    site_12 = models_12.execute_kw(db_2, uid_db2, password_db_2, 'oscar.site', 'search_read', [[['code_site', '=', record['code_magasin']]]], {'fields': ['id', 'code_site']})
    print('site_12-------------',site_12)
    if site_12:
        print('if site_12---------',site_12)
    else:
        print('Magasin---:', record)
        if record['user_ids']:
            tab = []
            for user_id in record['user_ids']:
                user = models_10.execute_kw(db_1, uid_db1, password_db_1, 'res.users', 'read', [user_id],
                                                 {'fields': ['code_user']})
                # print('code_user----', user[0]['code_user'])
                user_10 = user[0]['code_user']
                user_12 = models_12.execute_kw(db_2, uid_db2, password_db_2, 'res.users', 'search_read', [[['code_user', '=', user_10]]], {'fields': ['id', 'login', 'code_user']})
                print('user_12-----',user_12)
    
                tab.append(user_12[0]['id'])
                print('tab-----', tab)
        
        bank_id = False
        if record['bank_id']:
            print(record['bank_id'][0])
            bank = models_10.execute_kw(db_1, uid_db1, password_db_1, 'oscar.bank', 'read', [record['bank_id'][0]],
                                                 {'fields': ['code_bank']})
            print(bank)
            code_bank_10 = bank[0]['code_bank']
            bank_12 = models_12.execute_kw(db_2, uid_db2, password_db_2, 'res.bank', 'search_read', [[['code_bank', '=', code_bank_10]]], {'fields': ['id', 'name', 'code_bank']})
            print('bank_12-----',bank_12)
            bank_id = bank_12[0]['id']
        
        user_id = False
        if record['user_id']:
            print(record['user_id'][0])
            user = models_10.execute_kw(db_1, uid_db1, password_db_1, 'res.users', 'read', [record['user_id'][0]],
                                                 {'fields': ['code_user']})
            print(user)
            code_user_10 = user[0]['code_user']
            user_12 = models_12.execute_kw(db_2, uid_db2, password_db_2, 'res.users', 'search_read', [[['code_user', '=', code_user_10],'|',['active','=',True],['active','=',False]]], {'fields': ['id', 'login', 'code_user']})
            print('user_12-----',user_12)
            user_id = user_12[0]['id']
        
        adjoint_id = False
        if record['adjoint_id']:
            print(record['adjoint_id'][0])
            user = models_10.execute_kw(db_1, uid_db1, password_db_1, 'res.users', 'read', [record['adjoint_id'][0]],
                                                 {'fields': ['code_user']})
            print(user)
            code_user_10 = user[0]['code_user']
            user_12 = models_12.execute_kw(db_2, uid_db2, password_db_2, 'res.users', 'search_read', [[['code_user', '=', code_user_10],'|',['active','=',True],['active','=',False]]], {'fields': ['id', 'login', 'code_user']})
            print('user_12-----',user_12)
            adjoint_id = user_12[0]['id']
        
        resp_zone_id = False
        if record['resp_zone_id']:
            print(record['resp_zone_id'][0])
            user = models_10.execute_kw(db_1, uid_db1, password_db_1, 'res.users', 'read', [record['resp_zone_id'][0]],
                                                 {'fields': ['code_user']})
            print(user)
            code_user_10 = user[0]['code_user']
            user_12 = models_12.execute_kw(db_2, uid_db2, password_db_2, 'res.users', 'search_read', [[['code_user', '=', code_user_10],'|',['active','=',True],['active','=',False]]], {'fields': ['id', 'login', 'code_user']})
            print('user_12-----',user_12)
            resp_zone_id = user_12[0]['id']
        
        dre_id = False
        if record['dre_id']:
            print(record['dre_id'][0])
            user = models_10.execute_kw(db_1, uid_db1, password_db_1, 'res.users', 'read', [record['dre_id'][0]],
                                                 {'fields': ['code_user']})
            print(user)
            code_user_10 = user[0]['code_user']
            user_12 = models_12.execute_kw(db_2, uid_db2, password_db_2, 'res.users', 'search_read', [[['code_user', '=', code_user_10],'|',['active','=',True],['active','=',False]]], {'fields': ['id', 'login', 'code_user']})
            print('user_12-----',user_12)
            dre_id = user_12[0]['id']
        total_count += 1
        
        
        new_site = models_12.execute_kw(db_2, uid_db2, password_db_2, 'oscar.site', 'create',
        [{'name': record['name'], 'code': record['code'], 'code_site': record['code_magasin'] ,'date_ouverture': record['date_ouverture'],
          'zone': record['zone'], 'region': record['region'], 'type_versement': record['type_versement'],'site_type': 'MAGASIN',
          'resp_zone_id': resp_zone_id,'dre_id': dre_id, 'adjoint_id': adjoint_id, 'bank_id': bank_id, 'user_id': user_id,
        'user_ids': [(6, 0, tab)], 'active': record['active']}])

#   'resp_zone_id': record['resp_zone_id'][0],'dre_id': record['dre_id'][0],
#   'adjoint_id': record['adjoint_id'][0], 'bank_id': bank_id,
print('****Total Created Magasin***', total_count)