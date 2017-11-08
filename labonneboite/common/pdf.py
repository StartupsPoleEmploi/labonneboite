# coding: utf8
import errno
import logging
import os
import StringIO

from flask import render_template
from slugify import slugify
from xhtml2pdf import pisa

from labonneboite.common import util
from labonneboite.conf import settings
from labonneboite.conf.common.contact_mode import CONTACT_MODE_STAGES

logger = logging.getLogger('main')


def get_file_path(office):
    return os.path.join(settings.GLOBAL_STATIC_PATH, "pdf",
                        office.departement, office.naf, slugify(office.name.strip()[0]),
                        "%s.pdf" % office.siret)


def write_file(office, data):
    filename = get_file_path(office)
    if not os.path.exists(os.path.dirname(filename)):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc:
            # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
    with open(filename, "w") as f:
        f.write(data)
    f.close()
    logger.info("wrote PDF file to %s", filename)


def delete_file(office):
    filename = get_file_path(office)
    if os.path.exists(filename):
        os.remove(filename)


def render(office, rome=None):
    """
    If necessary, render an office to pdf and save to disk.

    Args:
        office (Office)
        rome (str or None)
    Return: path to generated pdf file.
    """
    full_path = get_file_path(office)
    if not os.path.exists(full_path):
        contact_mode = util.get_contact_mode_for_rome_and_naf(rome, office.naf)
        stages = CONTACT_MODE_STAGES[contact_mode]
        pdf_data = render_template(
            'office/pdf_detail.html', company=office,
            contact_mode=contact_mode, stages=stages
        )
        write_file(office, convert_to_pdf(pdf_data).getvalue())

    return full_path


def render_favorites(offices):
    """
    Render the list of companies as favorites.

    Return: a file-like object.
    """
    companies = [
        (company, util.get_contact_mode_for_rome_and_naf(None, company.naf)) for company in offices
    ]
    pdf_data = render_template(
        'office/pdf_list.html', companies=companies,
    )
    return convert_to_pdf(pdf_data)


def convert_to_pdf(pdf_data):
    """
    Convert a str to pdf

    Return: a file-like object
    """
    pdf_target = StringIO.StringIO()
    pisa.CreatePDF(
        StringIO.StringIO(pdf_data), pdf_target,
        link_callback=lambda uri, rel: "https://%s%s" % (settings.HOST, uri)
    )
    pdf_target.seek(0)
    return pdf_target
