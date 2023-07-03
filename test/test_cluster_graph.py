#!/usr/bin/env python3

import unittest
import os
os.environ["POLARS_MAX_THREADS"] = "1"
import polars as pl
from polars.testing import assert_frame_equal
from ibis.workflow.scripts.cluster_graph import pipeline

ELUSIVE_EDGES_COLUMNS={
    "style": str,
    "cluster_size": int,
    "samples": str,
    "target_ids": str,
    }
READ_SIZE_COLUMNS=["sample", "read_size"]
ELUSIVE_CLUSTERS_COLUMNS={
    "samples": str,
    "length": int,
    "total_targets": int,
    "total_size": int,
    "recover_samples": str,
    "coassembly": str,
    }

class Tests(unittest.TestCase):
    def assertDataFrameEqual(self, a, b):
        assert_frame_equal(a, b, check_dtype=False)

    def test_cluster_graph(self):
        elusive_edges = pl.DataFrame([
            ["match", 2, "sample_2.1,sample_1.1", "0,1,2"],
            ["match", 2, "sample_1.1,sample_3.1", "1,2"],
        ], schema=ELUSIVE_EDGES_COLUMNS)
        read_size = pl.DataFrame([
            ["sample_1", 1000],
            ["sample_2", 2000],
            ["sample_3", 3000],
        ], schema=READ_SIZE_COLUMNS)

        expected = pl.DataFrame([
            ["sample_1,sample_2", 2, 3, 3000, "sample_1,sample_2,sample_3", "coassembly_0"],
        ], schema=ELUSIVE_CLUSTERS_COLUMNS)
        observed = pipeline(elusive_edges, read_size)
        self.assertDataFrameEqual(expected, observed)

    def test_cluster_two_components(self):
        elusive_edges = pl.DataFrame([
            ["match", 2, "1,2", "1"],
            ["match", 2, "1,3", "1,2"],
            ["match", 2, "2,3", "1,2,3"],
            ["match", 2, "4,5", "4,5,6,7"],
            ["match", 2, "4,6", "4,5,6,7,8"],
            ["match", 2, "5,6", "4,5,6,7,8,9"],
        ], schema = ELUSIVE_EDGES_COLUMNS)
        read_size = pl.DataFrame([
            ["1", 1000],
            ["2", 1000],
            ["3", 1000],
            ["4", 1000],
            ["5", 1000],
            ["6", 1000],
        ], schema=READ_SIZE_COLUMNS)

        expected = pl.DataFrame([
            ["5,6", 2, 6, 2000, "4,5,6", "coassembly_0"],
            ["2,3", 2, 3, 2000, "1,2,3", "coassembly_1"],
        ], schema=ELUSIVE_CLUSTERS_COLUMNS)
        observed = pipeline(elusive_edges, read_size)
        self.assertDataFrameEqual(expected, observed)

    def test_cluster_single_bud(self):
        elusive_edges = pl.DataFrame([
            ["match", 2, "1,2", "1,2"],
            ["match", 2, "1,3", "1,3"],
            ["match", 2, "1,4", "1,4"],
            ["match", 2, "2,3", "2,3"],
            ["match", 2, "2,4", "2,4"],
            ["match", 2, "3,4", "3,4"],
            ["match", 2, "4,5", "5"],
        ], schema = ELUSIVE_EDGES_COLUMNS)
        read_size = pl.DataFrame([
            ["1", 1000],
            ["2", 1000],
            ["3", 1000],
            ["4", 1000],
            ["5", 1000],
        ], schema=READ_SIZE_COLUMNS)

        expected = pl.DataFrame([
            ["4", 1, 5, 1000, "1,2,3,4", "coassembly_0"],
            ["3", 1, 4, 1000, "1,2,3,4", "coassembly_1"],
            ["2", 1, 4, 1000, "1,2,3,4", "coassembly_2"],
            ["1", 1, 4, 1000, "1,2,3,4", "coassembly_3"],
            ["5", 1, 1, 1000, "4,5", "coassembly_4"],
        ], schema=ELUSIVE_CLUSTERS_COLUMNS)
        observed = pipeline(
            elusive_edges,
            read_size,
            MAX_COASSEMBLY_SAMPLES=1,
            MIN_COASSEMBLY_SAMPLES=1,
            MAX_RECOVERY_SAMPLES=4,
            )
        self.assertDataFrameEqual(expected, observed)

    def test_cluster_single_bud_choice(self):
        elusive_edges = pl.DataFrame([
            ["match", 2, "1,2", "1,2,3,4"],
            ["match", 2, "3,1", "5"],
            ["match", 2, "3,2", "6,7"],
        ], schema = ELUSIVE_EDGES_COLUMNS)
        read_size = pl.DataFrame([
            ["1", 1000],
            ["2", 1000],
            ["3", 1000],
        ], schema=READ_SIZE_COLUMNS)

        expected = pl.DataFrame([
            ["2", 1, 6, 1000, "1,2", "coassembly_0"],
            ["1", 1, 5, 1000, "1,2", "coassembly_1"],
            ["3", 1, 3, 1000, "2,3", "coassembly_2"],
        ], schema=ELUSIVE_CLUSTERS_COLUMNS)
        observed = pipeline(
            elusive_edges,
            read_size,
            MAX_COASSEMBLY_SAMPLES=1,
            MIN_COASSEMBLY_SAMPLES=1,
            MAX_RECOVERY_SAMPLES=2,
            )
        self.assertDataFrameEqual(expected, observed)

    def test_cluster_double_bud(self):
        elusive_edges = pl.DataFrame([
            ["match", 2, "1,2", "1,2,3"],
            ["match", 2, "1,3", "1,3"],
            ["match", 2, "1,4", "1,4"],
            ["match", 2, "2,3", "2,3"],
            ["match", 2, "2,4", "2,4"],
            ["match", 2, "3,4", "1,3,4"],
            ["match", 2, "4,5", "5"],
            ["match", 2, "4,6", "5"],
            ["match", 2, "5,6", "5,6,7"],
        ], schema = ELUSIVE_EDGES_COLUMNS)
        read_size = pl.DataFrame([
            ["1", 1000],
            ["2", 1000],
            ["3", 1000],
            ["4", 1000],
            ["5", 1000],
            ["6", 1000],
        ], schema=READ_SIZE_COLUMNS)

        expected = pl.DataFrame([
            ["5,6", 2, 3, 2000, "4,5,6", "coassembly_0"],
            ["3,4", 2, 3, 2000, "1,2,3,4", "coassembly_1"],
            ["1,2", 2, 3, 2000, "1,2,3,4", "coassembly_2"],
        ], schema=ELUSIVE_CLUSTERS_COLUMNS)
        observed = pipeline(
            elusive_edges,
            read_size,
            MAX_RECOVERY_SAMPLES=4,
            )
        self.assertDataFrameEqual(expected, observed)

    def test_cluster_double_bud_choice(self):
        elusive_edges = pl.DataFrame([
            ["match", 2, "1,2", "1,2,3"],
            ["match", 2, "1,3", "1,3"],
            ["match", 2, "2,3", "1,3"],
            ["match", 2, "4,1", "4"],
            ["match", 2, "4,3", "5"],
            ["match", 2, "5,1", "4"],
            ["match", 2, "5,3", "6"],
            ["match", 2, "4,5", "4,5,6"],
        ], schema = ELUSIVE_EDGES_COLUMNS)
        read_size = pl.DataFrame([
            ["1", 1000],
            ["2", 1000],
            ["3", 1000],
            ["4", 1000],
            ["5", 1000],
        ], schema=READ_SIZE_COLUMNS)

        expected = pl.DataFrame([
            ["4,5", 2, 3, 2000, "3,4,5", "coassembly_0"],
            ["1,2", 2, 3, 2000, "1,2,3", "coassembly_1"],
        ], schema=ELUSIVE_CLUSTERS_COLUMNS)
        observed = pipeline(
            elusive_edges,
            read_size,
            MAX_RECOVERY_SAMPLES=3,
            )
        self.assertDataFrameEqual(expected, observed)

    def test_cluster_double_bud_irrelevant_targets(self):
        elusive_edges = pl.DataFrame([
            ["match", 2, "1,2", "1,2,3"],
            ["match", 2, "1,3", "1,3"],
            ["match", 2, "2,3", "1,3"],
            ["match", 2, "4,1", "4"],
            ["match", 2, "4,3", "7"],
            ["match", 2, "5,1", "4"],
            ["match", 2, "5,3", "8"],
            ["match", 2, "4,5", "4,5,6"],
        ], schema = ELUSIVE_EDGES_COLUMNS)
        read_size = pl.DataFrame([
            ["1", 1000],
            ["2", 1000],
            ["3", 1000],
            ["4", 1000],
            ["5", 1000],
        ], schema=READ_SIZE_COLUMNS)

        expected = pl.DataFrame([
            ["4,5", 2, 3, 2000, "1,4,5", "coassembly_0"],
            ["1,2", 2, 3, 2000, "1,2,3", "coassembly_1"],
        ], schema=ELUSIVE_CLUSTERS_COLUMNS)
        observed = pipeline(
            elusive_edges,
            read_size,
            MAX_RECOVERY_SAMPLES=3,
            )
        self.assertDataFrameEqual(expected, observed)

    def test_cluster_two_samples_among_many(self):
        elusive_edges = pl.DataFrame([
            ["match", 2, "1,2", "some"],
        ], schema = ELUSIVE_EDGES_COLUMNS)
        read_size = pl.DataFrame([
            ["1", 1000],
            ["2", 1000],
            ["3", 1000],
            ["4", 1000],
            ["5", 1000],
            ["6", 1000],
        ], schema=READ_SIZE_COLUMNS)

        expected = pl.DataFrame([
            ["1,2", 2, 1, 2000, "1,2", "coassembly_0"],
        ], schema=ELUSIVE_CLUSTERS_COLUMNS)
        observed = pipeline(elusive_edges, read_size)
        self.assertDataFrameEqual(expected, observed)

    def test_cluster_no_edges(self):
        elusive_edges = pl.DataFrame([
        ], schema = ELUSIVE_EDGES_COLUMNS)
        read_size = pl.DataFrame([
            ["1", 1000],
            ["2", 1000],
            ["3", 1000],
            ["4", 1000],
            ["5", 1000],
            ["6", 1000],
        ], schema=READ_SIZE_COLUMNS)

        expected = pl.DataFrame([
        ], schema=ELUSIVE_CLUSTERS_COLUMNS)
        observed = pipeline(elusive_edges, read_size)
        self.assertDataFrameEqual(expected, observed)

    def test_cluster_only_large_clusters(self):
        elusive_edges = pl.DataFrame([
            ["match", 2, "1,2", "some"],
        ], schema = ELUSIVE_EDGES_COLUMNS)
        read_size = pl.DataFrame([
            ["1", 10000],
            ["2", 10000],
        ], schema=READ_SIZE_COLUMNS)

        expected = pl.DataFrame([
        ], schema=ELUSIVE_CLUSTERS_COLUMNS)
        observed = pipeline(elusive_edges, read_size, MAX_COASSEMBLY_SIZE=2000)
        self.assertDataFrameEqual(expected, observed)

    def test_cluster_three_samples(self):
        # 1: 1 2 3 4
        # 2: 1 2 3
        # 3: 1   3   5
        # 4:       4 5 6 7 8 9
        # 5:           6 7     10 11 12
        # 6:           6   8 9 10 11 12

        elusive_edges = pl.DataFrame([
            ["match", 2, "1,2", "1,2,3"],
            ["match", 2, "1,3", "1,3"],
            ["match", 2, "2,3", "1,3"],
            ["match", 2, "4,1", "4"],
            ["match", 2, "4,3", "5"],
            ["match", 2, "4,5", "6,7"],
            ["match", 2, "4,6", "8,9"],
            ["match", 2, "5,6", "10,11,12"],
            ["pool", 3, "1,2,3", "1,3"],
            ["pool", 3, "4,5,6", "6"],
        ], schema = ELUSIVE_EDGES_COLUMNS)
        read_size = pl.DataFrame([
            ["1", 1000],
            ["2", 1000],
            ["3", 1000],
            ["4", 1000],
            ["5", 1000],
            ["6", 1000],
        ], schema=READ_SIZE_COLUMNS)

        expected = pl.DataFrame([
            ["4,5,6", 3, 7, 3000, "4,5,6", "coassembly_0"],
            ["1,2,3", 3, 3, 3000, "1,2,3", "coassembly_1"],
        ], schema=ELUSIVE_CLUSTERS_COLUMNS)
        observed = pipeline(
            elusive_edges,
            read_size,
            MAX_RECOVERY_SAMPLES=3,
            MIN_COASSEMBLY_SAMPLES=3,
            MAX_COASSEMBLY_SAMPLES=3,
            )
        self.assertDataFrameEqual(expected, observed)

    def test_cluster_four_samples(self):
        # 1:   2 3 4
        # 2: 1   3 4
        # 3: 1 2   4
        # 4: 1 2 3 4

        # 5: 1         6 7 8 9 10
        # 6:         5   7 8
        # 7:         5 6   8
        # 8:               8 9 10

        elusive_edges = pl.DataFrame([
            # pairs of 1,2,3,4
            ["match", 2, "1,2", "3,4"],
            ["match", 2, "1,3", "2,4"],
            ["match", 2, "1,4", "2,3,4"],
            ["match", 2, "2,3", "1,4"],
            ["match", 2, "2,4", "1,3,4"],
            ["match", 2, "3,4", "1,2,4"],
            # pairs of 5,6,7,8
            ["match", 2, "5,6", "7,8"],
            ["match", 2, "5,7", "6,8"],
            ["match", 2, "5,8", "8,9,10"],
            ["match", 2, "6,7", "5,8"],
            ["match", 2, "6,8", "8"],
            ["match", 2, "7,8", "8"],
            # joint pairs
            ["match", 2, "2,5", "1"],
            ["match", 2, "3,5", "1"],
            ["match", 2, "4,5", "1"],
            # triplets
            ["pool", 3, "2,3,4,5", "1"],
            ["pool", 3, "1,3,4", "2"],
            ["pool", 3, "1,2,4", "3"],
            ["pool", 3, "1,2,3,4", "4"],
            ["pool", 3, "5,6,7,8", "8"],
            # quads
            ["pool", 4, "2,3,4,5", "1"],
            ["pool", 4, "1,2,3,4", "4"],
            ["pool", 4, "5,6,7,8", "8"],
        ], schema = ELUSIVE_EDGES_COLUMNS)
        read_size = pl.DataFrame([
            ["1", 1000],
            ["2", 1000],
            ["3", 1000],
            ["4", 1000],
            ["5", 1000],
            ["6", 1000],
            ["7", 1000],
            ["8", 1000],
        ], schema=READ_SIZE_COLUMNS)

        expected = pl.DataFrame([
            ["5,6,7,8", 4, 6, 4000, "5,6,7,8", "coassembly_0"],
            ["1,2,3,4", 4, 4, 4000, "1,2,3,4", "coassembly_1"],
        ], schema=ELUSIVE_CLUSTERS_COLUMNS)
        observed = pipeline(
            elusive_edges,
            read_size,
            MAX_RECOVERY_SAMPLES=4,
            MIN_COASSEMBLY_SAMPLES=4,
            MAX_COASSEMBLY_SAMPLES=4,
            )
        self.assertDataFrameEqual(expected, observed)

if __name__ == '__main__':
    unittest.main()
