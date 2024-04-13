import psycopg2
import psycopg2.extras
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

connection_10 = psycopg2.connect(user="odoo", password="Aziza21022018", host="172.17.1.47", port="5432", database="aziza")
cursor_10 = connection_10.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

logging.info("______________________StART CRON JOBS__________________________")

db_1_product = models_10.execute_kw(db_1, uid_db1, password_db_1, 'sav.product', 'search_read', [[]],
                                  {'fields': ['id', 'name', 'barcode', 'code_product',
                                             'categ_id','supplier_id']})

total_count = 0
total_search = 0
for record in db_1_product:
    if record['name']:
        total_count += 1
        name = record['name']
        product = models_10.execute_kw(db_1, uid_db1, password_db_1, 'dispatch.product.inter', 'search_read', [[['article','ilike',name]]],{'fields': ['id', 'article', 'code_article'],'limit':1})
        if product:
            total_search += 1
            print("product SAV : ", name)
            print("product Dispatch : ", product)
            query = '''UPDATE public.sav_product SET code_product='%s' WHERE id=%s;'''%(product[0]['code_article'],record['id'])
            mg_query = cursor_10.execute(query)
            connection_10.commit()

print('****Total Searched Products***', total_search)
print('****Total Created Products***', total_count)