# -*- coding: utf-8 -*-

from odoo import models, api, _
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsxAbstract
from datetime import datetime

DEFAULT_DATE_FORMAT = '%Y-%m-%d'


class DerogationXlsReport(models.AbstractModel):
    """Class of equipment pickup xls report."""

    _name = 'report.spc_derogation_aziza.xlsx_report_derogation.xlsx'
    _inherit = 'report.report_xlsx.abstract'

    @api.model
    def generate_xlsx_report(self, workbook, data, objs):
        # construct of the xls report (workbook)
        worksheet = workbook.add_worksheet()
        row = 0
        col = 0

        # Header construct
        header = [_('Type'), _('Nom'), _('Responsable'), _('Date de création'), _('Date de dérogation')]
        header_format = workbook.add_format({'bold': True})
        for title in header:
            worksheet.write_string(row, col, title, header_format)
            col += 1
        row += 1

        for dero in objs:
            date_derogation = datetime.strptime(str(dero['date_derogation']), '%Y-%m-%d').strftime('%d-%m-%Y')
            create_date = datetime.strptime(str(dero['create_date']), "%Y-%m-%d %H:%M:%S.%f").strftime('%d-%m-%Y')
            worksheet.write(row, 0, dero['type'])
            worksheet.write(row, 1, dero['name'])
            worksheet.write(row, 2, dero['requested_by']['name'])
            worksheet.write(row, 3, create_date)
            worksheet.write(row, 4, date_derogation)
            row += 1


# DerogationXlsReport('report.spc_derogation_aziza.xlsx_report_derogation.xlsx', 'derogation.derogation')
