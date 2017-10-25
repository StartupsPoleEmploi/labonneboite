# coding: utf8

# pylint: disable=unused-import
from labonneboite.conf.common.rome_mobilities import ROME_MOBILITIES
# pylint: enable=unused-import
from labonneboite.common.load_data import load_rome_labels, load_naf_labels

ROME_DESCRIPTIONS = load_rome_labels()

NAF_CODES = load_naf_labels()

LOCALE = 'fr_FR.utf8'

SEARCHING_TIME = 10000

HOST = 'labonneboite.pole-emploi.fr'

# Headcount
HEADCOUNT_INSEE = {
    u'00': u'0 salarié',
    u'01': u'1 ou 2 salariés',
    u'02': u'3 à 5 salariés',
    u'03': u'6 à 9 salariés',
    u'11': u'10 à 19 salariés',
    u'12': u'20 à 49 salariés',
    u'21': u'50 à 99 salariés',
    u'22': u'100 à 199 salariés',
    u'31': u'200 à 249 salariés',
    u'32': u'250 à 499 salariés',
    u'41': u'500 à 999 salariés',
    u'42': u'1 000 à 1 999 salariés',
    u'51': u'2 000 à 4 999 salariés',
    u'52': u'5 000 à 9 999 salariés',
    u'53': u'10 000 salariés et plus',
}

HEADCOUNT_INSEE_CHOICES = [(key, value) for key, value in sorted(HEADCOUNT_INSEE.items())]

HEADCOUNT_WHATEVER = 1
HEADCOUNT_SMALL_ONLY = 2
HEADCOUNT_BIG_ONLY = 3

HEADCOUNT_SMALL_ONLY_MAXIMUM = 12
HEADCOUNT_BIG_ONLY_MINIMUM = 21
HEADCOUNT_FILTER_DEFAULT = 1

HEADCOUNT_VALUES = {
    'all': HEADCOUNT_WHATEVER,
    'big': HEADCOUNT_BIG_ONLY,
    'small': HEADCOUNT_SMALL_ONLY
}

# Contract Value
CONTRACT_VALUES = {'all': 0, 'alternance': 1}

# Sort
SORTING_CHOICES = (
    (u'distance', u'Distance'),
    (u'score', u'Potentiel d\'embauche'),
)
SORT_FILTER_DEFAULT = "score"

# Paginaton
PAGINATION_MAX_PAGES = 10
PAGINATION_COMPANIES_PER_PAGE = 10

# Contact modes
CONTACT_MODE_STAGES = {
    u"Se présenter spontanément": [
        u"Se présenter à l'adresse indiquée avec CV et photo",
        u"Demander le nom d'un contact pour relancer",
        u"Relancer votre interlocuteur par téléphone",
        u"Déclarer votre reprise d'emploi à Pôle emploi :-)",
    ],
    u"Envoyer un CV et une lettre de motivation": [
        (u"Rechercher le nom d'un contact dans l'entreprise (google, kompass, linkedin, viadeo, votre réseau) "
            u"pour lui adresser votre courrier/email"),
        (u"Rechercher des informations économiques (projet, évolution) sur l'entreprise afin de personnaliser "
            u"votre lettre de motivation"),
        u"Envoyer votre CV et votre lettre de motivation",
        u"Relancer votre interlocuteur par téléphone",
        u"Préparer votre entretien",
        u"Déclarer votre reprise d'emploi à Pôle emploi :-)",
    ]
}
CONTACT_MODE_DEFAULT = u"Envoyer un CV et une lettre de motivation"

ES_INDEX = 'labonneboite'

LOGSTASH_HOST = "localhost"
LOGSTASH_PORT = 5959

TILE_SERVER_URL = "http://openmapsurfer.uni-hd.de/tiles/roads/x={x}&y={y}&z={z}"

COMPANY_RESULTS_MAX = 100
AUTOCOMPLETE_MAX = 5

ROME_NAF_PROBABILITY_CUTOFF = 0.05

DISTANCE_FILTER_DEFAULT = 10