import psycopg2
import psycopg2.extras
import time
import logging
logging.basicConfig(format='Date-Time : %(asctime)s : Line No. : %(lineno)d - %(message)s', \
                    level = logging.INFO)

logging.info("______________________StART CRON JOBS__________________________")

# lot1 = ('1070','1098','1306') 10/20
# lot2 = ('1176','1181','1357','1180') 14/12
# lot3 = ('1090','1124','1194','1183','1277','1299','1305') 17/12
# lot4 = ('1182','1206','1093','1107','1379','1175','1163','1114','1137','1147','1208') 24/12
# lot5 = ('1075','1106','1109','1126','1198','1195','1259','1311','1312') 25/12
# lot6 = ('1102','1023','1218','1050','1027','1105') 13/01
# lot7 = ('1021','1125','1276','1144') 16/01

try:
    connection_10 = psycopg2.connect(user="odoo", password="Aziza21022018", host="172.17.1.47", port="5432", database="aziza")
    cursor_10 = connection_10.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    print("SELECT COMMANDES")
    cursor_10.execute("SELECT name,  code_site, lib_site, lib_fr, code_fr, date_commande::date, active FROM commande_gold WHERE code_site in ('1021','1125','1276','1144')") #magasin_id,
    records_10 = cursor_10.fetchall()
#     print('recodes10-----------', records_10)

    connection_12 = psycopg2.connect(user="odoo12", password="Aziza22072019", host="172.17.1.53", port="5432", database="oscar_v12")
    cursor_12 = connection_12.cursor()
    total_row = 0
    obj = ''
    i = 0
    for record in records_10:
        i = i + 1
        total_row += 1
        try:
            query = '''SELECT id FROM public.oscar_site WHERE code='%s';'''%(record['code_site'])
            mg_query = cursor_12.execute(query)
            mg_id = cursor_12.fetchall()[0][0]
        except Exception:
            mg_id = ''
        if not record['code_site']:
            code_site = ''
        else:
            code_site = record['code_site']
        if not record['lib_fr']:
            lib_fr = ''
        else:
            lib_fr = record['lib_fr']
        if not record['code_fr']:
            code_fr = ''
        else:
            code_fr = record['code_fr']
        if not record['date_commande']:
            date_commande = ''
        else:
            date_commande = record['date_commande']

        vals = (record['name'],code_site,mg_id, str(lib_fr), code_fr, str(date_commande), True)
        # print('vals------', vals)
        obj += str(vals).replace("''", "NULL").replace("L'AVENIR","L AVENIR").replace('"',"'") + ','
        logging.info("------> %s <------"%(total_row))
        if i >= 1000:
            logging.info("________________________________________ %s _______________________________________"%(i))
            query = """INSERT INTO commande_gold (name, code_site, magasin_id, lib_fr, code_fr, date_commande, active) VALUES %s ON CONFLICT (name) DO NOTHING;"""%(obj[:-1])
            print('QUERY  :', query)
            cursor_12.execute(query)
            obj = ''
            i=0
            connection_12.commit()
            time.sleep(1)

    if i > 0:
        logging.info("________________________________________ %s _______________________________________"%(i))
        query = """INSERT INTO commande_gold (name, code_site, magasin_id, lib_fr, code_fr, date_commande, active) VALUES %s ON CONFLICT (name) DO NOTHING;"""%(obj[:-1])
        cursor_12.execute(query)
        obj = ''
        connection_12.commit()
        time.sleep(1)
       
    print()
    logging.info("TOTAL RECORDS < %s >"%(total_row))
    logging.info("______________________END CRON JOBS__________________________")

    # Print PostgreSQL Connection properties
    # print ( connection_10.get_dsn_parameters(),"\n")
    # print(connection_12.get_dsn_parameters(), "\n")

except (Exception, psycopg2.Error) as error:
    print ("Error while connecting to PostgreSQL", error)