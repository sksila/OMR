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

db_1_contrat = models_10.execute_kw(db_1, uid_db1, password_db_1, 'contract.renewal', 'search_read', [[]],
                                  {'fields':['id', 'name', 'employee_id', 'job_id',
                                             'department_id','manager_id','magasin_id','type_current_id', 'date',
                                             'date_embauche','date_start','date_end','remaining_leaves', 'type_id',
                                             'number_months', 'end_contract','notes', 'is_expired',
                                             'code_employee','code_magasin', 'code_manager','code_job','state']})
total_count = 0
for record in db_1_contrat:
    total_count += 1
    # if record['employee_id']:
    employee_10 = record['code_employee']
    employee_id = False
    if employee_10:
        employee_12 = models_12.execute_kw(db_2, uid_db2, password_db_2, 'hr.employee', 'search_read',
                                       [[['code_employee', '=', employee_10]]], {'fields': ['id', 'name', 'code_employee']})
        employee_id = employee_12[0]['id']

    
    job_10 = record['job_id']
    if job_10:
        job_12 = models_12.execute_kw(db_2, uid_db2, password_db_2, 'hr.job', 'search_read',
                                           [[['name', '=', job_10[1]]]],
                                           {'fields': ['id', 'name', 'code_job']})
        job_id = job_12[0]['id'] or False

    # if record['magasin_id']:
    magasin_10 = record['code_magasin']
    if magasin_10:
        magasin_12 = models_12.execute_kw(db_2, uid_db2, password_db_2, 'oscar.site', 'search_read',
                                           [[['code_site', '=', magasin_10]]],
                                           {'fields': ['id', 'name', 'code_site']})
        magasin_id = magasin_12[0]['id'] or False

    manager_10 = record['code_manager']
    if manager_10:
        manager_12 = models_12.execute_kw(db_2, uid_db2, password_db_2, 'hr.employee', 'search_read',
                                          [[['code_employee', '=', manager_10]]],
                                          {'fields': ['id', 'name', 'code_employee']})
        manager_id = manager_12[0]['id'] or False

    if record['department_id']:
        department_10 = record['department_id'][1]
        department_12 = models_12.execute_kw(db_2, uid_db2, password_db_2, 'hr.department', 'search_read',
                                      [[['name', '=', department_10]]],
                                      {'fields': ['id', 'name', 'code_department']})
        department_id = department_12[0]['id'] or False

    if record['type_current_id']:
        type_current_10 = record['type_current_id'][1]
        type_current_12 = models_12.execute_kw(db_2, uid_db2, password_db_2, 'hr.contract.type', 'search_read',
                                      [[['name', '=', type_current_10]]],
                                      {'fields': ['id', 'name']})
        type_current_id = type_current_12[0]['id'] or False

    if record['type_id']:
        type_10 = record['type_id'][1]
        type_12 = models_12.execute_kw(db_2, uid_db2, password_db_2, 'hr.contract.type', 'search_read',
                                      [[['name', '=', type_10]]],
                                      {'fields': ['id', 'name']})
        type_id = type_12[0]['id'] or False
    
    logging.info("------> %s <------"%(total_count))
    
    new_contrat = models_12.execute_kw(db_2, uid_db2, password_db_2, 'oscar.contract.renewal', 'create',
    [{'name': record['name'], 'employee_id': employee_id,  'magasin_id': magasin_id,'manager_id': manager_id,'date': record['date'],
      'date_embauche': record['date_embauche'],'state':record['state'],
      'date_start': record['date_start'],'date_end': record['date_end'],'remaining_leaves': record['remaining_leaves'],
      'job_id': job_id,'department_id': department_id,'type_current_id': type_current_id,'type_id': type_id,
          'number_months': record['number_months'], 'end_contract': record['end_contract'],'notes': record['notes'], 'is_expired': record['is_expired']}])


logging.info("______________________END CRON JOBS__________________________")
print('****Total Created contrat***', total_count)
