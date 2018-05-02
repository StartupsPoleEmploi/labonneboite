# coding: utf8

SCORE_SORTING_LABEL = u'Tri optimisé %s' % (
	u'<span class="badge badge-large badge-info" data-toggle="tooltip" data-placement="right" title="%s">?</span>' % (
		u"""
		Tri exclusif LaBonneBoite basé sur le potentiel d'embauche des entreprises mis à jour toutes les 24 heures.
		"""
	)
)

SORT_FILTER_SCORE = "score"
SORT_FILTER_DISTANCE = "distance"
SORT_FILTER_DEFAULT = SORT_FILTER_SCORE
SORTING_CHOICES = (
    (SORT_FILTER_SCORE, SCORE_SORTING_LABEL),
    (SORT_FILTER_DISTANCE, u'Distance'),
)
SORT_FILTERS = [key for key, _ in SORTING_CHOICES]
