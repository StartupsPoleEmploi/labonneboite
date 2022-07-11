import logging
from typing import Sequence

from sqlalchemy import and_

from labonneboite.common.util import timeit
from labonneboite.importer import settings
from labonneboite.importer.models.computing import ExportableOffice

logger = logging.getLogger('main')


@timeit
def check_scores(departements: Sequence[str] = settings.DEPARTEMENTS_TO_BE_SANITY_CHECKED) -> Sequence[str]:
    errors = []
    for departement in departements:

        # 1) DPAE check

        departement_count = ExportableOffice.query.filter(
            and_(
                ExportableOffice.departement == departement,
                ExportableOffice.hiring >= settings.HIRING_REDUCING_MINIMUM_THRESHOLD)).count()
        logger.debug("%i offices with hiring >= %s in departement %s",
                     departement_count, settings.HIRING_REDUCING_MINIMUM_THRESHOLD, departement)
        if departement_count < settings.MINIMUM_OFFICES_PER_DEPARTEMENT_FOR_DPAE:
            errors.append("%s-dpae" % departement)

        # 2) Alternance check

        departement_count = ExportableOffice.query.filter(
            and_(
                ExportableOffice.departement == departement,
                ExportableOffice.score_alternance >= settings.SCORE_ALTERNANCE_REDUCING_MINIMUM_THRESHOLD)).count()
        logger.debug("%i offices with score_alternance >= %s in departement %s",
                     departement_count, settings.SCORE_ALTERNANCE_REDUCING_MINIMUM_THRESHOLD, departement)
        if departement_count < settings.MINIMUM_OFFICES_PER_DEPARTEMENT_FOR_ALTERNANCE:
            errors.append("%s-alternance" % departement)

    return errors
