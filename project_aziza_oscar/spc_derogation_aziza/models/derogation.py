# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
from datetime import date, datetime, timedelta

_STATES = [
    ('draft', 'Demande de derogation'),
    ('to_approve', 'Marchandises'),
    ('controle_gestion', 'CG'),
    ('approve_exp', 'Exploitation'),
    ('approve_quality', 'Qualité'),
    ('approve_dg', 'DG'),
    ('magasin', 'Magasin'),
    ('retour_fournisseur', 'Retour Fournisseur'),
    ('rejected', 'Rejected'),
    ('done', 'Clôturée')
]


class Derogation(models.Model):
    _name = "derogation.derogation"
    _description = "Derogation"
    _inherit = ['mail.thread']
    _mail_post_access = 'read'
    _order = "id desc"

    # region Default methods
    @api.one
    def compute_total_quantity(self):
        self.total_quantity = sum(line.quantity for line in self.derogation_line_ids)

    @api.one
    @api.depends('reset_ids')
    def _compute_reset_count(self):
        self.reset_count = len(self.reset_ids)

    @api.multi
    @api.depends('date_dlv_actuel', 'taux_couverture')
    def compute_date_dlv_new(self):
        for derog in self:
            if derog.date_dlv_actuel:
                date_1 = datetime.strptime(str(derog.date_dlv_actuel), '%Y-%m-%d')
                if derog.taux_couverture and derog.taux_couverture.isdigit():
                    derog.date_dlv_new = (date_1 + timedelta(days=int(derog.taux_couverture))).date()
                else:
                    return False

    @api.one
    @api.depends('qty_derogation')
    def _compute_total_qty_derog(self):
        self.qty_derogation = sum(self.mapped('product_ids').mapped('qty_derogation'))


    @api.depends('responsable_magasin_id')
    def get_current_user(self):
        self.responsable_magasin_id = self._context.get('uid')
        responsable_magasin_id = self.responsable_magasin_id.id
        magasin_id = self.env['oscar.site'].search([('user_id', '=', responsable_magasin_id)], limit=1)
        code = magasin_id.code
        if code and magasin_id:
            self.magasin_id = str(code) + "-" + magasin_id.name
        pass
    # endregion

    # region Fields  declaration
    name = fields.Char('Réf', readonly=True)
    date_derogation = fields.Date(string="Date", default=date.today(), readonly=True, required=True)
    date_dlc = fields.Date(string="DLC ")
    code_produit = fields.Many2one('product.template', 'Code Produit', required=True)
    produit = fields.Char('Libellé Produit', related='code_produit.name' ,required=True)
    category_id = fields.Many2one('product.category', 'Categorie', related='code_produit.categ_id.parent_id',required=True)
    vl_product = fields.Char('VL', required=True, help="Le VL a comme valeur un nombre décimale de 1 jusqu'à 8")
    fournisseur = fields.Many2one('res.partner', 'Fournisseur', domain="[('supplier','=',True)]", required=True)
    requested_by = fields.Many2one('res.users',
                                   string='Approvisionneur',
                                   default=lambda self: self.env.uid,
                                   index=True, track_visibility='always',
                                   readonly=True, required=True)
    qty_magasin = fields.Integer('Qté magasin UVC')
    qty_entrepot = fields.Integer('Qté entrepôt UVC')
    qty_derogation = fields.Integer('Qté Totale UVC', compute='_compute_total_qty_derog', strore=True)
    qty_retounee = fields.Integer('Qté retournée UVC', compute='_compute_qty_retounee', strore=True)
    montant = fields.Float(string='Montant avoir', compute='_compute_montant_avoir', digits=(12, 3), strore=True)
    confomity = fields.Text('Non-conformité', readonly=True)
    origin = fields.Selection([('local', 'Local'), ('import', 'Import')], string='Origine', default='local',
                              required=True)
    date_dlv_actuel = fields.Date(string="DLV actuelle")
    operation_speciale = fields.Char('Opération spéciale')
    taux_couverture = fields.Char('Taux de couverture')
    date_dlv_new = fields.Date(string="Date nouvelle DLV", compute="compute_date_dlv_new", readonly=True)
    commentaire_achat = fields.Text('Marchandise')
    commentaire_exploitation = fields.Text('Exploitation')
    commentaire_dqp = fields.Text('Qualité')
    commentaire_magasin = fields.Text('Magsin')
    type = fields.Selection(
        [('dlv_reception', 'DLV expirée réception'), ('dlv_entrepot', "DLV expirée entrepôt"),
         ('produit', 'Non conformité produit'), ('retrait_produit', 'Retrait produit')], string='Type', required=True)
    qty_partielle = fields.Integer('Qté partielle UVC')
    reset_ids = fields.One2many('derogation.reset', 'derogation_id', string='Remettre')
    reset_count = fields.Integer('Reset', compute='_compute_reset_count')
    state = fields.Selection(selection=_STATES,
                             string='Status',
                             index=True,
                             track_visibility='onchange',
                             required=True,
                             copy=False,
                             default='draft')
    # added by salwa
    state_dlv_reception = fields.Selection(related='state', track_visibility=False)
    state_dlv_entrepot = fields.Selection(related='state', track_visibility=False)
    state_produit = fields.Selection(related='state', track_visibility=False)
    state_retrait_produit = fields.Selection(related='state', track_visibility=False)
    prix_revient = fields.Float(string="Prix de revient UVC")
    cout_stockage = fields.Float(string="Coût de stockage")
    cout_logistique = fields.Float(string="Coût logistique")
    montant_recu = fields.Float(string="Montant reçu")
    image = fields.Binary('Joindre une image', readonly=True)
    derogation_line_ids = fields.One2many('derogation.derogation.line', 'derogation_id')
    quantity = fields.Float(string="Quantité")
    magasin_id = fields.Char(string="Magasin", compute='get_current_user', readonly=True)
    responsable_magasin_id = fields.Many2one('res.users', 'Responsable magasin', compute='get_current_user',
                                             readonly=True)
    bon_retour = fields.Char(string="Bon de retour")
    total_quantity = fields.Float(string="Quantité Totale Magasin", compute="compute_total_quantity")
    description = fields.Text(string="Description")
    option_envoie_fournisseur = fields.Selection([('dlc', 'DLC'), ('fin_operation', 'Date fin opération')],
                                                 string="Date envoie magasin ", default='dlc')
    date_fin_operation = fields.Date(string="Date fin opération")
    is_zero = fields.Boolean()
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.uid,)
    partner_id = fields.Many2one('res.partner', 'Partner')
    product_ids = fields.One2many('spc_derog.product', 'derog_product_id', 'Articles')
    is_inv = fields.Boolean(compute="_set_button_retour_four_inv",
                            help="rendre le bouton valider visible seleumement pour l'approvisonneur qui a crée la demande")
    # endregion

    # region Fields method
    @api.one
    @api.depends('state')
    def _set_button_retour_four_inv(self):
        for rec in self:
            if (rec.requested_by == rec.env.user and self.state == "magasin") and (self.requested_by.has_group('spc_oscar_aziza.group_approvisioneur_aziza') \
                    or self.requested_by.has_group('spc_oscar_aziza.group_direction_approvisionnement')):
                self.is_inv = False
            else:
                self.is_inv = True


    @api.multi
    @api.depends('qty_magasin', 'qty_entrepot')
    def _compute_qty_retounee(self):
        for derog in self:
            if derog.qty_magasin and derog.qty_magasin:
                derog.qty_retounee = derog.qty_magasin + derog.qty_entrepot

    @api.multi
    @api.depends('prix_revient', 'qty_retounee', 'cout_stockage', 'cout_logistique')
    def _compute_montant_avoir(self):
        for derog in self:
            cout_total = derog.cout_stockage + derog.cout_logistique
            derog.montant = (derog.prix_revient * derog.qty_retounee) + cout_total

    def check_numval(self):
        val = self.taux_couverture
        if val and val.isdigit() or isinstance(val, bool):
            return True
        else:
            return False
    _constraints = [(check_numval, "La valeur d'entrée de taux de couverture n'est pas correcte!\n Cette valeur doit être un nombre", ['taux_couverture']), ]

    # endregion

    # region Contranints
    @api.multi
    @api.constrains('qty_derogation', 'qty_partielle')
    def _check_qty_derogation_partielle(self):
        qty_derogation = self.qty_derogation
        qty_partielle = self.qty_partielle
        if qty_derogation and qty_partielle:
            if qty_partielle > qty_derogation:
                raise ValidationError(_('La Qté partielle doit être inférieure à la Qté total !'))

    @api.multi
    @api.constrains('qty_partielle', 'qty_retounee')
    def _check_qty_partielle_retounee(self):
        qty_partielle = self.qty_partielle
        qty_retounee = self.qty_retounee
        if qty_retounee and qty_partielle:
            if qty_retounee > qty_partielle:
                raise ValidationError(_('La Qté retournée doit être inférieure à la Qté partielle !'))

    @api.multi
    @api.constrains('date_dlc', 'date_fin_operation')
    def _check_date_fin_operation(self):
        date_dlc = self.date_dlc
        date_fin_operation = self.date_fin_operation
        if date_dlc and date_fin_operation:
            if date_fin_operation > date_dlc:
                raise ValidationError(_('La date fin opération doit être inférieure à la date DLC !'))

    @api.multi
    @api.constrains('date_dlc')
    def _check_date_dlc(self):
        date_dlc = self.date_dlc
        if date_dlc <= fields.Date.today():
            raise ValidationError(_("La date DLC doit être supérieur de la date d'aujourd'hui!"))

    @api.multi
    @api.constrains('date_dlv_new', 'date_dlv_actuel')
    def _check_date_dlv(self):
        start_date = self.date_dlv_actuel
        end_date = self.date_dlv_new

        if start_date and end_date:
            if start_date > end_date:
                raise ValidationError(_('The new dlv date must be superior to the actuel dlv date !'))

    @api.multi
    @api.constrains('date_dlv_actuel', 'date_dlc')
    def _check_date_dlc_dlv(self):
        start_date = self.date_dlv_actuel
        end_date = self.date_dlc

        if start_date and end_date:
            if start_date > end_date:
                raise ValidationError(_('La date DLV actuelle doit être inférieure à la date DLC !'))

    @api.constrains('derogation_line_ids')
    def _check_unique_magasin_in_list(self):
        for rec in self.derogation_line_ids[:len(self.derogation_line_ids) - 1]:
            if self.responsable_magasin_id in rec.responsable_magasin_id:
                raise ValidationError("Le responsable de cet magasin existe déja!")


    # endregion

    # region of private methods
    @api.multi
    def open_wizard_add_quantity(self):
        """Ouvrir un popup pour l'ajout de quantité pour chaque magasin"""
        self.ensure_one()
        form_view_id = self.env.ref('spc_derogation_aziza.wizard_add_quantity_view', False).id
        return {
            'name': _('Ajouter quantité'),
            'context': self.env.context,
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'views': [(form_view_id, 'form')],
            'view_id': form_view_id,
            'res_id': self.id,
            'target': 'new',
        }

    @api.multi
    def button_send_mail(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('spc_derogation_aziza', 'email_template_derogation')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = {
            'default_model': 'derogation.derogation',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'force_email': True,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def send_mail_template(self):
        # Find the e-mail template
        template = self.env.ref('spc_derogation_aziza.email_template_derogation')
        # Send out the e-mail template to the user
        template.send_mail(self.id, force_send=True)

    @api.multi
    def add_quantity(self):
        """Ajouter la quantité de produit pour chaque magasin """
        if self.quantity == 0:
            self.is_zero = True
        else:
            self.is_zero = False
        derogation_line_ids = {
            'quantity': self.quantity,
            'magasin_id': self.magasin_id,
            'responsable_magasin_id': self.responsable_magasin_id,
            'bon_retour': self.bon_retour,
        }
        self.derogation_line_ids = [(0, 0, derogation_line_ids)]

    @api.model
    def edit_state_magasin(self):
        for der in self.search([('state', 'in', (
                'draft', 'to_approve', 'controle_gestion', 'approve_exp', 'approve_quality', 'approve_dg'))]):
            if der.option_envoie_fournisseur == 'dlc' and der.date_dlc and der.date_dlc == fields.Date.today():
                der.write({'state': 'magasin'})
            if der.option_envoie_fournisseur == 'fin_operation' and der.date_fin_operation and der.date_fin_operation == fields.Date.today():
                der.write({'state': 'magasin'})
        for der in self.search([('state', '=', 'magasin'), ('date_dlc', '=', fields.Date.today())]):
            der.send_mail_template()
        for der in self.search([('state', '=', 'magasin'), ('date_fin_operation', '=', fields.Date.today())]):
            der.send_mail_template()

    # endregion

    # region on change methods
    @api.onchange('code_produit')
    def produit_fournisseur_onchange(self):
        for rec in self:
            return {'domain': {'fournisseur': [('id', 'in', rec.code_produit.supplier_ids.ids)]}}

    @api.model
    def onchange_type(self, vals):
        if vals['is_type_retrait']:
            vals.extend([('retrait_produit', 'Retrait produit')])
        else:
            vals.extend([('dlv_reception', 'DLV expirée réception')])
        return vals


    @api.multi
    @api.onchange('qty_retounee')
    def _onchange_qty_retournee(self):
        if self.qty_retounee == 0:
            self.montant = 0.0
    # endregion

    # region CRUD(overrides)
    @api.model
    def create(self, vals):
        vals['name'] = 'Brouillon'
        if self.env.user.has_group('spc_oscar_aziza.group_quality_product_aziza') and not self.env.user.has_group('spc_oscar_aziza.group_admin_oscar') and (vals['type'] != 'retrait_produit'):
            raise UserError(_('Vous ne pouvez créer que une note de retrait!'))
        elif self.env.user.has_group('spc_oscar_aziza.group_quality_product_aziza') and not self.env.user.has_group('spc_oscar_aziza.group_admin_oscar') and (vals['type'] == 'retrait_produit'):
            vals['name'] = self.env['ir.sequence'].next_by_code('derogation.derogation')
            return super(Derogation, self).create(vals)
        elif (vals['type'] == 'retrait_produit') and not self.env.user.has_group('spc_oscar_aziza.group_quality_product_aziza'):
            raise UserError(_("Vous n'avez pas le droit de créer une note de retrait!"))
        else:
            return super(Derogation, self).create(vals)

    @api.multi
    @api.model
    def write(self, vals):
        if self.state == 'retour_fournisseur' and not (self.env.user.has_group('spc_derogation_aziza.group_approvisioneur_aziza') or not self.env.user.has_group('spc_derogation_aziza.group_direction_approvisionnement')):
            raise ValidationError("Vous n'avez pas le droit de modifier cette demande !")
        return super(Derogation, self).write(vals)

    @api.multi
    def unlink(self):
        for order in self:
            if order.state not in ('draft'):
                raise UserError(_('Vous ne pouvez pas supprimer une demande confirmée!'))
        return super(Derogation, self).unlink()

    # endregion

    # region actions methods for button
    @api.multi
    def button_draft(self):
        return self.write({'state': 'draft'})

    def get_partner_ids(self, group_id):
        group = self.env['res.groups'].browse(group_id)
        partner_ids = []
        for obj in group.users:
            if obj.partner_id.id:
                partner_ids.append(obj.partner_id.id)
        return partner_ids

    @api.multi
    def button_to_approve(self):
        self.name = self.env['ir.sequence'].get('derogation.derogation')
        self.write({'state': 'to_approve'})
        partner_ids = self.get_partner_ids(self.env.ref('spc_oscar_aziza.group_direction_approvisionnement').id)
        template = self.env.ref('spc_derogation_aziza.spc_email_template_derog')
        for partner_id in partner_ids:
            template.send_mail(self.id,
                                 force_send=True,
                                 email_values={'recipient_ids': [(4, partner_id)]},
                                 )

        return True


    @api.multi
    def button_quality_to_approve_exp(self):
        return self.write({'state': 'approve_exp'})

    @api.multi
    def button_approve_achat(self):
        if self.type == 'dlv':
            if self.origin == 'import':
                self.write({'state': 'controle_gestion'})
            else:
                self.write({'state': 'approve_exp'})
        else:
            if self.origin == 'import':
                self.write({'state': 'controle_gestion'})
            else:
                self.write({'state': 'approve_quality'})
        return True

    @api.multi
    def button_approve_exp(self):
        self.write({'state': 'approve_quality'})
        return True

    @api.multi
    def button_approve_cg(self):
        if self.type == 'dlv':
            self.write({'state': 'approve_exp'})
        else:
            self.write({'state': 'approve_quality'})
        return True

    @api.multi
    def button_approve_quality(self):
        self.write({'state': 'approve_dg'})
        return True

    @api.multi
    def button_retour_fournisseur(self):
        if self.state == 'magasin':
            if (self.option_envoie_fournisseur == 'dlc' and self.date_dlc and self.date_dlc != fields.Date.today()) or \
                    (self.option_envoie_fournisseur == 'fin_operation' and
                     self.date_fin_operation and self.date_fin_operation != fields.Date.today()):
                raise ValidationError(
                    _("Il faut que la DLC de produit ou bien date fin opération est celui d'aujourd'hui!"))
            else:
                self.write({'state': 'retour_fournisseur'})
                template = self.env.ref('spc_derogation_aziza.spc_email_template_derog')
                user = self.env['res.users'].browse(self.env.context.get('uid', self.env.uid))
                template.send_mail(self.id,
                                   force_send=True,
                                   email_values={'email_to': user.email,}
                                   )

                return True

    @api.multi
    def button_to_done(self):
        if (self.qty_magasin == 0 or self.qty_entrepot == 0 or self.qty_retounee == 0 or self.prix_revient == 0 or self.cout_stockage == 0 or self.cout_logistique == 0 or self.montant_recu == 0) and self.env.user.has_group('spc_oscar_aziza.group_approvisioneur_aziza') and self.state == 'retour_fournisseur':
            form_view_id = self.env.ref('spc_derogation_aziza.wizard_confirmation_view', False).id
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
            return self.write({'state': 'done'})

    @api.multi
    def button_done(self):
        self.write({'state': 'done'})
        partner_ids = self.get_partner_ids(self.env.ref('spc_oscar_aziza.group_dg').id)
        template = self.env.ref('spc_derogation_aziza.spc_email_template_derog_cloture')
        for partner_id in partner_ids:
            template.send_mail(self.id,
                               force_send=True,
                               email_values={'recipient_ids': [(4, partner_id)]},
                               )
        return True

    @api.multi
    def button_rejected(self):
        return self.write({'state': 'rejected'})
    # endregion
