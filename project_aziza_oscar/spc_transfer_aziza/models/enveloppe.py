# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError

STATE_ENVELOPE_SELECTION = [
    ('new', 'Nouvelle'),
    ('sent', 'Envoyée'),
    ('receive_warehouse', 'Reçue à l\'Entrepôt'),
    ('receive_siege', 'Reçue au Siège'),
    ('receive_store', 'Reçue au Magasin'),
]


class EnvelopeContent(models.Model):
    _name = 'oscar.envelope.content'
    _inherit = ['mail.thread']
    _order = "name"
    _rec_name = 'complete_name'

    name = fields.Char(string="Référence", required=True)
    code = fields.Char(string='Code')
    complete_name = fields.Char('Nom complet', compute='_compute_complete_name', store=True)
    parent_id = fields.Many2one('oscar.envelope.content', string="Contenu parent")
    child_ids = fields.One2many('oscar.envelope.content', 'parent_id', string='Enveloppes enfants')
    color = fields.Integer('Indice de couleur')
    type_go_site = fields.Selection([
        ('CENTRALE', 'Siège'),
        ('MAGASIN', 'Magasin'),
        ('ALL', 'Siège / Magasin'),
    ], string="Type destination d'aller", default='CENTRALE', help="Choisir le type de destination d'aller")
    site_id = fields.Many2one('oscar.site', string="Destination", index=True)
    has_reference = fields.Boolean('Numéro de référence requis')
    two_way_flow = fields.Boolean(string='flux à double sens')
    type_return_site = fields.Selection([
        ('MAGASIN', 'Magasin'),
        ('CENTRALE', 'Siège'),
    ], string='Type destination de retour', default='MAGASIN', help='Choisir le type de destination de retour')
    return_site_id = fields.Many2one('oscar.site', string="Destination de retour", index=True)
    isolated = fields.Boolean(string='Contenu isolé')
    active = fields.Boolean(string='Activé', default=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Le contenu d'enveloppe existe déjà !"),
    ]

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for content in self:
            if content.parent_id:
                content.complete_name = '%s / %s' % (content.parent_id.complete_name, content.name)
            else:
                content.complete_name = content.name

    @api.onchange('type_go_site')
    def _onchange_type_go_site(self):
        self.site_id = None
        if self.type_go_site:
            destinataire_ids = self.env['oscar.site'].search([('site_type', '=', self.type_go_site)])
            return {'domain': {'site_id': [('id', 'in', [dest_obj.id for dest_obj in destinataire_ids])]}}

    @api.onchange('type_return_site')
    def _onchange_type_return_site(self):
        self.return_site_id = None
        if self.type_return_site:
            destinataire_ids = self.env['oscar.site'].search([('site_type', '=', self.type_return_site)])
            return {'domain': {'return_site_id': [('id', 'in', [dest_obj.id for dest_obj in destinataire_ids])]}}


