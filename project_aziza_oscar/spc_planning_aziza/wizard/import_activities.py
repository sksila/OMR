# -*- coding: utf-8 -*-

import xlrd
import logging
import tempfile
import binascii
from datetime import date, datetime, time, timedelta

from odoo import api, fields, models, tools, _
from odoo.exceptions import Warning, UserError, ValidationError

_logger = logging.getLogger(__name__)


class ImportActivity(models.TransientModel):
    _name = 'import.activity.wizard'
    _description = 'Import Activities'

    file_type = fields.Selection([('XLS', 'XLS File')], string='File Type', default='XLS')
    file = fields.Binary(string="Fichier")
    by_pass = fields.Boolean(default=True)

    def import_activity(self):
        if not self.file:
            raise ValidationError(_("Please Upload File to Import Activities !"))

        if self.file_type == 'XLS':
            try:
                file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
                file.write(binascii.a2b_base64(self.file))
                file.seek(0)
                values = {}
                workbook = xlrd.open_workbook(file.name)
                sheet = workbook.sheet_by_index(0)
            except Exception:
                raise ValidationError(_("Please Select Valid File Format !"))

            for row_no in range(sheet.nrows):
                val = {}
                if row_no <= 0:
                    fields = list(map(lambda row: row.value.encode('utf-8'), sheet.row(row_no)))
                else:
                    line = list(
                        map(lambda row: isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value),
                            sheet.row(row_no)))
                    print('row_1-----Activité-----', line[0])
                    print('row_2----Résumé------', line[1])
                    print('row_3-----date debut-----', line[2])
                    print('row_4----date fin------', line[3])
                    print('row_5----durée(en heures)------', line[4])
                    print('row_6-----toute la journé-----', line[5])
                    print('row_7------avant midi------', line[6])
                    print('row_8-----apres midi-----', line[7])
                    print('row_9-----Assigné à-----', line[8])
                    print('row_10-----Site-----', line[9])
                    print('row_11-----Région/Nom-----', line[10])
                    print('row_12-----Zone-----', line[11])
                    print('row_13-----Confidentialité-----', line[12])
                    print('row_14-----Groupes-----', line[13])
                    print('row_15----- Référence-----', line[14])
                    print('row_16----- by_mass-----', line[15])
                    print('********************************************')
                    print('********************************************')

                    activity = sheet.cell_value(row_no, 0)
                    print('activity---', activity)
                    summary = sheet.cell_value(row_no, 1)
                    print('summary---', summary)
                    allday = sheet.cell_value(row_no, 5)
                    print('allday---', allday)

                    # start_date
                    value = sheet.cell_value(row_no, 2)
                    start_date = datetime(*xlrd.xldate_as_tuple(value, workbook.datemode)).date()
                    print('start_date---', start_date)
                    start_date_1 = str(datetime(*xlrd.xldate_as_tuple(value, workbook.datemode)).date())
                    print('start_date_1---', start_date_1)

                    # stop_date
                    value = sheet.cell_value(row_no, 3)
                    stop_date = datetime(*xlrd.xldate_as_tuple(value, workbook.datemode)).date()
                    print('stop_date---', stop_date)

                    # start_datetime
                    start_datetime = datetime.strptime(start_date_1, "%Y-%m-%d") + timedelta(hours=7)
                    print('start_datetime----------', start_datetime)

                    duration = sheet.cell_value(row_no, 4)
                    print('duration---', duration)
                    avant_midi = sheet.cell_value(row_no, 6)
                    print('avant_midi---', avant_midi)
                    apres_midi = sheet.cell_value(row_no, 7)
                    print('apres_midi---', apres_midi)
                    assigned_to = sheet.cell_value(row_no, 8)
                    print('assigned_to---', assigned_to)
                    site_id = sheet.cell_value(row_no, 9)
                    print('site---', site_id)
                    region = sheet.cell_value(row_no, 10)
                    print('region---', region)
                    zone = sheet.cell_value(row_no, 11)
                    print('zone---', zone)
                    privacy = sheet.cell_value(row_no, 12)
                    print('privacy---', privacy)
                    groupe = sheet.cell_value(row_no, 13)
                    print('groupe---', groupe)
                    resource_ref = sheet.cell_value(row_no, 14)
                    print('resource_ref1---', resource_ref)
                    print('type_resource_ref', type(resource_ref))
                    type_site = sheet.cell_value(row_no, 16)
                    print('type_site---', type_site)

                    if duration == '0.5':
                        allday = False
                        duration = 4
                        if apres_midi == 1 and avant_midi == 0:
                            start_datetime = start_datetime + timedelta(hours=6)
                    else:
                        if allday == 1.0:
                            allday = True
                            duration = 8

                    # stop_date
                    stop_datetime = start_datetime + timedelta(hours=duration) - timedelta(seconds=1)
                    print('stop_datetime-------', stop_datetime)

                    if resource_ref == '#':
                        resource_ref = False

                    vals = {
                        'activity_type_id': activity,
                        'type_site': type_site,
                        'user_id': self.env.user.id,
                        'start_datetime': start_datetime,
                        'summary': summary,
                        'duration': duration,
                        'allday': allday,
                        'stop_datetime': stop_datetime,
                        'stop_date': stop_date,
                        'start_date': start_date,
                        'reccurrent': False,
                        'by_mass': line[15],
                        'site_id': site_id,
                        # 'user_ids': [(6, 0, [2, 6])],
                        'date_deadline': stop_date,
                        'assigned_to': assigned_to,
                        'privacy': privacy,
                        'resource_ref': resource_ref,
                        'by_pass': True,
                        # 'res_model_id': 74,
                        # 'res_id': 1,
                        # 'partner_ids': [[6, False, [3]]],
                        # 'activity_type_id': 1,# imporatnt pour la confidentialité
                        # 'start': start_datetime,
                        # 'stop': stop_datetime,

                    }

                    res = self.create_activity(vals)

    def create_activity(self, values):
        activity = self.env['mail.activity']

        activity_type_id = self.get_activity_id(values.get('activity_type_id'))
        print('activity_type_id---', activity_type_id)

        record_name = self.get_record_name(values.get('resource_ref'))
        print('get_record_name*****', record_name)
        description_model = self.get_description_model(values.get('resource_ref'))
        print('get_description_model*****', description_model)


        res_model_id = self.get_res_model_id(values.get('resource_ref'))
        print('res_model_id*****', res_model_id)
        res_id = self.get_res_id(values.get('resource_ref'))
        print('res_id2*****', res_id)
        if res_model_id and res_id:
            resource_ref = '% s,% s' % (res_model_id, res_id)
        else:
            resource_ref = False

        site_id = self.get_magsain(values.get('site_id'))
        if values.get('site_id') == '':
            raise Warning(_('Champ Magasin est vide !'))
        region_id = self.get_region(values.get('site_id'))
        if values.get('region_id') == '':
            raise Warning(_('Champ région est vide !'))
        zone_id = self.get_zone(values.get('site_id'))
        if values.get('zone_id') == '':
            raise Warning(_('Champ Zone est vide !'))

        user_ids = []
        if values.get('by_mass') == 'by_group':
            group_id = self.get_group_id(values.get('by_mass'), values.get('assigned_to'))
            print('group_id_1---', group_id)
            group_id = group_id
        # user_ids = self.env['res.users'].search([('groups_id', '=', group_id.id)]).ids
        else:
            group_id = False
        if values.get('by_mass') == 'individual':
            user_ids = self.get_user_ids(values.get('by_mass'), values.get('assigned_to'))
            print('user_ids---', user_ids)
            user_ids = [user_ids]

        vals = {
            'activity_type_id': activity_type_id,
            'type_site': values.get('type_site'),
            'user_id': self.env.user.id,
            'start_datetime': values.get('start_datetime'),
            'summary': values.get('summary'),
            'duration': values.get('duration'),
            'allday': values.get('allday'),
            'stop_datetime': values.get('stop_datetime'),
            'stop_date': values.get('stop_date'),
            'start_date': values.get('start_date'),
            'reccurrent': False,
            'by_mass': values.get('by_mass'),
            'site_id': site_id.id,
            'zone_id': zone_id.id,
            'region_id': region_id.id,
            'user_ids': [(6, 0, user_ids)],
            'date_deadline': values.get('date_deadline'),
            'resource_ref': resource_ref,
            'res_model_id': 74,
            'res_id': 1,
            'partner_ids': [[6, False, [3]]],
            # 'activity_type_id': 1,# imporatnt pour la confidentialité
            'start': values.get('start'),
            'stop': values.get('stop'),
            'group_id': group_id,
            'by_pass': True,

        }
        print('vals******', vals)

        res = activity.create(vals)
        return res

    def get_magsain(self, site_id):
        if site_id:
            print('name*************', site_id)
            code_magasin = site_id[1:5]
            site_id = self.env['oscar.site'].search([('code', '=', code_magasin)], limit=1)
            print('magasin----', site_id)
            if site_id:
                return site_id
            else:
                raise UserError(_('"%s" Cette magasin is not found in system !') % code_magasin)

    def get_zone(self, site_id):
        code_magasin = site_id[1:5]
        zone_id = self.env['oscar.site'].search([('code', '=', code_magasin)], limit=1).zone_id
        print('zone_id----', zone_id.name)
        if zone_id:
            return zone_id
        else:
            raise UserError(_('"%s" cette région n\'est pas trouvé dans le système !') % zone_id.name)

    def get_region(self, site_id):
        code_magasin = site_id[1:5]
        region_id = self.env['oscar.site'].search([('code', '=', code_magasin)], limit=1).region_id
        print('region_id----', region_id.name)
        if region_id:
            return region_id
        else:
            raise UserError(_('"%s" cette zone n\'est pas trouvé dans le système !') % region_id.name)

    def get_group_id(self, by_mass, assigned_to):
        print('by_mass----', by_mass)
        print('assigned_to----', assigned_to)
        if by_mass == 'by_group':
            if assigned_to in 'Exploitation / Responsable Magasin / Adjoint':

                group_id = self.env['res.groups'].search([('name', 'like', 'Responsable Magasin')])
                print('get_group_id---', group_id)
                group_id = group_id.id
                return group_id
            else:
                return False

    def get_user_ids(self, by_mass, assigned_to):
        if by_mass == 'individual':
            user_id = self.env['res.users'].search([('name', 'like', assigned_to)])
            user_ids = user_id.id
            return user_ids

    def get_activity_id(self, activity_type_id):
        if activity_type_id:
            activity_type_id = self.env['mail.activity.type'].search([('name', 'like', activity_type_id)]).id
            print('activity_id2---', activity_type_id)
        return activity_type_id

    # methode qui permet d'avoir le nom de record par exemple
    # pour l'audit elle extraire le nom de la session à partir de colonne reference.
    # input : resource_ref = session d'audit / Fiche de controle de la temperature
    # output : model_name = Fiche de controle de la temperature
    def get_record_name(self, resource_ref):
        s = resource_ref
        letter = "/"
        if resource_ref != False:
            for i, c in enumerate(s):
                if c == letter:
                    print("/ est présent à l'indice ", i + 1)
                    indice = i + 1
            print('indice record_name-----', indice)
            model_name = s[indice:]
            print('model_name', model_name)
            return model_name

    # methode qui permet d'avoir le nom de record par exemple
    # pour l'audit elle extraire le nom de la session à partir de colonne reference.
    # input: reference = session d'audit / Fiche de controle de la temperature
    # output : model_name = session d'audit

    def get_description_model(self, resource_ref):
        s = resource_ref
        letter = "/"
        if resource_ref != False:
            for i, c in enumerate(s):
                if c == letter:
                    print("/ est présent à l'indice ", i + 1)
                    indice = i + 1
            print('indice description_model-----', indice)
            description_model = s[:indice - 1]
            if description_model:
                description_model = description_model.lstrip()
                description_model = description_model.rstrip()
                print('description_model', description_model)
                return description_model

    # methode qui permet d'avoir le model de n'importe quel reference
    #input: reference = session d'audit / Fiche de controle de la temperature
    #output : model = spc_survey.session
    def get_model(self, resource_ref):
        description_model = self.get_description_model(resource_ref)
        print('description_model get_model', description_model)
        model = self.env['ir.model'].search([('name', '=', description_model)]).model
        print('model----', model)
        return model


    # methode qui permet d'avoir le modèle (model_name)pour remplir le champs reference(model_name, record_id)
    # chercher dans l'objet model, celui qui correspond au model qui est déja extracté à partir de la colonne reference
    def get_res_model_id(self, resource_ref):
        print('*********get_res_model_id***********')
        print('*********resource_ref10***********', resource_ref)
        if resource_ref != False:
            print('****if1*****')
            model = self.get_model(resource_ref)
            res_model_id = self.env['ir.model'].search([('model', '=', model)], limit=1).model
            print('*****res_model_id/get_res_model_id*******', res_model_id)
            return res_model_id

    # methode qui permet d'avoir l'id de record de l'objet (record_id)pour remplir le champs reference(model_name, record_id)
    # chercher dans l'id de record, celui qui correspond au model qui est déja extracté à partir de la colonne referene
    def get_res_id(self, resource_ref):
        print('*********resource_ref20***********', resource_ref)
        record_name = self.get_record_name(resource_ref)
        print('*********record_name***********', record_name)
        model = self.get_model(resource_ref)
        print('*********model2***********', model)

        if record_name:
            record_name = record_name.lstrip()
            record_name = record_name.rstrip()
        if resource_ref != False:
            print('****if20****')
            res_id = self.env[model].search([('name', 'ilike', record_name)], limit=1).id
            print('***res_id get_res_id****', res_id)
            return res_id
