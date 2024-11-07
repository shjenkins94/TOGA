#!/usr/bin/env python3
"""
Run the orthology type map step of TOGA with custom input

MAYBE: Reconcile old isoforms with new if given

MAYBE: Consolidate duplicate transcripts

"""
import os
import argparse
import sys
import shutil
from collections import defaultdict
from modules.common import setup_logger
from modules.common import to_log
from modules.filter_bed import prepare_bed_file
from modules.make_query_isoforms import get_query_isoforms_data
from modules.orthology_type_map import orthology_type_map
from version import __version__


class TogaRescue:
    """a class to manage the original TOGA results directory and a new directory with rescued/consolidated transcripts"""

    def __init__(self, args):
        # Directories
        self.togadir = os.path.abspath(args.togadir)
        self.outdir = os.path.abspath(args.outdir)
        # Options
        self.ignore_color = args.ignore_color
        self.gene_prefix = args.gene_prefix

        # Old TOGA input
        # Required
        self.target_bed = (
            args.target_bed
            if args.target_bed
            else os.path.join(self.togadir, "temp/toga_filt_ref_annot.bed")
        )
        # Optional
        if args.isoforms:
            self.isoforms = args.isoforms
        elif os.path.isfile(os.path.join(self.togadir, "temp/isoforms.tsv")):
            self.isoforms = os.path.join(self.togadir, "temp/isoforms.tsv")
        else:
            self.isoforms = None

        # Old TOGA output
        self.query_annotation = os.path.join(self.togadir, "query_annotation.bed")
        # Not having paralogs is probably fine
        paralogs_file = os.path.join(self.togadir, "temp/paralogs.txt")
        self.paralogs = paralogs_file if os.path.isfile(paralogs_file) else None
        self.loss_summ = os.path.join(self.togadir, "loss_summ_data.tsv")
        self.pred_scores = os.path.join(self.togadir, "orthology_scores.tsv")

        # New output
        self.log_file = os.path.join(self.outdir, "log.txt")
        # For isoforms
        self.query_isoforms = os.path.join(self.outdir, "query_isoforms.tsv")
        self.query_gene_spans = os.path.join(self.outdir, "query_gene_spans.bed")
        # For bed filtering
        self.ref_bed = os.path.join(self.outdir, "target_annotation_filtered.bed")
        self.bed_filt_rejected = os.path.join(
            self.outdir, "target_annotation_rejected.txt"
        )
        # For orthology mapping
        self.orthology_type = os.path.join(self.outdir, "orthology_classification.tsv")
        self.skipped_ref_trans = os.path.join(self.outdir, "ref_orphan_transcripts.txt")

    def __check_input(self):
        files_in_togadir = [self.query_annotation, self.loss_summ, self.pred_scores]

        to_log(f"Checking togadir {self.togadir} for files")

        for item in files_in_togadir:
            if not os.path.isfile(item):
                self.die(f"Error! File {item} is missing!")

    def die(self, msg, rc=1):
        """Show msg in stderr, exit with the rc given."""
        to_log(msg)
        to_log(f"Program finished with exit code {rc}\n")
        sys.exit(rc)

    def run(self):
        os.mkdir(self.outdir) if not os.path.isdir(self.outdir) else None

        setup_logger(self.log_file)
        self.__check_input()

        get_query_isoforms_data(
            self.query_annotation,
            self.query_isoforms,
            save_genes_track=self.query_gene_spans,
            ignore_color=self.ignore_color,
            gene_prefix=self.gene_prefix,
        )

        to_log("Filtering target annotations...")

        prepare_bed_file(
            self.target_bed,
            self.ref_bed,
            ouf=False,
            save_rejected=self.bed_filt_rejected,
            only_chrom=None,
        )

        to_log("Calling orthology types mapping step...")

        orthology_type_map(
            self.ref_bed,
            self.query_annotation,
            self.orthology_type,
            ref_iso=self.isoforms,
            que_iso=self.query_isoforms,
            paralogs_arg=self.paralogs,
            loss_data=self.loss_summ,
            save_skipped=self.skipped_ref_trans,
            orth_scores_arg=self.pred_scores,
        )


def parse_args():
    """Read and check CMD args"""
    app = argparse.ArgumentParser()
    app.add_argument("togadir", help="Path to TOGA results directory", type=str)
    app.add_argument("outdir", help="Path to output directory", type=str)
    app.add_argument(
        "--target_bed",
        "--tb",
        help="Path to bed file with annotations for the target genome (required if togadir/temp doesn't exist)",
        type=str,
    )
    app.add_argument(
        "--isoforms", "-i", type=str, default="", help="Path to target isoforms"
    )
    app.add_argument(
        "--ignore_color",
        action="store_true",
        dest="ignore_color",
        help="Disable color filter",
    )
    app.add_argument(
        "--gene_prefix",
        "--gp",
        default="TOGA",
        help="Prefix to use for query gene identifiers. Default value is TOGA",
    )

    args = app.parse_args()

    # Check for togadir and temp bed
    togadir = os.path.abspath(args.togadir)
    temp_bed = os.path.join(togadir, "temp/toga_filt_ref_annot.bed")

    if not os.path.isdir(togadir):
        app.error(f"togadir {togadir} must be a directory!")
    if not args.target_bed and not os.path.isfile(temp_bed):
        app.error(f"target_bed is required if {temp_bed} does not exist!")

    return args

if __name__ == "__main__":
    args = parse_args()
    rescue_manager = TogaRescue(args)
    rescue_manager.run()