class Envelope(models.Model):
    _name = 'oscar.envelope'
    _description = 'Enveloppe'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"

    # endregion

    # region Default methods

    @api.model
    def _default_source(self):
        res = self.env['oscar.site'].search([('user_ids', 'child_of', [self.env.uid])], limit=1)
        return res

    # endregion

    # region Fields declaration
    name = fields.Char(string='Numéro enveloppe', readonly=True, copy=False, track_visibility='onchange')
    sending_date = fields.Date(string="Date d'envoi de l'enveloppe", required=True, default=fields.Date.context_today,
                               readonly=True, states={'new': [('readonly', False)]})
    date_reception = fields.Date(string="Date de réception de l'enveloppe", required=True,
                                 default=fields.Date.context_today, readonly=True,
                                 states={'new': [('readonly', False)]})
    date_creation = fields.Date(string='Date création Enveloppe', default=fields.Date.context_today, readonly=True,
                                index=True)
    source_id = fields.Many2one('oscar.site', string="Source", index=True, default=_default_source, readonly=True,
                                track_visibility='onchange')

    manual_filling = fields.Boolean(compute="_compute_destinataire_id")
    type_destinataire = fields.Char(string='Type destinataire', compute="_compute_destinataire_id")
    destinataire_id = fields.Many2one('oscar.site', string="Destinataire final",
                                      domain=[('site_type', 'in', ['MAGASIN', 'CENTRALE'])], index=True, required=False,
                                      readonly=True, states={'new': [('readonly', False), ('required', True)]},
                                      track_visibility='onchange')
    destination_intermediaire_ids = fields.Many2many('oscar.site', 'site_enveloppe_rel', 'site_id', 'enveloppe_id',
                                                     string='Destination intermédiaire', readonly=True)
    user_id = fields.Many2one('res.users', string='Utilisateur', index=True, default=lambda self: self.env.user,
                              readonly=True, states={'new': [('readonly', False)]})
    state = fields.Selection(STATE_ENVELOPE_SELECTION, string='Statut', readonly=True, copy=False, index=True,
                             default='new', track_visibility='onchange')
    content_envelope_ids = fields.Many2many('oscar.envelope.content', 'envelope_content_rel', 'enveloppe_id',
                                            'content_env_id', string="Contenu d'enveloppe", required=True,
                                            readonly=True, states={'new': [('readonly', False)]})
    print_date = fields.Date(string="Date d'impression", readonly=True)
    color = fields.Integer('Indice de couleur', default=0)
    reference_ids = fields.One2many('oscar.envelope.reference', 'envelope_id', string='Références', readonly=True,
                                    states={'new': [('readonly', False)]})
    references = fields.Char(string='Réferences', compute="_compute_references")
    bordereau_ids = fields.Many2many('oscar.bordereau', 'bordereau_envelope_rel', 'bordereau_id', 'envelope_id',
                                     string='Bordereaux')
    bordereau_count = fields.Integer(string='Nombre des bordereaux', compute="_compute_bordereau_count")
    bordereau_id = fields.Many2one('oscar.bordereau', compute='_compute_bordereau_id', string="Bordereau actuel",
                                   help="Dernier bordereau de l'enveloppe")
    active = fields.Boolean(string='Activée', default=True)

    # endregion

    # region Fields method

    @api.one
    @api.depends('reference_ids')
    def _compute_references(self):
        if self.reference_ids:
            refs = []
            for ref in self.reference_ids:
                refs.append(ref.name)
            self.references = str(refs).replace("'", "")

    @api.one
    @api.depends('bordereau_ids')
    def _compute_bordereau_count(self):
        self.bordereau_count = len(self.bordereau_ids.ids)

    def _compute_bordereau_id(self):
        """ get the lastest bordereau """
        Bordereau = self.env['oscar.bordereau']
        for envelope in self:
            envelope.bordereau_id = Bordereau.search([('envelope_ids', 'in', [envelope.id])], order='name desc',
                                                     limit=1)

    @api.depends('content_envelope_ids')
    def _compute_destinataire_id(self):
        if self.content_envelope_ids:
            tab = []
            two_way = False
            aller = False
            retour = False
            count_contents = len(self.content_envelope_ids.ids)
            for content in self.content_envelope_ids:
                if content.isolated and count_contents > 1:
                    raise ValidationError(
                        _("Vous ne pouvez pas sélectionner un autre contenu avec l'enveloppe %s!" %(content.name)))
                if content.two_way_flow:
                    if content.return_site_id in self.source_id or content.type_return_site == self.source_id.site_type:
                        aller = True
                        if content.site_id:
                            tab.append(content.site_id.id)
                        else:
                            self.manual_filling = True
                            self.type_destinataire = content.type_go_site
                    elif content.site_id in self.source_id or content.type_go_site == self.source_id.site_type:
                        retour = True
                        if content.return_site_id:
                            tab.append(content.return_site_id.id)
                        else:
                            self.manual_filling = True
                            self.type_destinataire = content.type_return_site
                else:
                    aller = True
                    if content.site_id:
                        tab.append(content.site_id.id)
                    else:
                        self.manual_filling = True
                        self.type_destinataire = content.type_go_site
            if tab:
                res = all(ele == tab[0] for ele in tab)
                if res:
                    self.destinataire_id = tab[0]
                else:
                    raise ValidationError(
                        _("Vous devez ne sélectionner que les enveloppes qui ont le même destinataire!"))

    @api.onchange('type_destinataire')
    def _onchange_type_destinataire(self):
        self.destinataire_id = None
        if self.type_destinataire in ['CENTRALE', 'MAGASIN']:
            destinataire_ids = self.env['oscar.site'].search([('site_type', '=', self.type_destinataire)])
            return {'domain': {'destinataire_id': [('id', 'in', [dest_obj.id for dest_obj in destinataire_ids])]}}
        elif self.type_destinataire == 'ALL':
            return {'domain': {'destinataire_id': [('site_type', 'in', ['MAGASIN', 'CENTRALE'])]}}

    # @api.onchange('content_envelope_ids')
    # def _onchange_content_envelope_ids(self):
    #     # Add envelope references
    #     if self.content_envelope_ids:
    #         self.reference_ids = [(5)]
    #         for content in self.content_envelope_ids:
    #             if content.child_ids:
    #                 for child in content.child_ids:
    #                     if child.has_reference:
    #                         self.reference_ids = [(0, 0,  {'content_envelope_id': child.id})]
    #             if content.has_reference and not content.child_ids:
    #                 self.reference_ids = [(0, 0,  {'content_envelope_id': content.id})]

    # endregion

    # region Constrains and Onchange

    @api.constrains('source_id', 'destinataire_id')
    def _check_source_not_destinataire(self):
        if self.source_id == self.destinataire_id:
            raise ValidationError(_("le destinataire et la source de l'enveloppe doivent être distincts"))

    @api.constrains('content_envelope_ids', 'reference_ids')
    def _check_references_envelope(self):
        if self.content_envelope_ids:
            for content in self.content_envelope_ids:
                if content.has_reference:
                    if len(self.reference_ids.ids) == 0:
                        raise ValidationError(_("Vous devez saisir la référence de l'enveloppe '%s'" % (content.name)))

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions methods for button
    @api.multi
    def imprimer_envelope(self):
        """ imprimer l'enveloppe
        """
        self.ensure_one()
        self.write({'print_date': fields.Date.today(), })
        return self.env.ref('spc_transfer_aziza.action_report_enveloppe').report_action(self)

    @api.multi
    def envoyer_envelope(self):
        if self.destinataire_id:
            for content in self.content_envelope_ids:
                if not content.two_way_flow:
                    if content.site_id != self.destinataire_id:
                        raise ValidationError(
                            _("Le destinataire final de l'enveloppe %s a été mal saisi!" % (self.name)))
        else:
            raise ValidationError(_("Le destinataire final de l'enveloppe %s n'a pas été saisi!" % (self.name)))
        return True

    @api.multi
    def recevoir_envelope(self):
        partially_receive = self.env.context.get('partially_receive', True)
        if self.env.uid not in self.bordereau_id.destinataire_id.user_ids.ids and not self.env.user.has_group(
                'spc_oscar_aziza.group_admin_oscar'):
            raise ValidationError(_("Vous n'avez pas l'autorisation de recevoir cette enveloppe %s !" % (self.name)))
        if self.bordereau_id.type_destinataire == 'warehouse':
            self.filtered(lambda s: s.state == 'sent').write({'state': 'receive_warehouse'})
        elif self.bordereau_id.type_destinataire == 'siege':
            self.filtered(lambda s: s.state == 'sent').write({'state': 'receive_siege'})
        elif self.bordereau_id.type_destinataire == 'store':
            self.filtered(lambda s: s.state == 'sent').write({'state': 'receive_store'})

        if partially_receive:
            if self.bordereau_id.verify_envelope_received():
                self.bordereau_id.filtered(lambda s: s.state in ['sent', 'partially_received']).write(
                    {'state': self.state, 'partially_received': False})
            else:
                self.bordereau_id.filtered(lambda s: s.state == 'sent').write(
                    {'state': 'partially_received', 'partially_received': True})
        return True

    # endregion

    # region Model methods
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('oscar.envelope')
        envelope = super(Envelope, self).create(vals)
        return envelope

    # endregion


