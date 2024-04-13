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
try:
    connection_10 = psycopg2.connect(user="odoo", password="Aziza21022018", host="172.17.1.47", port="5432", database="aziza")
    cursor_10 = connection_10.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor_10.execute("""SELECT name, code, product_id, customer_id, magasin_id, user_id, problem_id, other, panne, date_purchase, date_claim, state, is_fixed, is_refused, is_exchanged, is_back, type, is_receive, has_guarantee, has_receipt, has_accessories, code_customer, code_magasin, code_problem, code_user, repair_note, repair_mode, cmis_folder  FROM sav_claim WHERE state IN ('done4')""")
    records_10 = cursor_10.fetchall()

    connection_12 = psycopg2.connect(user="odoo12", password="Aziza22072019", host="172.17.1.53", port="5432", database="oscar_v12")
    cursor_12 = connection_12.cursor()

    total_row = 0
    obj = ''
    i = 0
    not_product = 0
    client = 0

    for record in records_10:

        total_row += 1
        i += 1

        if not record['name']:
            name = ''
        else:
            name = record['name']

        if not record['code']:
            code = ''
        else:
            code = record['code']

        logging.info("SEARCH CUSTOMER")
        if not record['customer_id']:
            customer_id = ''
        else:
            client_id = record['customer_id']
            query = """SELECT name,last_name,phone,code_customer FROM sav_customer WHERE id='%s';""" % (client_id)
            customer_query = cursor_10.execute(query)
            customer_id_v10 = cursor_10.fetchall()
            code_customer = customer_id_v10[0]['code_customer']
            query = """SELECT id FROM res_partner WHERE code_partner='%s';""" % (code_customer)
            customer_query = cursor_12.execute(query)
            customer_id_v12 = cursor_12.fetchall()
            if customer_id_v12:
                customer_id = customer_id_v12[0][0]
            else:
                client_id = record['customer_id']
                query = """SELECT name,last_name,phone,code_customer FROM sav_customer WHERE id='%s';""" % (client_id)
                customer_query = cursor_10.execute(query)
                customer_id_v10 = cursor_10.fetchall()
                name_customer = '%s %s'%(customer_id_v10[0]['name'],customer_id_v10[0]['last_name'] or '')
                phone = customer_id_v10[0]['phone']
                # vals_customer = {
                #     'name': "%s %s"%(customer_id_v10[0]['name'],customer_id_v10[0]['last_name'] or ''),
                #     'phone': customer_id_v10[0]['phone'],
                #     'code_partner': code_customer,
                #     'customer': True,
                #     'type': 'contact',
                #     'active': True
                # }
                # customer_id = models_12.execute_kw(db_2, uid_db2, password_db_2, 'res.partner', 'create', vals_customer)


                query_create_client = '''INSERT INTO res_partner (name, phone, code_partner, customer, type, active) 
                VALUES ('%s', '%s', '%s', %s, '%s', %s);''' %(name_customer,phone,code_customer,True,'contact',True)
                cursor_12.execute(query_create_client)
                obj = ''
                connection_12.commit()
                client += 1

                select_client = """SELECT id FROM res_partner WHERE code_partner='%s';""" % (code_customer)
                cursor_12.execute(select_client)
                partner_id_v12 = cursor_12.fetchall()
                customer_id = partner_id_v12[0][0]

                logging.info("---- Customer created : %s ---- " % (customer_id_v10[0]['name']))


        logging.info("SEARCH PRODUCT")
        product_id = ''
        if record['product_id']:
            query_barcode = '''SELECT barcode,code_product FROM public.sav_product WHERE id='%s';''' % (record['product_id'])
            query_exe = cursor_10.execute(query_barcode)
            product_v10 = cursor_10.fetchall()
            code_product = product_v10[0]['code_product'] or product_v10[0]['barcode'] or False
            if code_product:
                query = '''SELECT id FROM public.product_template WHERE default_code='%s';''' % (code_product)
                product_query = cursor_12.execute(query)
                product_id_v12 = cursor_12.fetchall()
                if product_id_v12:
                    product_id = product_id_v12[0][0]
                else:
                    not_product += 1
                    logging.info("---- :/ Product not found : %s " % (record['product_id']))
            else:
                not_product += 1
                logging.info("---- :/ Product not found : %s " %(record['product_id']))

        logging.info("SEARCH MAGASIN")
        magasin_id = ''
        if record['magasin_id']:
            query_mg = '''SELECT code FROM public.magasin_aziza WHERE id='%s';''' % (record['magasin_id'])
            query_exe = cursor_10.execute(query_mg)
            code_mg = cursor_10.fetchall()[0]['code']

            query = '''SELECT id FROM public.oscar_site WHERE code='%s';''' % (code_mg)
            magasin_query = cursor_12.execute(query)
            magasin_id_v12 = cursor_12.fetchall()
            if magasin_id_v12:
                magasin_id = magasin_id_v12[0][0]

        logging.info("SEARCH SAV PROBLEM")
        problem_id = ''
        if record['problem_id']:
            query_problem = '''SELECT code_problem FROM public.sav_problem WHERE id='%s';''' % (record['problem_id'])
            cursor_10.execute(query_problem)
            code_problem = cursor_10.fetchall()[0]['code_problem']
            query = '''SELECT id FROM public.oscar_sav_problem WHERE code_problem='%s';''' % (code_problem)
            problem_query = cursor_12.execute(query)
            problem_id = cursor_12.fetchall()[0][0]


        if not record['other']:
            other = False
        else:
            other = record['other']

        if not record['panne']:
            panne = ''
        else:
            panne = str(record['panne']).replace('"', '').replace("'", "")

        logging.info("SEARCH USER")
        user_id = ''
        if record['user_id']:
            query_user = '''SELECT login FROM public.res_users WHERE id='%s';''' % (record['user_id'])
            query_exe = cursor_10.execute(query_user)
            login_user = cursor_10.fetchall()[0]['login']
            logging.info("USER : %s"%(login_user))
            query = '''SELECT id FROM public.res_users WHERE login='%s';''' % (login_user)
            user_query = cursor_12.execute(query)
            user_id = cursor_12.fetchall()[0][0]


        if not record['date_claim']:
            date_claim = ''
        else:
            date_claim = str(record['date_claim'])

        if not record['date_purchase']:
            date_purchase = ''
        else:
            date_purchase = str(record['date_purchase'])

        if not record['is_fixed']:
            is_fixed = False
        else:
            is_fixed = record['is_fixed']

        if not record['is_refused']:
            is_refused = False
        else:
            is_refused = record['is_refused']


        if not record['is_exchanged']:
            is_exchanged = False
        else:
            is_exchanged = record['is_exchanged']

        if not record['is_back']:
            is_back = False
        else:
            is_back = record['is_back']

        if not record['type']:
            type = 'reclamation_client'
        else:
            type = record['type']

        if not record['is_receive']:
            is_receive = False
        else:
            is_receive = record['is_receive']

        if not record['state']:
            state = 'done4'
        else:
            state = record['state']

        if not record['has_guarantee']:
            has_guarantee = False
        else:
            has_guarantee = record['has_guarantee']

        if not record['has_receipt']:
            has_receipt = False
        else:
            has_receipt = record['has_receipt']

        if not record['has_accessories']:
            has_accessories = False
        else:
            has_accessories = record['has_accessories']

        if record['repair_note']:
            repair_note = str(record['repair_note']).replace('"', '').replace("'", "")
        else:
            repair_note = ''

        if record['repair_mode']:
            repair_mode = record['repair_mode']
        else:
            repair_mode = ''

        if record['cmis_folder']:
            cmis_folder = record['cmis_folder']
        else:
            cmis_folder = ''


        vals = (name, code,product_id, customer_id,magasin_id, user_id, problem_id,other,panne, date_purchase, date_claim, state, is_fixed, is_refused, is_back, is_exchanged, type, is_receive, has_guarantee, has_receipt, has_accessories,repair_note,repair_mode,cmis_folder)
        obj += str(vals).replace("''", "NULL").replace('"', "'") + ','

        logging.info("------> %s <------" % (total_row))

        if i >= 100:
            logging.info("________________________________________ %s _______________________________________" % (i))

            query = """INSERT INTO oscar_sav_claim (name, code,product_id, customer_id,magasin_id, user_id, problem_id,other,panne,date_purchase, date_claim, state, is_fixed, is_refused, is_back, is_exchanged, type, is_receive, has_guarantee, has_receipt, has_accessories,repair_note,repair_mode,cmis_folder) VALUES %s ON CONFLICT (name) DO NOTHING;""" % (obj[:-1])
            cursor_12.execute(query)
            obj = ''
            i = 0
            connection_12.commit()
            time.sleep(1)

    if i > 0:
        logging.info("________________________________________ %s _______________________________________" % (i))

        query = """INSERT INTO oscar_sav_claim (name, code,product_id, customer_id,magasin_id, user_id, problem_id,other,panne,date_purchase, date_claim, state, is_fixed, is_refused, is_back, is_exchanged, type, is_receive, has_guarantee, has_receipt, has_accessories,repair_note,repair_mode,cmis_folder) VALUES %s ON CONFLICT (name) DO NOTHING;""" %(obj[:-1])
        cursor_12.execute(query)
        obj = ''
        connection_12.commit()
        time.sleep(1)

    logging.info("CLAIMS CREATED     :  %s " % (total_row))
    logging.info("CUSTOMERS CREATED  :  %s " % (client))
    logging.info("PRODUCTS NOT FOUND :  %s " % (not_product))

    logging.info("______________________END CRON JOBS__________________________")

except (Exception, psycopg2.Error) as error:
    print ("Error while connecting to PostgreSQL", error)