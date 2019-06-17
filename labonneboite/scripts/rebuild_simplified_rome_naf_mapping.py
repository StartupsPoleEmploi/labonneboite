# coding: utf8
import os
import re
import itertools
import logging
import pandas as pd
from slugify import slugify
import numpy as np

from labonneboite.conf import settings
from labonneboite.common import mapping as mapping_util
from labonneboite.common import hiring_type_util
from labonneboite.common import geocoding
from labonneboite.common.search import fetch_offices

logging.basicConfig(level=logging.INFO)

INPUT_FILENAME = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../common/data/rome_naf_mapping.raw.csv')
OUTPUT_FILENAME = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../common/data/rome_naf_mapping.csv')
CSV_DELIMITER = ','

# There might sometimes be a few items more than the wanted maximum,
# because for example we won't drop the last ROME of a given NAF
# if this NAF is highly ranked for this ROME.
# These threshold have been carefully selected so that:
# - approx 90% of romes have less than 10 nafs
# - approx 90% of nafs have less than 10 romes
WANTED_MAXIMUM_ROMES_PER_NAF = 4
WANTED_MAXIMUM_NAFS_PER_ROME = 3

SHOW_DETAILED_STATS = False


class RomeNafMapping:

    def __init__(self):
        self.df = pd.read_table(INPUT_FILENAME, sep=CSV_DELIMITER)

        self.sorted_nafs_for_rome = {}
        for rome in self.df.rome_id.unique():
            self.sorted_nafs_for_rome[rome] = self.df[self.df.rome_id == rome].sort_values(
                by='hirings', ascending=False
            ).naf_id.tolist()

        self.sorted_romes_for_naf = {}
        for naf in self.df.naf_id.unique():
            self.sorted_romes_for_naf[naf] = self.df[self.df.naf_id == naf].sort_values(
                by='hirings', ascending=False
            ).rome_id.tolist()

    def get_romes(self):
        return self.sorted_nafs_for_rome.keys()

    def get_nafs(self):
        return self.sorted_romes_for_naf.keys()

    def delete_mapping(self, rome, naf):
        # We apply an exception requested by our business developer.
        # M* romes mappings should stay untouched, as they are generally by
        # nature relevant for all kinds of companies.
        # For example, every company needs a secretary... (M1607)
        if rome.startswith('M'):
            return

        self.sorted_romes_for_naf[naf].remove(rome)
        assert rome not in self.sorted_romes_for_naf[naf]
        if self.sorted_romes_for_naf[naf] == []:
            del self.sorted_romes_for_naf[naf]
            assert naf not in self.sorted_romes_for_naf

        self.sorted_nafs_for_rome[rome].remove(naf)
        assert naf not in self.sorted_nafs_for_rome[rome]
        if self.sorted_nafs_for_rome[rome] == []:
            del self.sorted_nafs_for_rome[rome]
            assert rome not in self.sorted_nafs_for_rome

        # delete mapping in dataframe
        indexNames = self.df[(self.df.rome_id == rome) & (self.df.naf_id == naf)].index
        self.df.drop(indexNames, inplace=True)

    def simplify_rome(self, rome):
        """
        Simplify given rome by dropping its weak mappings.

        All nafs after the "top WANTED_MAXIMUM_NAFS_PER_ROME"
        are candidates to be dropped provided the current rome
        is not too relevant for them i.e. the rome is not in the
        "top WANTED_MAXIMUM_ROMES_PER_NAF" for this naf.
        """
        sorted_nafs = self.sorted_nafs_for_rome[rome]
        # Select all nafs but the first WANTED_MAXIMUM_NAFS_PER_ROME ones.
        weak_nafs = sorted_nafs[WANTED_MAXIMUM_NAFS_PER_ROME:]
        for naf in weak_nafs:
            weak_romes = self.sorted_romes_for_naf[naf][WANTED_MAXIMUM_ROMES_PER_NAF:]
            if rome in weak_romes:
                self.delete_mapping(rome=rome, naf=naf)

    def simplify_naf(self, naf):
        """
        Simplify given naf by dropping its weak mappings.

        All romes after the "top WANTED_MAXIMUM_ROMES_PER_NAF"
        are candidates to be dropped provided the current naf
        is not too relevant for them i.e. the naf is not in the
        "top WANTED_MAXIMUM_NAFS_PER_ROME" for this rome.
        """
        sorted_romes = self.sorted_romes_for_naf[naf]
        # Select all romes but the first WANTED_MAXIMUM_ROMES_PER_NAF ones.
        weak_romes = sorted_romes[WANTED_MAXIMUM_ROMES_PER_NAF:]
        for rome in weak_romes:
            weak_nafs = self.sorted_nafs_for_rome[rome][WANTED_MAXIMUM_NAFS_PER_ROME:]
            if naf in weak_nafs:
                self.delete_mapping(rome=rome, naf=naf)

    def simplify(self):
        iteration_id = 1
        self.mappings_initial = len(self.df)
        self.display_initial_stats()
        while True:
            mappings_before = len(self.df)
            for rome in self.get_romes():
                self.simplify_rome(rome)
            for naf in self.get_nafs():
                self.simplify_naf(naf)
            mappings_after = len(self.df)
            mappings_deleted = mappings_before - mappings_after
            logging.info("Iteration #{} : eliminated {} mappings (from {} down to {} mappings)".format(
                iteration_id,
                mappings_deleted,
                mappings_before,
                mappings_after,
            ))
            if mappings_deleted == 0:
                self.mappings_final = mappings_after
                self.iterations = iteration_id
                self.display_final_stats()
                break
            iteration_id += 1

    def display_initial_stats(self):
        logging.info("Loaded {} mappings ({} romes and {} nafs).".format(
            self.mappings_initial,
            len(self.sorted_nafs_for_rome),
            len(self.sorted_romes_for_naf),
        ))

    def display_final_stats(self):
        logging.info("Stability reached! No more mappings to simplify.")
        logging.info("Eliminated {} mappings (from {} down to {} mappings) in {} iterations!".format(
            self.mappings_initial - self.mappings_final,
            self.mappings_initial,
            self.mappings_final,
            self.iterations,
        ))
        logging.info("Ended with a mapping dataset of {} romes and {} nafs).".format(
            len(self.sorted_nafs_for_rome),
            len(self.sorted_romes_for_naf),
        ))

        romes_per_naf = [len(romes) for romes in self.sorted_romes_for_naf.values()]
        max_romes_per_naf = max(romes_per_naf)
        max_romes_per_naf_champions = [
            naf for naf in self.get_nafs()
            if len(self.sorted_romes_for_naf[naf]) == max_romes_per_naf
        ]
        logging.info("Actual maximum of romes per naf : {} achieved by nafs {}".format(
            max_romes_per_naf,
            max_romes_per_naf_champions,
        ))
        if SHOW_DETAILED_STATS:
            logging.info("Romes per naf : {}".format(romes_per_naf))
        logging.info("90% of nafs have {} romes or less.".format(round(np.percentile(romes_per_naf, 90), 1)))

        nafs_per_rome = [len(nafs) for nafs in self.sorted_nafs_for_rome.values()]
        max_nafs_per_rome = max(nafs_per_rome)
        max_nafs_per_rome_champions = [
            rome for rome in self.get_romes()
            if len(self.sorted_nafs_for_rome[rome]) == max_nafs_per_rome
        ]
        logging.info("Actual maximum of nafs per rome : {} achieved by romes {}".format(
            max_nafs_per_rome,
            max_nafs_per_rome_champions,
        ))
        if SHOW_DETAILED_STATS:
            logging.info("Nafs per rome : {}".format(nafs_per_rome))
        logging.info("90% of romes have {} nafs or less.".format(round(np.percentile(nafs_per_rome, 90), 1)))


    def export_to_file(self):
        self.df.to_csv(OUTPUT_FILENAME, sep=CSV_DELIMITER, index=False, encoding='utf-8')


def rebuild_simplified_rome_naf_mapping():
    rome_naf_mapping = RomeNafMapping()
    rome_naf_mapping.simplify()
    rome_naf_mapping.export_to_file()
    logging.info("please consult result in file %s", OUTPUT_FILENAME)


if __name__ == '__main__':
    rebuild_simplified_rome_naf_mapping()
