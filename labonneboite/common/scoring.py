# coding: utf8

import math
from functools import lru_cache

from labonneboite.common import mapping as mapping_util
from labonneboite.conf import settings

# scores between 0 and 100
SCORE_FOR_ROME_MINIMUM = 20
SCORE_ALTERNANCE_FOR_ROME_MINIMUM = 10

# stars between 0.0 and 5.0
STARS_MINIMUM = 2.5
STARS_MAXIMUM = 5.0

# ############### WARNING about matching scores vs hirings ################
# Methods scoring_util.get_hirings_from_score
# and scoring_util.get_score_from_hirings
# rely on special coefficients SCORE_50_HIRINGS, SCORE_60_HIRINGS etc..
# which values in github repository are *fake* and used for dev and test only.
#
# The real values are confidential, stored outside of github repo,
# and only used in staging and production.
#
# This is designed so that you *CANNOT* guess the hirings based
# on the score you see in production.
# #########################################################################

def round_half_up(x):
    """
    The 'round' function from Python 3 is different from Python 2.7's:
    https://docs.python.org/2.7/library/functions.html#round
    https://docs.python.org/3/library/functions.html#round

    This function emulates the behaviour from Python 2.7, where:

        round(integer + 0.5) == integer + 1 if integer >= 0 else integer
    """
    diff = x - math.floor(x)
    if diff < 0.5:
        return int(math.floor(x))
    elif diff > 0.5:
        return int(math.ceil(x))

    return int(math.ceil(x) if x > 0 else math.floor(x))


# very good hit/miss ratio observed while running create_index.py
# thanks to bucketing float values of hirings, see get_score_from_hirings
@lru_cache(maxsize=512*1024)
def _get_score_from_hirings(hirings, as_float=False):
    """
    Note: leading underscore in method name means "private method" (python naming convention).

    Transform a number of hirings (typically, the predicted hirings in the next 6 months)
    which is a float between 0 and 1000 or even more (it is the output of the regression model)
    into a score (int between 50 and 100) just like in the previous binary classification model.

    The underlying formula has been designed when switching from a binary classification model
    to a regression model, in order to roughly keep the same volumes of 1-stars, 2-stars,
    3-stars and 4-stars offices.

    0.0 stars ~ 0 hirings
    2.5 stars ~ SCORE_50_HIRINGS hirings
    3.0 stars ~ SCORE_60_HIRINGS hirings
    4.0 stars ~ SCORE_80_HIRINGS hirings
    5.0 stars ~ SCORE_100_HIRINGS+ hirings

    For confidentiality reasons, we cannot disclose the SCORE_*_HIRINGS values.
    """
    if hirings <= settings.SCORE_50_HIRINGS:
        # this way about 500K offices will be selected to be deployed in production
        # and all others (score below 50) will be automatically filtered out
        score = 0.0 + 50 * (hirings - 0.0) / (settings.SCORE_50_HIRINGS - 0.0)
    elif hirings >= settings.SCORE_100_HIRINGS:
        score = 100.0
    elif hirings <= settings.SCORE_60_HIRINGS:
        score = (50.0 + 10 * (hirings - settings.SCORE_50_HIRINGS) /
            (settings.SCORE_60_HIRINGS - settings.SCORE_50_HIRINGS))
    elif hirings <= settings.SCORE_80_HIRINGS:
        score = (60.0 + 20 * (hirings - settings.SCORE_60_HIRINGS) /
            (settings.SCORE_80_HIRINGS - settings.SCORE_60_HIRINGS))
    elif hirings <= settings.SCORE_100_HIRINGS:
        score = 80.0 + 20.0/math.log10(settings.SCORE_100_HIRINGS) * math.log10(1 + hirings - settings.SCORE_80_HIRINGS)
    else:
        raise Exception("unexpected value of hirings : %s" % hirings)

    # score should always be positive
    score = max(0.0, score)

    if as_float:
        return score
    return round_half_up(score)


def get_score_from_hirings(hirings, as_float=False, skip_bucketing=False):
    """
    Bucket values of float hirings in order to improve hit/miss ratio of underlying
    private method _get_score_from_hirings.
    """
    if skip_bucketing:
        pass
    elif hirings <= 3:
        hirings = round(hirings, 1)
    else:
        hirings = round_half_up(hirings)
    return _get_score_from_hirings(hirings, as_float=False)


