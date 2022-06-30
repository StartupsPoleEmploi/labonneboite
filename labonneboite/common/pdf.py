import errno
import logging
import os
import io

from flask import render_template
from slugify import slugify
from xhtml2pdf import pisa

from labonneboite.common import util
from labonneboite.common.conf import settings

logger = logging.getLogger('main')


def get_file_path(office):
    return os.path.join(settings.GLOBAL_STATIC_PATH, "pdf", office.departement, office.naf,
                        slugify(office.name.strip()[0]), "%s.pdf" % office.siret)


def write_file(office, data, path):
    if not os.path.exists(os.path.dirname(path)):
        try:
            os.makedirs(os.path.dirname(path))
        except OSError as exc:
            # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
    with open(path, "wb") as f:
        f.write(data)
    f.close()
    logger.debug("wrote PDF file to %s", path)


def delete_file(office):
    filename = get_file_path(office)
    if os.path.exists(filename):
        os.remove(filename)


def convert_to_pdf(pdf_data, web_dir):
    """
    Convert a str to pdf
    Return: a file-like object
    """
    pdf_target = io.BytesIO()
    # The link callback is a function that is used to determine the path of
    # local static assets required to generate the pdf. This should not point
    # to http://labonneboite.
    link_callback = lambda uri, rel: os.path.join(web_dir, uri.strip("/"))
    pisa.CreatePDF(io.StringIO(pdf_data), dest=pdf_target, link_callback=link_callback)
    pdf_target.seek(0)
    return pdf_target


def render_favorites(offices, web_dir):
    """
    Render the list of companies as favorites.

    Return: a file-like object.
    """
    companies = [(company, util.get_contact_mode_for_rome_and_office(None, company)) for company in offices]
    pdf_data = render_template(
        'office/pdf_list.html',
        companies=companies,
    )
    return convert_to_pdf(pdf_data, web_dir)
