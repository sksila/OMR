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

db_1_problem = models_10.execute_kw(db_1, uid_db1, password_db_1, 'sav.problem', 'search_read', [[]],
            {'fields': ['id', 'name', 'categ_id', 'code_problem']})
print('db_1_problem', db_1_problem)
total_count = 0
for record in db_1_problem:
    print('problem---:', record)
    if record['categ_id']:
        category = models_10.execute_kw(db_1, uid_db1, password_db_1, 'sav.product.category', 'read', [record['categ_id'][0]],
                                {'fields': ['name']})
        print('category----', category)
        category_10 = category[0]['name']
        print('category_10----', category_10)
        category_12 = models_12.execute_kw(db_2, uid_db2, password_db_2, 'product.category', 'search_read',
                                   [[['name', '=', category_10]]], {'fields': ['id', 'name']})
        print('category_12-----', category_12)
        category_id = False
        if category_12:
            category_id = category_12[0]['id']

        total_count += 1

        new_problem = models_12.execute_kw(db_2, uid_db2, password_db_2, 'oscar.sav.problem', 'create',
        [{'name': record['name'], 'code_problem': record['code_problem'], 'categ_id':category_id}])

print('****Total Created Customers***', total_count)