# very good hit/miss ratio observed while running create_index.py
@lru_cache(maxsize=1024)
def get_hirings_from_score(score):
    """
    does exactly the reverse operation of get_score_from_hirings
    """
    if score <= 50:
        hirings = settings.SCORE_50_HIRINGS * score / 50.0
    elif score <= 60:
        hirings = (settings.SCORE_50_HIRINGS +
            (score - 50) / 10.0 * (settings.SCORE_60_HIRINGS - settings.SCORE_50_HIRINGS))
    elif score <= 80:
        hirings = (settings.SCORE_60_HIRINGS +
            (score - 60) / 20.0 * (settings.SCORE_80_HIRINGS - settings.SCORE_60_HIRINGS))
    elif score <= 100:
        hirings = -1 + settings.SCORE_80_HIRINGS + 10.0 ** ((score-80) / 20.0 * math.log10(settings.SCORE_100_HIRINGS))
    else:
        raise Exception("unexpected value of score : %s" % score)
    return hirings


# very good hit/miss ratio observed while running create_index.py
@lru_cache(maxsize=256*1024)
def get_score_adjusted_to_rome_code_and_naf_code(score, rome_code, naf_code):
    """
    Adjust the score to a rome_code (e.g. the ROME code of the current search)
    and a naf_code (e.g. NAF code of an office)
    The resulting score is an integer and might be below 50 (from 0 to 100)
    """

    # fallback to main score in some cases
    # - no rome_code in context (favorites page, office page...)
    # - orphaned naf_code (no related rome_code)
    # - rome_code is not related to the naf_code (custom ROME via SAVE)
    if (
        not rome_code
        or naf_code not in mapping_util.MANUAL_NAF_ROME_MAPPING
        or rome_code not in mapping_util.MANUAL_NAF_ROME_MAPPING[naf_code]
    ):
        return score

    total_office_hirings = get_hirings_from_score(score)
    affinity = mapping_util.get_affinity_between_rome_and_naf(rome_code, naf_code)
    office_hirings_for_current_rome = total_office_hirings * affinity

    # result should be integer
    return get_score_from_hirings(office_hirings_for_current_rome, as_float=False)


def get_stars_from_score(score):
    """
    Convert the score (integer theoretically between 0 and 100)
    to a number of stars (float theoretically between 0.0 and 5.0).

    All documentation below is based on the assumption that SCORE_FOR_ROME_MINIMUM is 20,
    STARS_MINIMUM is 2.5 and STARS_MAXIMUM is 5.0. This makes things
    more readable hopefully.

    The score is actually between 20 and 100, as lower scores were filtered out by the create_index process.
    Exception: this stays true for all scores per rome_code, but not for
    the general all-jobs-included score which might still sometimes be below 20.

    Stars were initially between 1.0 and 5.0, matching scores between 20 and 100,
    however as lower stars may give a bad unjustified feeling about the company, we artificially raise the
    stars to be guaranteed to be between 2.5 and 5.0.

    Returned stars number always has 1 digit exactly. (i.e. 4.3 or 3.0 but not 4.35)
    """
    score_min = SCORE_FOR_ROME_MINIMUM
    score_max = 100.0

    # adjust for rare case of all-jobs-included score below 20
    # happens for example on the office details page without rome_code context
    score = max(score, score_min)

    # normalize score between 0 and 1
    normalized_score = (score - score_min) / (score_max - score_min)

    stars = STARS_MINIMUM + normalized_score * (STARS_MAXIMUM - STARS_MINIMUM)
    
    # round to 1 digit
    stars = round(stars, 1)

    return stars

def get_score_from_stars(stars):
    """
    Reverse of get_stars_from_score(score).
    """
    score_min = SCORE_FOR_ROME_MINIMUM
    score_max = 100.0
    normalized_score = (stars - STARS_MINIMUM) / (STARS_MAXIMUM - STARS_MINIMUM)
    score = score_min + normalized_score * (score_max - score_min)
    return score
