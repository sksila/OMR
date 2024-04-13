from datetime import timedelta

from odoo import models, fields, api, exceptions


class Session(models.Model):
    _name = 'openacademy.session'

    name = fields.Char(required=True)
    start_date = fields.Date(string='Start date', default=fields.Date.today())
    end_date = fields.Date(string='End date', compute='_get_end_date',
                           inverse='_set_end_date')
    duration = fields.Float(digits=(6, 2), help='Duration in days')
    seats = fields.Integer(string='Number of seats')
    taken_seats = fields.Float(string='Taken seats', compute='_taken_seats')
    active = fields.Boolean(default=True)
    instructor_id = fields.Many2one("res.partner", string='Instructor',
                                    domain=['!',
                                            ('instructor', '=', True),
                                            ('category_id.name', 'ilike', 'Teacher')])
    course_id = fields.Many2one("openacademy.course", string='Course',
                                ondelete='cascade', required=True)
    attendee_ids = fields.Many2many("res.partner",
                                    column1='session_id', column2='attendee_id',
                                    string='Attendees')
    attendees_count = fields.Integer(string='Attendees count',
                                     compute='_get_attendees_count',
                                     store=True)
    color = fields.Integer()

    @api.depends('attendee_ids')
    def _get_attendees_count(self):
        for record in self:
            record.attendees_count = len(record.attendee_ids)

    @api.depends('start_date', 'duration')
    def _get_end_date(self):
        for record in self:
            if not (record.start_date and record.duration):
                record.end_date = record.start_date
                continue

            duration = timedelta(days=record.duration)
            record.end_date = record.start_date + duration
            pass

    def _set_end_date(self):
        pass

    @api.depends('seats', 'attendee_ids')
    def _taken_seats(self):
        for record in self:
            if not record.seats:
                record.taken_seats = 0
            else:
                record.taken_seats = 100 * len(record.attendee_ids) / record.seats

    @api.onchange('seats', 'attendee_ids')
    def _verify_valid_seats(self):
        if self.seats < 0:
            return {
                'warning': {
                    'title': 'Invalid seats value',
                    'message': 'The number of seats may not be negative'
                }
            }
        if len(self.attendee_ids) > self.seats:
            return {
                'warning': {
                    'title': 'Too many attendees',
                    'message': 'Increase seats or remove excess attendees'
                }
            }

    @api.constrains('instructor_id', 'attendee_ids')
    def _check_constructor_not_in_attendees(self):
        for record in self:
            if record.instructor_id and record.instructor_id in record.attendee_ids:
                raise exceptions.ValidationError("A session's instructor can't be an attendee")
