#!/usr/bin/env python3
"""Write Jobscripts for running on UGE."""
import argparse
import sys
import os
from collections import defaultdict
from jinja2 import Template

__author__ = "Scott H. Jenkins, 2023."
__version__ = "1.0"
__email__ = "shjenkins94@gmail.com"

def parse_args():
    """Parse and check args."""
    app = argparse.ArgumentParser()
    app.add_argument("jobname", help="Name to give job in scheduler")
    app.add_argument("logdir", help="Directory to run job in")
    app.add_argument("jobnum", help="Number of jobs to run")
    app.add_argument("memGB", help="Memory to request in GB")
    app.add_argument("joblist", help="File with list of jobs to run")
    app.add_argument("jobfile", help="File to save jobscript to")
    app.add_argument(
        "--queue",
        default=None,
        help="Queue to submit job to.",
    )
    if len(sys.argv) < 6:
        app.print_help()
        sys.exit(0)
    args = app.parse_args()
    return args

def write_jobscript(jobname, logdir, jobnum, memGB, joblist, jobfile, queue):
    templatefile = os.path.join(os.path.dirname(__file__), 'array_jobscript.jinja2')
    with open(templatefile) as tf:
        content = Template(tf.read()).render(
            jobname=jobname,
            logdir=logdir,
            jobnum=jobnum,
            memGB=memGB,
            joblist=joblist,
            queue=queue
        )
        with open(jobfile, "w") as jf:
            jf.write(content)

def main():
    """Entry point."""
    args = parse_args()
    write_jobscript(
        args.jobname,
        args.logdir,
        args.jobnum,
        args.memGB,
        args.joblist,
        args.jobfile,
        args.queue,
    )

if __name__ == "__main__":
    main()