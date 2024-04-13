import psycopg2.extras
import xmlrpc.client
import time
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

logging.info("______________________StART CRON JOBS__________________________")

vals_customer = {
                    'name': "TEST",
                    'phone': '001',
                    'code_partner': 'TEST001',
                    'customer': True,
                    'type': 'contact',
                    'active': True
                }
logging.info("---- CREATE CUSTOMER")
customer_id = models_12.execute_kw(db_2, uid_db2, password_db_2, 'res.partner', 'create', vals_customer)
logging.info("---- Customer created %s : 'Test' ---- "%(customer_id) )