template = {
  "swagger": "2.0",
  "info": {
    "title": "API - La Bonne Boite",
    "description": 'Trouvez les entreprises qui embauchent sans deposer d\'offres d\'emploi !',
    "contact": {
      "email": "labonneboite@pole-emploi.fr",
      "url": "labonneboite.pole-emploi.fr",
    },
    "termsOfService": "https://labonneboite.pole-emploi.fr/conditions-generales",
    "version": "1.0.0"
  },
  "host": "https://api.emploi-store.fr/partenaire/",  # overrides localhost:500
  "basePath": "api",  # base bash for blueprint registration
  "schemes": [
    "http",
    "https"
  ],
  "produces": [
    "application/json",
  ]
}

config = {
    "headers": [
    ],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_1.json',
            "rule_filter": lambda rule: True,  # all in
            "model_filter": lambda tag: True,  # all in
        }
    ],
    "swagger_ui": True,
    "static_url_path": "/flasgger_static",
    "specs_route": "/apidocs/"
}