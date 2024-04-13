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

db_1_employee = models_10.execute_kw(db_1, uid_db1, password_db_1, 'hr.employee', 'search_read', [[]],
              {'fields':['id', 'code_employee','name','first_name', 'last_name',
                  'full_name','department_id','job_id','address_id','user_id','active']})
print('db_1_magasin', db_1_employee)


# total_count = 0
# for record in db_1_employee:
#     # print('Site---:', record)
#     if record['name']:
#         print('EMP--------:', record)
#     department_id = False
#     if record['department_id']:
#         print(record['department_id'][0])
#         department = models_10.execute_kw(db_1, uid_db1, password_db_1, 'hr.department', 'read', [record['department_id'][0]],
#                                              {'fields': ['name']})
#         print(department)
#         name_department = department[0]['name']
#         department_12 = models_12.execute_kw(db_2, uid_db2, password_db_2, 'res.bank', 'search_read', [[['name', '=', name_department]]], {'fields': ['id', 'name']})
#         print('department_12-----',department_12)
#         if department_12:
#             department_id = department_12[0]['id']
#     
#     job_id = False
#     if record['job_id']:
#         print(record['job_id'][0])
#         job = models_10.execute_kw(db_1, uid_db1, password_db_1, 'hr.job', 'read', [record['job_id'][0]],
#                                              {'fields': ['name']})
#         print(job)
#         name_job = job[0]['name']
#         print('name_job-----------',name_job)
#         job_12 = models_12.execute_kw(db_2, uid_db2, password_db_2, 'res.bank', 'search_read', [[['name', '=', name_job]]], {'fields': ['id', 'name']})
#         print('job_12-----',job_12)
#         if job_12:
#             job_id = job_12[0]['id']
#     
#     user_id = False
#     if record['user_id']:
#         print(record['user_id'][0])
#         user = models_10.execute_kw(db_1, uid_db1, password_db_1, 'res.users', 'read', [record['user_id'][0]],
#                                              {'fields': ['code_user']})
#         print(user)
#         code_user_10 = user[0]['code_user']
#         user_12 = models_12.execute_kw(db_2, uid_db2, password_db_2, 'res.users', 'search_read', [[['code_user', '=', code_user_10],'|',['active','=',True],['active','=',False]]], {'fields': ['id', 'login', 'code_user']})
#         print('user_12-----',user_12)
#         if user_12:
#             user_id = user_12[0]['id']
#         
#     total_count += 1
#     
#     
#     new_user = models_12.execute_kw(db_2, uid_db2, password_db_2, 'hr.employee', 'create',
#     [{'code_employee': record['code_employee'], 'name': record['name'], 'first_name': record['first_name'],
#       'last_name': record['last_name'], 'department_id': 3, 'job_id': job_id, 'address_id': 1, 'active': True}])

new_user = models_12.execute_kw(db_2, uid_db2, password_db_2, 'hr.employee', 'create',[{'name': 'TEST', 'first_name': 'TEST1','last_name': 'TEST2'}])

logging.info("______________________END CRON JOBS__________________________")
print('****Total Created Employee***', total_count)