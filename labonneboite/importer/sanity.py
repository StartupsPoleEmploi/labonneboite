import logging
from sqlalchemy import and_

from labonneboite.importer.util import timeit
from labonneboite.importer import settings
from labonneboite.importer.models.computing import ExportableOffice

logger = logging.getLogger('main')


@timeit
def check_scores(departements=settings.DEPARTEMENTS_TO_BE_SANITY_CHECKED):
    errors = []
    for departement in departements:
        departement_count = ExportableOffice.query.filter(
            and_(
                ExportableOffice.departement == departement,
                ExportableOffice.score >= settings.SCORE_REDUCING_MINIMUM_THRESHOLD)).count()
        logger.debug("%i offices with score > %s in departement %s", 
            settings.SCORE_REDUCING_MINIMUM_THRESHOLD, departement_count, departement)
        ok = departement_count >= settings.MINIMUM_OFFICES_PER_DEPARTEMENT
        if not ok:
            errors.append(departement)
    return errors
