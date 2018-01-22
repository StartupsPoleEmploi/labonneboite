
def is_siret(siret):
    # A valid SIRET is composed by 14 digits
    return len(siret) == 14 and siret.isdigit()
