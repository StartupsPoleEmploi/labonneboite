# coding: utf8


CONTACT_MODE_MAIL = 'mail'
CONTACT_MODE_EMAIL = 'email'
CONTACT_MODE_OFFICE = 'office'
CONTACT_MODE_WEBSITE = 'website'
CONTACT_MODE_PHONE = 'phone'

# Contact modes human readable labels as displayed in the API result and the frontend.
CONTACT_MODE_LABELS = {
    CONTACT_MODE_OFFICE: "Se présenter spontanément à l’entreprise",
    CONTACT_MODE_EMAIL: "Envoyer un CV et une lettre de motivation par email",
    CONTACT_MODE_MAIL: "Envoyer un CV et une lettre de motivation par courrier postal",
    CONTACT_MODE_PHONE: "Contacter l'entreprise par téléphone",
    CONTACT_MODE_WEBSITE: "Candidater depuis le site web de l'entreprise",
}


# Keywords designed to correctly match contact_modes based on real data
# observed in production in etablissements.contact_mode
CONTACT_MODE_KEYWORDS = {
    CONTACT_MODE_OFFICE: ["sur place", "Présentez vous", "spontané"],
    CONTACT_MODE_EMAIL: ["mail", "@"],
    CONTACT_MODE_MAIL: ["courrier"],
    CONTACT_MODE_PHONE: ["phone"],
    CONTACT_MODE_WEBSITE: ["site"],
}

# FIXME - ask teammates to fill up remaining codes - also need fallback value!
# Steps for each contact mode as displayed in the office downloadable PDF
CONTACT_MODE_STEPS = {
    CONTACT_MODE_OFFICE: [
        "Se présenter à l'adresse indiquée avec CV et photo",
        "Demander le nom d'un contact pour relancer",
        "Relancer votre interlocuteur par téléphone",
        "Déclarer votre reprise d'emploi à Pôle emploi :-)",
    ],
    CONTACT_MODE_EMAIL: [
        ("Rechercher le nom d'un contact dans l'entreprise (google, kompass, linkedin, viadeo, votre réseau) "
            "pour lui adresser votre courrier/email"),
        ("Rechercher des informations économiques (projet, évolution) sur l'entreprise afin de personnaliser "
            "votre lettre de motivation"),
        "Envoyer votre CV et votre lettre de motivation",
        "Relancer votre interlocuteur par téléphone",
        "Préparer votre entretien",
        "Déclarer votre reprise d'emploi à Pôle emploi :-)",
    ]
}


