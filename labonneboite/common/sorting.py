from flask import Markup

SCORE_SORTING_LABEL = 'Recommandation %s' % (
    '<span class="badge badge-large badge-info" data-toggle="tooltip" data-placement="right" title="%s">?</span>' % (
        """
        Tri exclusif La bonne boite basé sur le potentiel d'embauche des entreprises mis à jour toutes les 24 heures.
        """
    )
)

SORT_FILTER_SMART = "smart"
SORT_FILTER_SCORE = "score"
SORT_FILTER_DISTANCE = "distance"
SORT_FILTER_DEFAULT = SORT_FILTER_SMART
SORTING_CHOICES = (
    (SORT_FILTER_SMART, Markup(SCORE_SORTING_LABEL)),
    (SORT_FILTER_DISTANCE, 'Distance'),
    (SORT_FILTER_SCORE, Markup("Potentiel d'embauche <strong>(Nouveau !)</strong>"))
)
SORT_FILTERS = [key for key, _ in SORTING_CHOICES]
