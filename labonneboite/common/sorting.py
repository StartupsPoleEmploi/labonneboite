# coding: utf8

SCORE_SORTING_LABEL = u'Tri optimisé %s' % (
	u'<span class="badge badge-large badge-info" data-toggle="tooltip" data-placement="right" title="%s">?</span>' % (
		u"""
		Tri exclusif LaBonneBoite basé sur le potentiel d'embauche des entreprises mis à jour toutes les 24 heures.
		"""
	)
)

SORTING_CHOICES = (
    (u'score', SCORE_SORTING_LABEL),
    (u'distance', u'Distance'),
)

SORT_FILTER_SCORE = "score"
SORT_FILTER_DISTANCE = "distance"
SORT_FILTERS = [SORT_FILTER_SCORE, SORT_FILTER_DISTANCE]
SORT_FILTER_DEFAULT = SORT_FILTER_SCORE
