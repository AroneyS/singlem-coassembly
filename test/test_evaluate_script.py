#!/usr/bin/env python3

import unittest
import pandas as pd
from cockatoo.workflow.scripts.evaluate import evaluate

SINGLEM_COLUMNS=["gene", "sample", "sequence", "num_hits", "coverage", "taxonomy"]
TARGET_COLUMNS=SINGLEM_COLUMNS+["target"]
CLUSTER_COLUMNS=["samples", "length", "total_weight", "total_targets", "total_size", "recover_samples", "coassembly"]
EDGE_COLUMNS=["taxa_group", "weight", "target_ids", "sample1", "sample2"]
OUTPUT_COLUMNS=["coassembly", "gene", "sequence", "genome", "target", "taxonomy"]

class Tests(unittest.TestCase):
    def assertDataFrameEqual(self, a, b):
        pd.testing.assert_frame_equal(a, b)

    def test_evaluate_script(self):
        targets = pd.DataFrame([
            ["S3.1", "sample_1.1", "AAA", 5, 10.0, "Root", 10],
            ["S3.1", "sample_2.1", "AAA", 5, 10.0, "Root", 10],
        ], columns=TARGET_COLUMNS)
        clusters = pd.DataFrame([
            ["sample_1,sample_2", 2, 1, 1, 100, "sample_1,sample_2,sample_3", "coassembly_0"],
        ], columns=CLUSTER_COLUMNS)
        edges = pd.DataFrame([
            ["Root", 1, "10", "sample_1.1", "sample_2.1"],
        ], columns=EDGE_COLUMNS)
        recovered = pd.DataFrame([
            ["S3.1", "coassembly_0-genome_1_transcripts", "AAA", 1, 2.0, "Root"],
            ["S3.1", "coassembly_0-genome_1_transcripts", "AAB", 1, 2.0, "Root"],
        ], columns=SINGLEM_COLUMNS)

        expected_matches = pd.DataFrame([
            ["coassembly_0", "S3.1", "AAA", "genome_1_transcripts", "10", "Root"],
        ], columns=OUTPUT_COLUMNS)
        expected_unmatched = pd.DataFrame([
            ["coassembly_0", "S3.1", "AAB", "genome_1_transcripts", None, None],
        ], columns=OUTPUT_COLUMNS)

        observed_matches, observed_unmatched = evaluate(targets, clusters, edges, recovered)
        self.assertDataFrameEqual(expected_matches, observed_matches)
        self.assertDataFrameEqual(expected_unmatched, observed_unmatched)


if __name__ == '__main__':
    unittest.main()
