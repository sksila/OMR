# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError


_STATES = [
    ('draft', 'Demande de dispatching'),
    ('to_approve', 'Approbation marchandise'),
    ('approved', 'Approbation exploitation'),
    ('verification', 'Dispatching exploitation'),
    ('verification_2', 'Vérification'),
    ('done', 'Clôturé'),
    ('rejected', 'Rejeté')
]


class Dispatch(models.Model):
    # region Private attributes
    _name = "oscar.dispatch"
    _description = "Dispatch"
    _inherit = ['mail.thread']
    _mail_post_access = 'read'
    _order = "id desc"
    # endregion

    # region Default and computed methods
    @api.one
    @api.depends('reset_ids')
    def _compute_reset_count(self):
        self.reset_count = len(self.reset_ids)
    # endregion



    # region Fields declaration
    name = fields.Char(string="Numéro", readonly=True)
    category_id = fields.Many2one('product.category', 'Categorie')
    sub_category_id = fields.Many2one('product.category', 'Famille')
    date_dispatch = fields.Datetime(string="Date", default=fields.Datetime.now, readonly=True)
    requested_by = fields.Many2one('res.users',
                                   string='Approvisionneur',
                                   default=lambda self: self.env.uid,
                                   index=True, track_visibility='always', readonly=True)
    approbateur_id = fields.Many2one('res.users',
                                     string='Approbateur',
                                     index=True, track_visibility='always', readonly=True)
    approbateur_exec_id = fields.Many2one('res.users',
                                          string='Approbateur execution',
                                          index=True, track_visibility='always', readonly=True)
    state = fields.Selection(selection=_STATES,
                             string='Status',
                             index=True,
                             track_visibility='onchange',
                             required=True,
                             copy=False,
                             default='draft')
    dispatch_lines = fields.One2many('oscar.dispatch.lines', 'dispatch_id', 'Lignes de dispatch')
    dispatch_lines_verification = fields.One2many('oscar.dispatch.lines.verification', 'dispatch_id', 'Lignes de dispatch')
    # Rejet de dispatching
    date_rejet = fields.Date('Date rejet', readonly=True)
    motif_rejet = fields.Text("Motif", readonly=True)
    reset_ids = fields.One2many('oscar.dispatch.reset', 'dispatch_id', string='Remettre')
    reset_count = fields.Integer('Reset', compute='_compute_reset_count')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.uid,)
    partner_id = fields.Many2one('res.partner', 'Partner')

    # endregion

    # region Fields method
    # endregion


    # region Constraints and Onchange
    # endregion

    # region CRUD (overrides)
    @api.model
    def create(self, vals):
        vals['name'] = 'Brouillon'
        return super(Dispatch, self).create(vals)

    @api.multi
    def unlink(self):
        for line in self:
            if line.state not in ('draft'):
                raise UserError(_('Vous ne pouvez pas supprimer une demande confirmée!'))

        return super(Dispatch, self).unlink()
    # endregion

    # region Actions
    def get_partner_ids_dispatch(self, group_id):
        group = self.env['res.groups'].browse(group_id)
        partner_ids = []
        for obj in group.users:
            if obj.partner_id.id:
                partner_ids.append(obj.partner_id.id)
        return partner_ids

    @api.multi
    def button_to_approve(self):
        for line in self:
            if not line.dispatch_lines:
                raise UserError(_('Vous ne pouvez pas envoyer une demande de dispatching sans lignes!'))
            if line.category_id.dlv_dlc_required:
                if not line.dlc:
                    raise UserError(_('le champs DLC doit etre mentionné!'))
        if self.reset_count == 0:

            self.name = self.env['ir.sequence'].get('dispatch.dispatch')
            print('here---')
            self.write({'state': 'to_approve'})
            partner_ids = self.get_partner_ids_dispatch(self.env.ref('spc_oscar_aziza.group_direction_approvisionnement').id)
            print('partner_ids--', partner_ids)
            template = self.env.ref('spc_dispatching_aziza.spc_email_template_dispatching')
            for partner_id in partner_ids:
                template.send_mail(self.id,
                                   force_send=True,
                                   email_values={'recipient_ids': [(4, partner_id)]},
                                   )

            return True
        else:
            self.write({'state': 'to_approve'})
            partner_ids = self.get_partner_ids_dispatch(self.env.ref('spc_oscar_aziza.group_direction_approvisionnement').id)
            print('partner_ids--', partner_ids)
            template = self.env.ref('spc_dispatching_aziza.spc_email_template_dispatching')
            for partner_id in partner_ids:
                template.send_mail(self.id,
                                   force_send=True,
                                   email_values={'recipient_ids': [(4, partner_id)]},
                                   )

            return True


    @api.multi
    def button_approved(self):
        for request in self:
            self.add_follower_exploitation()
        self.write({'state': 'approved',
                    'approbateur_id': self.env.uid})
        partner_ids = self.get_partner_ids_dispatch(self.env.ref('spc_oscar_aziza.group_DE').id)
        print('partner_ids--', partner_ids)
        template = self.env.ref('spc_dispatching_aziza.spc_email_template_dispatching')
        for partner_id in partner_ids:
            template.send_mail(self.id,
                               force_send=True,
                               email_values={'recipient_ids': [(4, partner_id)]},
                               )
        return True

    @api.multi
    def button_verification(self):
        for request in self:
            self.add_follower_execution()
            self.write({'state': 'verification',
                        'approbateur_exec_id': request.env.uid})
        partner_ids = self.get_partner_ids_dispatch(self.env.ref('spc_oscar_aziza.group_bo_oscar').id)
        print('partner_ids--', partner_ids)
        template = self.env.ref('spc_dispatching_aziza.spc_email_template_dispatching')
        for partner_id in partner_ids:
            template.send_mail(self.id,
                               force_send=True,
                               email_values={'recipient_ids': [(4, partner_id)]},
                               )
        return True
    @api.multi
    def button_verification_confirm_2(self):
        for rec in self.dispatch_lines:
            for line in rec.dispatch_lines_details_ids:
                if line.qty_dispatched == 0:
                    form_view_id = self.env.ref(
                        'spc_dispatching_aziza.wizard_confirmation_qty_dispached_exploitation_view', False).id
                    return {
                        'name': _('Confirmation'),
                        'context': self.env.context,
                        'type': 'ir.actions.act_window',
                        'res_model': self._name,
                        'view_mode': 'form',
                        'views': [(form_view_id, 'form')],
                        'view_id': form_view_id,
                        'res_id': self.id,
                        'target': 'new',
                    }

        self.write({'state': 'verification_2'})
        # partner_ids = self.get_partner_ids_dispatch(self.env.ref('spc_oscar_aziza.group_bo_oscar').id)
        # print('partner_ids--', partner_ids)
        template = self.env.ref('spc_dispatching_aziza.spc_email_template_dispatching')
        approvisionneur = self.requested_by
        print('approvisionneur---', approvisionneur)
        #ici,reste à ajouter le directeur de l'appro

        template.send_mail(self.id,
                           force_send=True,
                           email_values={'email_to': approvisionneur.email}
                           )
        return True

    @api.multi
    def button_verification_2(self):
        for rec in self.dispatch_lines:
            for line in rec.dispatch_lines_details_second_ids or rec.dispatch_lines_details_ids:
                if not line.motif_ecart:
                    raise UserError(_("Vous devez mentionné Le motif d'ecart 1 pour le produit %s dans l'entrepôt %s!")% (rec.product_id.name,line.entrepot_id.name))

        self.write({'state': 'verification_2'})
        return True

    @api.multi
    def button_done_confirm(self):
        for rec in self.dispatch_lines:
            for line in rec.dispatch_lines_details_second_ids or rec.dispatch_lines_details_ids:
                if not line.qty_reel_dispatched or line.qty_reel_dispatched == 0:
                    form_view_id = self.env.ref(
                        'spc_dispatching_aziza.wizard_confirmation_qty_relle_livre_appro_view', False).id
                    return {
                        'name': _('Confirmation'),
                        'context': self.env.context,
                        'type': 'ir.actions.act_window',
                        'res_model': self._name,
                        'view_mode': 'form',
                        'views': [(form_view_id, 'form')],
                        'view_id': form_view_id,
                        'res_id': self.id,
                        'target': 'new',
                    }
                else:
                    self.button_done()
        template = self.env.ref('spc_dispatching_aziza.spc_email_template_dispatching_cloture')
        approvisionneur = self.requested_by
        template.send_mail(self.id,
                           force_send=True,
                           email_values={'email_to': approvisionneur.email}
                           )
        return True

    @api.multi
    def button_done(self):
        for rec in self.dispatch_lines:
            for line in rec.dispatch_lines_details_second_ids or rec.dispatch_lines_details_ids:
                if not line.motif_ecart_reel:
                    raise UserError(_("Vous devez mentionné Le motif d'ecart 2 pour le produit %s dans l'entrepôt %s!")% (rec.product_id.name,line.entrepot_id.name))
                if line.motif_ecart_reel:
                    self.write({'state': 'done'})
        template = self.env.ref('spc_dispatching_aziza.spc_email_template_dispatching_cloture')
        approvisionneur = self.requested_by
        template.send_mail(self.id,
                           force_send=True,
                           email_values={'email_to': approvisionneur.email}
                           )
        return True

    @api.multi
    def button_rejected(self):
        return self.write({'state': 'rejected'})
    # endregion

    # region Model methods
    @api.multi
    def add_follower_approvisionneur(self, user_id):
        groups_id = self.env.ref('spc_oscar_aziza.group_achat_marchandise_aziza').id
        if not user_id.dispatch_approbateurs:
            raise UserError(_('Erreur, vous ne possedez pas de validateur, veuillez contacter votre administrateur!'))
        user = self.env['res.users'].search(
            [('groups_id', 'in', [groups_id]), ('id', 'in', [user_id.dispatch_approbateurs.ids])])
        subtypes = self.env['mail.message.subtype'].search([])
        if user:
            self.message_subscribe(partner_ids=user.ids, subtype_ids=subtypes.ids)

    @api.multi
    def add_follower_exploitation(self):
        groups_id = self.env.ref('spc_oscar_aziza.group_DE').id

        user = self.env['res.users'].search([('groups_id', 'in', [groups_id])])
        subtypes = self.env['mail.message.subtype'].search([])
        if user:
            self.message_subscribe(partner_ids=user.ids, subtype_ids=subtypes.ids)

    @api.multi
    def add_follower_execution(self):
        groups_id = self.env.ref('spc_oscar_aziza.group_DRE').id

        user = self.env['res.users'].search([('groups_id', 'in', [groups_id])])
        subtypes = self.env['mail.message.subtype'].search([])
        if user:
            self.message_subscribe(partner_ids=user.ids, subtype_ids=subtypes.ids)

    # endregion

