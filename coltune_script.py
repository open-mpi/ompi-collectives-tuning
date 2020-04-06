#!/usr/bin/env python
# Copyright (c) 2020      Amazon.com, Inc. or its affiliates.  All Rights
#                         reserved.
#
# $COPYRIGHT$
#
# Additional copyrights may follow
#
# $HEADER$
#

import os
import sys

imb_collectives = ["reduce_scatter_block"]

def main():
    from os import system
    from sys import argv
    from common import Params

    dir_path = os.path.dirname(os.path.realpath(__file__))
    config = Params( argv[1] )
    collective_list = config.getStrlst("collectives")
    omb_path = config.getStr("omb_collective_directory")
    imb_bin = config.getStr("imb_binary")
    num_rank_list = config.getIntlst("number_of_ranks")
    max_num_node = config.getInt("max_num_node")
    num_core_per_node = config.getInt("number_of_cores_per_node")
    num_run = config.getInt("number_of_runs_per_test")

    job_directory = dir_path+"/collective_jobs"
    for collective in collective_list:
        params = Params( job_directory+"/"+collective+".job" )

        if not os.path.exists(dir_path+"/output"):
            os.makedirs(dir_path+"/output")
        if not os.path.exists(dir_path+"/output/"+collective):
            os.makedirs(dir_path+"/output/"+collective)

        num_alg = params.getInt("number_of_algorithms")
        exclude_alg = params.getIntlst("exclude_algorithms")
        two_proc_alg = -1
        try:
            two_proc_alg = params.getInt("two_proc_alg")
        except Exception as e:
            print "No two proc algorithm for "+collective

        f = open(dir_path+"/output/"+collective+"/"+collective+"_coltune.sh", "w")
        print >> f, "#!/bin/sh"
        print >> f, "#"
        print >> f, "#$ -j y"
        print >> f, "#$ -pe mpi %d" % (max_num_node * num_core_per_node)
        print >> f, "#"
        print >> f, "#$ -cwd"
        print >> f, "#"
        print >> f, "echo Got $NSOLTS processors."
        print >> f, ""

 
        for num_rank in num_rank_list:
            for alg in range(num_alg+1):
                if alg in exclude_alg or (alg == two_proc_alg and num_rank > 2):
                    continue
                print >> f, "# ", alg, num_rank, "ranks"
                for run_id in xrange(num_run):
                    if collective in imb_collectives:
                        prg_name = imb_bin+" -npmin %d %s " % (num_rank, collective)
                    else:
                        prg_name = omb_path+"/osu_"+collective
                    cmd = "mpirun --np %d " % (num_rank)
                    cmd += "--mca coll_tuned_use_dynamic_rules 1 --mca coll_tuned_"+collective+"_algorithm "+str(alg)
                    cmd += " " + prg_name
                    cmd += " >& " + dir_path+"/output/"+collective + "/" + str(alg) + "_" + str(num_rank) + "ranks" + "_run" + str(run_id) + ".out"
                    print >> f, cmd
                print >> f, ""

        f.close()
        print "SGE script wrote to "+collective+"_coltune.sh successfully!"

if __name__ == "__main__":
    main()