class EnvelopeReference(models.Model):
    _name = 'oscar.envelope.reference'
    _description = 'Référence d\'enveloppe'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"

    # endregion

    # region Default methods

    # endregion

    # region Fields declaration
    name = fields.Char(string='Référence', required=True, track_visibility='onchange')
    confirm_name = fields.Char(string='Confirmer Réf')
    content_envelope_id = fields.Many2one('oscar.envelope.content', string="Contenu", required=True)
    envelope_id = fields.Many2one('oscar.envelope', string="Enveloppe", ondelete='cascade', index=True,
                                  track_visibility='onchange')
    user_id = fields.Many2one('res.users', string='Utilisateur', default=lambda self: self.env.user)

    # endregion

    # region Fields method

    # endregion

    # region Constrains and Onchange

    @api.constrains('name', 'confirm_name')
    def _check_name_equal_confirm_name(self):
        if self.name != self.confirm_name:
            raise ValidationError(_("Les réferences %s ne correspondent pas!" % (self.content_envelope_id.name)))

    # endregion

    # region CRUD (overrides)

    @api.model
    def create(self, vals):
        name = vals.get('name', False)
        if name:
            ref_envelope = self.env['oscar.envelope.reference'].search([('name', '=', name)])
            if ref_envelope:
                raise ValidationError(_("La référence saisie < %s > existe déjà !" % (name)))
        return super(EnvelopeReference, self).create(vals)

    # endregion

    # region Actions methods for button

    # endregion

    # region Model methods

    # endregion