class DispatchLines(models.Model):
    # region Private attributes
    _name = "oscar.dispatch.lines"
    _description = "Lignes de dispatch"
    _inherit = ['mail.thread']
    _mail_post_access = 'read'
    _order = "id desc"
    # endregion

    # region Fields declaration
    name = fields.Char('Nom')
    origin = fields.Char('Réf demande', related='dispatch_id.name')
    dispatch_id = fields.Many2one('oscar.dispatch', 'Dispatch')
    product_id = fields.Many2one('product.template', string='Code Article', required=True)
    designation_article = fields.Char('Designation Article', related='product_id.name', readonly=True, required=True,store=True)
    vl = fields.Char('VL', required=True)
    spcb = fields.Boolean('SPCB')
    pcb = fields.Boolean('PCB')
    unity = fields.Selection([
        ('spcb', 'SPCB'),
        ('pcb', 'PCB'),
        ('uvc', 'UVC'),
        ('palette', 'Palette'),
    ], string="Unité", required=True)
    dispatch_lines_details_ids = fields.One2many('oscar.dispatch.lines.details', 'dispatch_line_id', 'Détails de dispatch')
    dispatch_lines_details_second_ids = fields.One2many('oscar.dispatch.lines.details', 'dispatch_line_id', 'Détails de dispatch')
    total_qty_dispatched = fields.Integer("Total Qté  dispatchée", compute='_compute_qty')
    total_qty_qty_estimated = fields.Integer("Total Qté à dispatcher", compute='_compute_qty')
    total_qty_ecart = fields.Integer("Écart 1", compute='_compute_qty')
    requested_by = fields.Many2one('res.users',
                                   string='Approvisionneur',
                                   default=lambda self: self.env.uid,
                                   index=True, track_visibility='always', readonly=True,
                                   related='dispatch_id.requested_by')
    date_dispatch = fields.Datetime(string="Date", default=fields.Datetime.now, related='dispatch_id.date_dispatch')
    category_id = fields.Many2one('product.category', 'Categorie', related='product_id.categ_id.parent_id', required=True)
    sub_category_id = fields.Many2one('product.category', 'Famille', related='product_id.categ_id', required=True)
    state = fields.Selection(selection=_STATES,
                             string='Status',
                             index=True,
                             track_visibility='onchange',
                             default='draft',
                             copy=False,
                             store=True,
                             related='dispatch_id.state')
    oc_id = fields.Many2one('oscar.dispatch.oc', 'OC', required=True, index=True)
    qty_reel_dispatched = fields.Integer("Total Qté réellement livrée", compute="_compute_qty", store=True)
    qty_reel_ecart = fields.Integer("Écart 2", compute="_compute_qty", store=True)
    motif_id = fields.Many2one('oscar.dispatch.motif', 'Motif', required=True)
    contrat_id = fields.Many2one('oscar.product.spot', 'Spot', related='product_id.spot_id', required=True)
    dlc = fields.Date(string="DLC", required=True)

    # region Fields method
    @api.one
    @api.depends('dispatch_lines_details_ids.qty_estimated',
                 'dispatch_lines_details_ids.qty_dispatched',
                 'dispatch_lines_details_ids.qty_ecart',
                 'dispatch_lines_details_ids.qty_reel_dispatched',
                 'dispatch_lines_details_ids.qty_reel_ecart')
    def _compute_qty(self):
        self.ensure_one()
        for line in self:
            self.total_qty_qty_estimated = sum(line.dispatch_lines_details_ids.mapped('qty_estimated'))
            self.total_qty_dispatched = sum(line.dispatch_lines_details_ids.mapped('qty_dispatched'))
            self.total_qty_ecart = sum(line.dispatch_lines_details_ids.mapped('qty_ecart'))
            self.qty_reel_dispatched = sum(line.dispatch_lines_details_ids.mapped('qty_reel_dispatched'))
            self.qty_reel_ecart = sum(line.dispatch_lines_details_ids.mapped('qty_reel_ecart'))
    # endregion

    # region Constraints and Onchange
    @api.onchange('sub_category_id')
    def onchange_sub_category_id(self):
        self.category_id = self.sub_category_id.parent_id

    @api.multi
    @api.constrains('dlc')
    def _check_date_dlc(self):

        for line in self:
            date_dlc = line.dlc
            if date_dlc <= fields.Date.today():
                raise ValidationError(_("La date DLC de produit %s doit être supérieur à la date d'aujourd'hui!") % line.product_id.name)
    # endregion



class DispatchOC(models.Model):
    _name = "oscar.dispatch.oc"
    _description = "OC"

    name = fields.Char('Nom', required=True)
    annee = fields.Integer('Année')


class DispatchMotif(models.Model):
    _name = "oscar.dispatch.motif"
    _description = "Motif de dispatch"
    _inherit = ['mail.thread']
    _mail_post_access = 'read'
    _order = "id desc"

    name = fields.Char('Nom', required=True)
    description = fields.Char('Description')


class DispatchContrat(models.Model):
    _name = "oscar.dispatch.contrat"
    _description = "Contrat de dispatch"
    _inherit = ['mail.thread']
    _mail_post_access = 'read'
    _order = "id desc"

    name = fields.Char('Nom', required=True)


class DispatchVL(models.Model):
    _name = "dispatch.vl"
    _description = "VL"
    _inherit = ['mail.thread']
    _mail_post_access = 'read'
    _order = "id desc"

    name = fields.Char('Nom', required=True)
    description = fields.Text("Description")




