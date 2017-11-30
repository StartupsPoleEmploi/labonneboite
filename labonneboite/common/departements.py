# coding: utf8
def get_departements(largest_ones_first=False):
    departements = ["{:02d}".format(d) for d in range(1, 96)] + ['97']
    if largest_ones_first:
        largest_departements = ['75', '13', '97', '69', '59', '33', '92', '06', '34']
        for d in largest_departements:
            if d not in departements:
                raise ValueError('unknown departement %s' % d)
            departements.remove(d)
            departements[:0] = [d]
    return departements


DEPARTEMENTS = get_departements()
DEPARTEMENTS_WITH_LARGEST_ONES_FIRST = get_departements(largest_ones_first=True)
