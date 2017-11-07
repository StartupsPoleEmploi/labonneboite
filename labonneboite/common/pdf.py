# coding: utf8
import errno
import logging
import os
import io

from flask import render_template
from slugify import slugify
from xhtml2pdf import pisa

from labonneboite.common import util
from labonneboite.conf import settings
from labonneboite.web import WEB_DIR

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
    with open(filename, "wb") as f:
        f.write(data)
    f.close()
    logger.debug("wrote PDF file to %s", filename)


def delete_file(office):
    filename = get_file_path(office)
    if os.path.exists(filename):
        os.remove(filename)


def convert_to_pdf(pdf_data):
    """
    Convert a str to pdf
    Return: a file-like object
    """
    pdf_target = io.BytesIO()
    # The link callback is a function that is used to determine the path of
    # local static assets required to generate the pdf. This should not point
    # to http://labonneboite.
    link_callback = lambda uri, rel: os.path.join(WEB_DIR, uri.strip("/"))
    pisa.CreatePDF(
        io.StringIO(pdf_data), dest=pdf_target,
        link_callback=link_callback
    )
    pdf_target.seek(0)
    return pdf_target


def render_favorites(offices):
    """
    Render the list of companies as favorites.

    Return: a file-like object.
    """
    companies = [
        (company, util.get_contact_mode_for_rome_and_office(None, company)) for company in offices
    ]
    pdf_data = render_template(
        'office/pdf_list.html', companies=companies,
    )
    return convert_to_pdf(pdf_data)
