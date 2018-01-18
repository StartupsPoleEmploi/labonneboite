
def is_siret(siret):
    # A valid SIRET is composed by 14 digits
    try:
        int(siret)
    except ValueError:
        return False

    return len(siret) == 14
