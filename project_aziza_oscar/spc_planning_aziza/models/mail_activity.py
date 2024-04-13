# -*- coding: utf-8 -*-

from odoo import api ,models, fields, _
from odoo.exceptions import ValidationError
from odoo.addons.mail.models.mail_activity import MailActivity as MailActivitySite
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat
import time
import datetime

from datetime import timedelta, MAXYEAR
VIRTUALID_DATETIME_FORMAT = "%Y%m%d%H%M%S"



def calendar_id2real_id(calendar_id=None, with_date=False):
    """ Convert a "virtual/recurring event id" (type string) into a real event id (type int).
        E.g. virtual/recurring event id is 4-20091201100000, so it will return 4.
        :param calendar_id: id of calendar
        :param with_date: if a value is passed to this param it will return dates based on value of withdate + calendar_id
        :return: real event id
    """
    if calendar_id and isinstance(calendar_id, pycompat.string_types):
        res = [bit for bit in calendar_id.split('-') if bit]
        if len(res) == 2:
            real_id = res[0]
            if with_date:
                real_date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT, time.strptime(res[1], VIRTUALID_DATETIME_FORMAT))
                start = datetime.datetime.strptime(real_date, DEFAULT_SERVER_DATETIME_FORMAT)
                end = start + timedelta(hours=with_date)
                return (int(real_id), real_date, end.strftime(DEFAULT_SERVER_DATETIME_FORMAT))
            return int(real_id)
    return calendar_id and int(calendar_id) or calendar_id

