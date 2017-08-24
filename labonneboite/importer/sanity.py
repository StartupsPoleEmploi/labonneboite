from sqlalchemy import and_

from labonneboite.importer import settings


import logging
logger = logging.getLogger('main')


def check_scores(departements=settings.DEPARTEMENTS, minimum_office_count=100):
    from labonneboite.importer.models.computing import ExportableOffice
    errors = []
    for departement in departements:
        departement_count = ExportableOffice.query.filter(
            and_(
                ExportableOffice.departement == departement,
                ExportableOffice.score > 50)).count()
        logger.debug("%i offices with score > 50 in departement %s", departement_count, departement)
        ok = departement_count >= minimum_office_count
        if not ok:
            errors.append(departement)
    return errors
