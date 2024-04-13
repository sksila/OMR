# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError

STATE_BORDEREAU_SELECTION = [
    ('new', 'Nouveau'),
    ('sent', 'Envoyé'),
    ('partially_received', 'Partiellement reçu'),
    ('receive_warehouse', 'Reçu à l\'Entrepôt'),
    ('receive_siege', 'Reçu au Siège'),
    ('receive_store', 'Reçu au Magasin'),
]


class Bordereau(models.Model):
    _name = 'oscar.bordereau'
    _description = 'Bordereau'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"


    # region Fields declaration

    name = fields.Char(string='Bordereau', readonly=True, track_visibility='onchange')
    date_bordereau = fields.Date(string='Date bordereau', required=True, default=fields.Date.context_today, readonly=True, states={'new': [('readonly', False)]})
    user_id = fields.Many2one('res.users', string='Utilisateur', index=True, default=lambda self: self.env.user, readonly=True, states={'new': [('readonly', False)]})
    state = fields.Selection(STATE_BORDEREAU_SELECTION, string='Statut', readonly=True, copy=False, index=True, default='new', track_visibility='onchange')
    sending_date = fields.Date(string="Date d'envoi de bordereau", readonly=True)
    envelope_ids = fields.Many2many('oscar.envelope', 'bordereau_envelope_rel', 'envelope_id', 'bordereau_id', string='Enveloppes', readonly=True, states={'new': [('readonly', False)]})
    envelope_count = fields.Integer("Nombre des enveloppes", compute="_compute_envelope_count")
    envelope_open_count = fields.Integer("Enveloppes Reçues", compute="_compute_envelope_count")
    fleet_id = fields.Many2one('fleet.vehicle', string='Véhicule', required=True, readonly=True, states={'new': [('readonly', False)]})
    chauffeur_id = fields.Many2one('res.partner',string="Chauffeur", domain=[('driver', '=', True)], index=True, readonly=True, states={'new': [('readonly', False)]})
    type_destinataire = fields.Selection([
        ('warehouse', 'Entrepôt'),
        ('store', 'Magasin'),
        ('siege', 'Siège'),
        ], string='Type du destinataire', default='warehouse', help='Choisir le type de chemin du bordereau', track_visibility='onchange', readonly=True, states={'new': [('readonly', False)]})
    destinataire_id = fields.Many2one('oscar.site', string="Destinataire",required=True, index=True, track_visibility='onchange', readonly=True, states={'new': [('readonly', False)]})
    source_id = fields.Many2one('oscar.site', string="Source", default=lambda self: self.env['oscar.site'].search([('user_ids', 'child_of', [self.env.uid])], limit=1), readonly=True, index=True, track_visibility='onchange')
    print_date = fields.Date(string="Date d'impression", readonly=True)
    partially_received = fields.Boolean(string='Partiellement reçu')
    active = fields.Boolean(string='Activé', default=True)

    # endregion

    @api.one
    @api.depends('envelope_ids')
    def _compute_envelope_count(self):
        self.envelope_count = len(self.envelope_ids.ids)
        self.envelope_open_count = sum(1 for env in self.envelope_ids if env.state in ['receive_siege','receive_store'])

    def verify_envelope_received(self):
        envelope_received_count = sum(1 for env in self.envelope_ids
                                      if (env.state in ['receive_warehouse', 'receive_siege', 'receive_store']
                                          and env.bordereau_id.id >= self.id)
                                      or (env.state == 'sent' and env.bordereau_id.id > self.id))
        if envelope_received_count == self.envelope_count:
            print("OK")
            return True
        else:
            print("NOT OK")
            return False



    # region Model methods

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('oscar.bordereau')
        res = super(Bordereau, self).create(vals)
        return res

    # endregion

    # region actions methods for button
    @api.multi
    def envoyer_bordereau(self):
        if self.envelope_ids:
            for enveloppe in self.envelope_ids:
                if self.destinataire_id != enveloppe.destinataire_id:
                    enveloppe.write({'destination_intermediaire_ids': [(4, self.destinataire_id.id)]})
                enveloppe.filtered(lambda s: s.state in ['new','receive_warehouse']).write({'state': 'sent'})
                enveloppe.envoyer_envelope()
        else:
            raise ValidationError("La liste des enveloppes est vide !")
        self.filtered(lambda s: s.state == 'new').write({'state': 'sent', 'sending_date': datetime.today().date()})


    @api.multi
    def recevoir_bordereau(self):
        if self.env.uid not in self.destinataire_id.user_ids.ids and not self.env.user.has_group(
                'spc_oscar_aziza.group_admin_oscar'):
            raise ValidationError(_("Vous n'avez pas l'autorisation de recevoir ce bordereau %s !" % (self.name)))
        if self.type_destinataire == 'warehouse':
            for envelope in self.envelope_ids:
                envelope.with_context({'partially_receive': False}).recevoir_envelope()
                self.filtered(lambda s: s.state in ['sent','partially_received']).write({'state': 'receive_warehouse'})

        elif self.type_destinataire == 'siege':
            for envelope in self.envelope_ids:
                envelope.with_context({'partially_receive': False}).recevoir_envelope()
                self.filtered(lambda s: s.state in ['sent','partially_received']).write({'state': 'receive_siege'})

        elif self.type_destinataire == 'store':
            for envelope in self.envelope_ids:
                envelope.with_context({'partially_receive': False}).recevoir_envelope()
                self.filtered(lambda s: s.state in ['sent','partially_received']).write({'state': 'receive_store'})

    @api.multi
    def imprimer_bordereau(self):
        """ imprimer le bordereau
        """
        self.ensure_one()
        self.write({'print_date': fields.Date.today(),})
        return self.env.ref('spc_transfer_aziza.oscar_bordereaux').report_action(self)

    # endregion
    # region Constrains and Onchange

    @api.constrains('envelope_ids','type_destinataire','source_id', 'destinataire_id')
    def _check_source_not_destinataire(self):
        if self.type_destinataire == 'store' and self.source_id.site_type == 'MAGASIN':
            raise ValidationError(_("Veuillez vérifier le type de destinataire!"))
        if self.source_id == self.destinataire_id:
            raise ValidationError(_("le destinataire et la source de bordereau doivent être distincts"))
        # if len(self.envelope_ids.ids) > 0:
        #     ele = self.envelope_ids[0]
        #     for env in self.envelope_ids:
        #         if ele.destinataire_id.id != env.destinataire_id.id:
        #             raise ValidationError(_("Le bordereau ne doit pas contenir des enveloppes avec des destinations différentes!"))
        if len(self.envelope_ids.ids) == 0:
            raise ValidationError(_("La liste des enveloppes est vide !"))

    @api.constrains('envelope_ids')
    def _check_envelope_ids(self):
        for ev in self.envelope_ids:
            if ev.state == 'new':
                domain = [('envelope_ids','in',[ev.id]),('id','!=',self.id)]
                count_br = self.search_count(domain)
                if count_br:
                    raise ValidationError(
                        _("L'enveloppe %s existe déjà dans un autre bordereau, veuillez vérifier !"%(ev.name)))


    @api.onchange('type_destinataire')
    def _onchange_destinataire_id(self):
        #si type_dest est un entrepot
        self.destinataire_id = None
        if self.type_destinataire == 'warehouse':
            destinataire_ids = self.env['oscar.site'].search([('site_type','=', 'ENTREPOT')])
            return {'domain': {'destinataire_id': [('id','in',[dest_obj.id for dest_obj in destinataire_ids])]}}
        #si no si type_dest est magasin
        elif self.type_destinataire == 'store':
            destinataire_ids = self.env['oscar.site'].search([('site_type','=', 'MAGASIN')])
            return {'domain': {'destinataire_id': [('id','in',[dest_obj.id for dest_obj in destinataire_ids])]}}
        #si non, type_det is siège
        else:
            destinataire_ids = self.env['oscar.site'].search([('site_type', '=', 'CENTRALE')])
            return {'domain': {'destinataire_id': [('id', 'in', [dest_obj.id for dest_obj in destinataire_ids])]}}

    # endregion