class MailActivity(models.Model):
    _inherit = "mail.activity"

    # region Default methods
    @api.model
    def default_get(self, fields):
        result = super(MailActivity, self).default_get(fields)
        if not fields or 'site_id' in fields:
            result['site_id'] = self.env['oscar.site'].search([('user_ids', 'child_of', [self.env.uid])], limit=1).id
        return result
    # endregion

    # region Fields declaration
    site_id = fields.Many2one('oscar.site', string='Site')
    region_id = fields.Many2one('oscar.region', string='Région')
    zone_id = fields.Many2one('oscar.zone', string='Zone')
    type_site = fields.Selection([
        ('SITE', 'Site'),
        ('REGION', 'Région'),
        ('ZONE', 'Zone'),
    ], string='Type', default='SITE')

    group_id = fields.Many2one('res.groups', 'Groupe', index=True,
                               domain=lambda self: [('category_id.id', '=', self.env.ref('spc_oscar_aziza.module_exploitation_aziza').id)])

    # endregion


    def _get_site(self, type, val):
        sites = []
        if type == 'SITE':
            sites.append(val)
        elif type == 'REGION':
            search_sites = self.env['oscar.site'].sudo().search([('region_id','=',val)])
            sites += search_sites.ids
        elif type == 'ZONE':
            search_sites = self.env['oscar.site'].sudo().search([('zone_id','=',val)])
            sites += search_sites.ids
        print('sites****', sites)
        return sites

    # region Constraints and Onchange
    @api.onchange('type_site')
    def onchange_type_site(self):
        res = {}
        if self.type_site == 'SITE':
            self.by_mass = 'individual'
        else:
            self.by_mass = 'by_group'
        site_ids = self.env.user.magasin_ids
        region_ids = []
        zone_ids = []
        if not site_ids:
            all_site_ids = self.env['oscar.site'].search([]).ids
            res = {'domain': {'site_id': [('id', 'in', all_site_ids)]}}
        if site_ids and self.type_site == 'SITE' and not self.env.user.has_group("spc_oscar_aziza.group_admin_oscar"):
            res = {'domain': {'site_id': [('id', 'in', site_ids.ids)]}}
        for rec in site_ids:
            region_ids.append(rec.region_id.id)
            zone_ids.append(rec.zone_id.id)
            if self.type_site == 'REGION':
                res = {'domain': {'region_id': [('id', 'in', region_ids)]}}
            if self.type_site == 'ZONE':
                res = {'domain': {'zone_id': [('id', 'in', zone_ids)]}}
        return res

    @api.onchange('site_id')
    def onchange_site(self):
        #si on change le site, un domain s'applique sur l'utilisateur(selement les utilisateurs de site choisi et les
        #utilisateurs de site choisi et les utilisateurs qui n'ont pas de site s'affiche)
        res = {}
        if self.site_id:
            user_for_all_site = self.env['res.users'].search([])
            # ----liste des utilisateurs qui n'ont pas de site----
            user_without_site = self.env['res.users'].search([('magasin_ids','=', False)])
            # ----liste des utilisateurs de site choisi----
            site_user_ids = self.env['oscar.site'].search([('id', '=', self.site_id.id)]).user_ids
            all_site_user_ids = site_user_ids + user_without_site
            # ----liste des utilisateurs de group admin----
            user_types_category = self.env.ref('spc_oscar_aziza.module_exploitation_aziza', raise_if_not_found=False)
            user_name_group_admin = self.env.ref('spc_oscar_aziza.group_admin_oscar', raise_if_not_found=False)
            group_admin_id = self.env['res.groups'].search([('category_id', '=', user_types_category.id),('id', '=', user_name_group_admin.id)]).users
            site_without_group_admin_ids = all_site_user_ids - group_admin_id

            if self.env.user.has_group("spc_oscar_aziza.group_admin_oscar"):
                res = {'domain': {'user_ids': [('id', 'in', [user.id for user in user_for_all_site])]}}
            else:
                res = {'domain': {'user_ids': [('id', 'in', [user.id for user in site_without_group_admin_ids])]}}
            return res

    @api.constrains('user_id', 'start_datetime', 'stop_datetime', 'site_id')
    def _check_same_activity(self):
        for activity in self:
            domain = [
                ('start_datetime', '<', activity.stop_datetime),
                ('stop_datetime', '>', activity.start_datetime),
                ('user_id', '!=', activity.user_id.id),
                ('site_id', '=', activity.site_id.id),
                ('activity_type_id', '=', activity.activity_type_id.id),
                ('id', '!=', activity.id),
            ]
            nbr_activity = self.search_count(domain)
            # if nbr_activity:
            #     raise ValidationError(_('Cette activité est occupé par un autre responsable!'))
    # endregion

    # region CRUD (overrides)
    # à voir ou à supprimer methode create_managers
    #Create Managers for utilisateur
    @api.multi
    def create_managers(self):
        current_user = self.env.user
        result = {}
        for meeting in self:
            meeting_managers = self.env['manager.user']
            meeting_users = self.env['res.users']
            user = meeting.user_id
            if meeting.site_id:
                site_manager = self.env['oscar.site'].search([('id', '=', meeting.site_id.id)])
                if current_user.has_group('spc_oscar_aziza.group_reponsable_magasin'):
                    resp_zone_id = site_manager.resp_zone_id
                    values = {
                        'user_id': resp_zone_id.id,
                        'email': resp_zone_id.email,
                        'activity_id': meeting.id,
                    }
                    attendee = self.env['manager.user'].create(values)
                    meeting_managers |= attendee
                    meeting_users |= user

                    if meeting_managers and not self._context.get('detaching'):
                        to_notify = meeting_managers.filtered(lambda a: a.email != current_user.email)
                        # to_notify._send_mail_to_managers('spc_activity.spc_template_notification_by_email_manager')

                    if meeting_managers:
                        meeting.write(
                            {'manager_ids': [(4, meeting_manager.id) for meeting_manager in meeting_managers]})

                    if meeting_users:
                        meeting.message_subscribe(partner_ids=meeting_users.ids)

                    # We remove old managers who are not in partner_ids now.
                    all_partners = meeting.user_id
                    all_partner_managers = meeting.manager_ids.mapped('user_id')
                    old_managers = meeting.manager_ids
                    partners_to_remove = all_partner_managers + meeting_users - all_partners

                    managers_to_remove = self.env["manager.user"]
                    if partners_to_remove:
                        managers_to_remove = self.env["manager.user"].search([('user_id', 'in', partners_to_remove.ids), ('activity_id', '=', meeting.id)])

                    result[meeting.id] = {
                        'new_managers': meeting_managers,
                        'old_managers': old_managers,
                        'removed_managers': managers_to_remove,
                        'removed_partners': partners_to_remove
                    }
                if current_user.has_group('spc_oscar_aziza.group_reponsable_zone'):
                    dre_id = site_manager.dre_id
                    values = {
                        'user_id': dre_id.id,
                        'email': dre_id.email,
                        'activity_id': meeting.id,
                    }
                    attendee = self.env['manager.user'].create(values)
                    meeting_managers |= attendee
                    meeting_users |= user

                    if meeting_managers and not self._context.get('detaching'):
                        to_notify = meeting_managers.filtered(lambda a: a.email != current_user.email)
                        # to_notify._send_mail_to_managers('spc_activity.spc_template_notification_by_email_manager')

                    if meeting_managers:
                        meeting.write(
                            {'manager_ids': [(4, meeting_manager.id) for meeting_manager in meeting_managers]})

                    if meeting_users:
                        meeting.message_subscribe(partner_ids=meeting_users.ids)

                    # We remove old managers who are not in partner_ids now.
                    all_partners = meeting.user_id
                    all_partner_managers = meeting.manager_ids.mapped('user_id')
                    old_managers = meeting.manager_ids
                    partners_to_remove = all_partner_managers + meeting_users - all_partners

                    managers_to_remove = self.env["manager.user"]
                    if partners_to_remove:
                        managers_to_remove = self.env["manager.user"].search([('user_id', 'in', partners_to_remove.ids), ('activity_id', '=', meeting.id)])

                    result[meeting.id] = {
                        'new_managers': meeting_managers,
                        'old_managers': old_managers,
                        'removed_managers': managers_to_remove,
                        'removed_partners': partners_to_remove
                    }

                if current_user.has_group('spc_oscar_aziza.group_DRE'):
                    group_DE_id = self.env['ir.model.data'].xmlid_to_res_id('spc_oscar_aziza.group_DE')
                    group_admin_id = self.env['ir.model.data'].xmlid_to_res_id('spc_oscar_aziza.group_admin_oscar')
                    group_DE = self.get_users_from_group(group_DE_id)
                    group_admin = self.get_users_from_group(group_admin_id)
                    group_DE = [item for item in group_DE if item not in group_admin]
                    de_id = self.env['res.users'].browse(group_DE)
                    values = {
                        'user_id': de_id.id,
                        'email': de_id.email,
                        'activity_id': meeting.id,
                    }

                    attendee = self.env['manager.user'].create(values)
                    meeting_managers |= attendee
                    meeting_users |= user
                    if meeting_managers and not self._context.get('detaching'):
                        to_notify = meeting_managers.filtered(lambda a: a.email != current_user.email)
                        # to_notify._send_mail_to_managers('spc_activity.spc_template_notification_by_email_manager')

                    if meeting_managers:
                        meeting.write({'manager_ids': [(4, meeting_manager.id) for meeting_manager in meeting_managers]})

                    if meeting_users:
                        meeting.message_subscribe(partner_ids=meeting_users.ids)

                    # We remove old managers who are not in partner_ids now.
                    all_partners = meeting.user_id
                    all_partner_managers = meeting.manager_ids.mapped('user_id')
                    old_managers = meeting.manager_ids
                    partners_to_remove = all_partner_managers + meeting_users - all_partners

                    managers_to_remove = self.env["manager.user"]
                    if partners_to_remove:
                        managers_to_remove = self.env["manager.user"].search([('user_id', 'in', partners_to_remove.ids), ('activity_id', '=', meeting.id)])
                    result[meeting.id] = {
                        'new_managers': meeting_managers,
                        'old_managers': old_managers,
                        'removed_managers': managers_to_remove,
                        'removed_partners': partners_to_remove
                    }
            return result

    @api.model
    def create(self, values):
        print("CREATE WITH ZONE")
        if self._context.get("by_pass"):
            if values['type_site'] == 'ZONE' and values['zone_id']:
                for site in self._get_site('ZONE', values['zone_id']):
                    if values['by_mass'] == 'by_group' and values['group_id']:
                        print('group : ', values['group_id'])
                        print('site : ', site)
                        users_affected = self.env['res.users'].search(
                            [('groups_id', 'in', [values['group_id']]), ('magasin_ids', 'in', [site])])
                        print("users_affected : ", users_affected)
                        if users_affected:
                            values.update({
                                'type_site': 'ZONE',
                                'site_id': site,
                                'user_ids': [(6, 0, users_affected.ids)],
                            })
                        else:
                            values.update({
                                'type_site': 'ZONE',
                                'site_id': site,
                            })
                        for rec in users_affected:
                            values.update({
                                'user_id': rec.id,
                                'copy_val': True,

                            })
                            activity = super(MailActivity, self).create(values)
                return activity
            if values['type_site'] == 'REGION' and values['region_id']:
                for site in self._get_site('REGION', values['region_id']):
                    print('region---')

                    if values['by_mass'] == 'by_group' and values['group_id']:
                        print('group : ', values['group_id'])
                        print('site : ', site)
                        users_affected = self.env['res.users'].search(
                            [('groups_id', 'in', [values['group_id']]), ('magasin_ids', 'in', [site])])
                        print("users_affected : ", users_affected)
                        if users_affected:
                            values.update({
                                'type_site': 'REGION',
                                'site_id': site,
                                'user_ids': [(6, 0, users_affected.ids)],
                            })
                        else:
                            values.update({
                                'type_site': 'REGION',
                                'site_id': site,
                            })
                        for rec in users_affected:
                            values.update({
                                'user_id': rec.id,
                                'copy_val': True,

                            })
                            activity = super(MailActivity, self).create(values)
                return activity
            if values['by_mass'] == 'by_group' and values['group_id'] :
                for site in self._get_site('SITE', values['site_id']):
                    print('SITE---')

                    print('group : ', values['group_id'])
                    print('site : ', site)
                    users_affected = self.env['res.users'].search(
                        [('groups_id', 'in', [values['group_id']]), ('magasin_ids', 'in', [site])])
                    print("users_affected_by_site: ", users_affected)
                    if users_affected:
                        values.update({
                            'type_site': 'SITE',
                            'site_id': site,
                            'user_ids': [(6, 0, users_affected.ids)],
                        })
                    for rec in users_affected:
                        print('rec', rec)
                        values.update({
                            'user_id': rec.id,
                            'copy_val': True,

                        })
                        print('number***')
                        activity = super(MailActivity, self).create(values)
                return activity
            if values['by_mass'] == 'individual' and values['site_id']:
                for site in self._get_site('SITE', values['site_id']):
                    print('individual site ---------')
                    users_affected = values['user_ids'][0][2]
                    print("users_affected : ", users_affected)
                    if users_affected:
                        values.update({
                            'type_site': 'SITE',
                            # 'site_id': site,
                            'user_ids': [(6, 0, users_affected)],
                        })
                    for rec in users_affected:
                        print('rec', rec)
                        values.update({
                            'user_id': rec,
                            'copy_val': True,

                        })
                        print('number***')
                        activity = super(MailActivity, self).create(values)
                return activity
        else:
            print('ELSE FINAL')
            activity = super(MailActivity, self).create(values)
        return activity
        # activity.with_context(dont_notify=True).create_managers()



    @api.multi
    def create_task_site(self, deadline, start, stop):
        values = self.create_task(deadline, start, stop)
        site_vals = {
            'site_id': self.site_id.id,
        }
        values.update(site_vals or {})

    @api.multi
    def write(self, values):
        res = super(MailActivity, self).write(values)
        # if values.get('user_id' or 'user_ids', False):
        #     self.create_managers()
        return res

    @api.multi
    def read(self, fields=None, load='_classic_read'):

        if not fields:
            fields = list(self._fields)
        fields2 = fields and fields[:]
        EXTRAFIELDS = ('privacy', 'user_id', 'duration', 'allday', 'start', 'rrule', 'group_ids')
        for f in EXTRAFIELDS:
            if fields and (f not in fields):
                fields2.append(f)

        select = [(x, calendar_id2real_id(x)) for x in self.ids]
        real_events = self.browse([real_id for calendar_id, real_id in select])
        real_data = super(MailActivitySite, real_events).read(fields=fields2, load=load)
        real_data = dict((d['id'], d) for d in real_data)

        result = []
        for calendar_id, real_id in select:
            if not real_data.get(real_id):
                continue
            res = real_data[real_id].copy()
            ls = calendar_id2real_id(calendar_id, with_date=res and res.get('duration', 0) > 0 and res.get('duration') or 1)
            if not isinstance(ls, (pycompat.string_types, pycompat.integer_types)) and len(ls) >= 2:
                res['start'] = ls[1]
                res['stop'] = ls[2]

                if res['allday']:
                    res['start_date'] = ls[1]
                    res['stop_date'] = ls[2]
                else:
                    res['start_datetime'] = ls[1]
                    res['stop_datetime'] = ls[2]

                if 'display_time' in fields:
                    res['display_time'] = self._get_display_time(ls[1], ls[2], res['duration'], res['allday'])

            res['id'] = calendar_id
            result.append(res)
        # group of user
        current_user = self.env.user.id
        group_current_user = self.env['res.users'].search([('id', '=', current_user)]).groups_id.ids
        for dict_activity in result:
            group_ids = dict_activity['group_ids']
            check = any(item in group_ids for item in group_current_user)

            if dict_activity['user_id']:
                user_id = type(dict_activity['user_id']) in (tuple, list) and dict_activity['user_id'][0] or dict_activity['user_id']
                if user_id == self.env.user.id or (dict_activity['privacy'] == 'by_group' and check is True):
                    continue
            if dict_activity['privacy'] == 'private' or (dict_activity['privacy'] == 'by_group' and check is False):
                for f in dict_activity:
                    recurrent_fields = self._get_recurrent_fields()
                    public_fields = list(set(recurrent_fields + ['id', 'allday', 'start', 'stop', 'display_start', 'display_stop', 'duration', 'state', 'interval', 'count', 'recurrent_id_date', 'rrule','date_deadline','site_id']))
                    if f not in public_fields:
                        if isinstance(dict_activity[f], list):
                            dict_activity[f] = []
                        else:
                            dict_activity[f] = False
                    if f == 'summary':
                        dict_activity[f] = _('Busy')

        for dict_activity in result:
            for k in EXTRAFIELDS:
                if (k in dict_activity) and (fields and (k not in fields)):
                    del dict_activity[k]

        return result

    # endregion

    # region Actions
    @api.multi
    def to_validate(self):
        user = self.env.user
        if user:
            if (self.activity_type_id.is_validated is True) and not user.has_group(
                    'spc_activity.group_responsable_planification'):
                raise ValidationError('Vous ne pouvez pas valider cette tâche!')
            else:
                self.ensure_one()

                template_obj = self.env['mail.template'].sudo().search([('name', '=', 'Retour email au responsable de la tache apres validation')], limit=1)
                name_user = ''
                for p in self.user_ids:
                    name_user = name_user + ',' + p.name
                    name_user = name_user[1:]
                partner_ids = []
                for obj in self.user_ids:
                    if obj.partner_id.id:
                        partner_ids.append(obj.partner_id.id)

                body_html = '<p>Bonjour '  ',<br />' \
                            ' La validation de votre tâche %s est approuvée. <br />' % (self.summary)

                if template_obj:
                    mail_values = {
                        'subject': _('Tâche validée: %s') % (self.summary),
                        'body_html': body_html,
                        'recipient_ids': [(4, pid) for pid in partner_ids]
                    }
                    create_and_send_email = self.env['mail.mail'].create(mail_values).send()
                return self.write({'workflow_activity': 'validated'})

    @api.multi
    def to_do(self):
        self.ensure_one()

        template_obj = self.env['mail.template'].sudo().search([('name', '=', 'Envoie email au Manager au cloture')], limit=1)
        name_user = ''
        for p in self.user_ids:
            name_user = name_user + ',' + p.name
            name_user = name_user[1:]
        partner_ids = []
        for obj in self.activity_type_id.manager_ids:
            if obj.partner_id.id:
                partner_ids.append(obj.partner_id.id)

        body_html = '<p>Bonjour '  ',<br />' \
        ' La tâche %s qui a été assigné à %s dans le site %s est terminée. <br />' % (self.summary, name_user, self.site_id.name)

        if template_obj:
            mail_values = {
                'subject': _('Tâche terminée: %s') % (self.summary),
                'body_html': body_html,
                'recipient_ids': [(4, pid) for pid in partner_ids]
            }
            create_and_send_email = self.env['mail.mail'].create(mail_values).send()
        return self.write({'workflow_activity': 'done'})
    # endregion


class OscarSiteCalendar(models.Model):
    _name = 'oscar.site.calendar'

    user_id = fields.Many2one('res.users', 'Me', required=True, default=lambda self: self.env.user)
    site_calendar_id = fields.Many2one('oscar.site', 'Site')
    active = fields.Boolean('Active', default=True)