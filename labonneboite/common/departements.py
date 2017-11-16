# coding: utf8
def get_departements(largest_ones_first=False):
    departements = ["{:02d}".format(d) for d in range(1, 96)] + ['97']
    if largest_ones_first:
        departements.remove('75')
        departements[:0] = ['75']
    return departements


DEPARTEMENTS = get_departements()
DEPARTEMENTS_WITH_LARGEST_ONES_FIRST = get_departements(largest_ones_first=True)
