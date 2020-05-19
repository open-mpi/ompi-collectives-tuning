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
    import sys

    dir_path = os.path.dirname(os.path.realpath(__file__))
    config = Params( argv[1] )
    scheduler = argv[2]
    collective_list = config.getStrlst("collectives")
    omb_path = config.getStr("omb_collective_directory")
    imb_bin = config.getStr("imb_binary")
    num_rank_list = config.getIntlst("number_of_ranks")
    max_num_node = config.getInt("max_num_node")
    num_core_per_node = config.getInt("number_of_cores_per_node")
    num_run = config.getInt("number_of_runs_per_test")
    mpirun_options = config.getStr("mpirun_options")

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
            print("No two proc algorithm for "+collective)

        f = open(dir_path+"/output/"+collective+"/"+collective+"_coltune.sh", "w")
        print("#!/bin/sh", file=f)
        print("#", file=f)
        if scheduler == "slurm":
            print("#SBATCH --job-name="+collective, file=f)
            print("#SBATCH --output=res.txt", file=f)
            print("#", file=f)
            print("#SBATCH --ntasks-per-node="+str(num_core_per_node), file=f)
            print("#SBATCH --time=1000:00:00", file=f)
            print("#SBATCH --nodes="+str(max_num_node), file=f)
        elif scheduler == "sge":
            print("#$ -j y", file=f)
            print("#$ -pe mpi %d" % (max_num_node * num_core_per_node), file=f)
            print("#", file=f)
            print("#$ -cwd", file=f)
            print("#", file=f)
            print("echo Got $NSOLTS processors.", file=f)
        else:
            print("Unknown scheduler. Aborting..")
            sys.exit()

        print("", file=f)
 
        for num_rank in num_rank_list:
            for alg in range(num_alg+1):
                if alg in exclude_alg or (alg == two_proc_alg and num_rank > 2):
                    continue
                print("# ", alg, num_rank, "ranks", file=f)
                for run_id in range(num_run):
                    if collective in imb_collectives:
                        prg_name = imb_bin+" -npmin %d %s " % (num_rank, collective)
                    else:
                        prg_name = omb_path+"/osu_"+collective
                    cmd = "mpirun --np %d " % (num_rank)
                    cmd += "%s " % (mpirun_options)
                    cmd += "--mca coll_tuned_use_dynamic_rules 1 --mca coll_tuned_"+collective+"_algorithm "+str(alg)
                    cmd += " " + prg_name
                    cmd += " >& " + dir_path+"/output/"+collective + "/" + str(alg) + "_" + str(num_rank) + "ranks" + "_run" + str(run_id) + ".out"
                    print(cmd, file=f)
                print("", file=f)

        f.close()
        print("SGE script wrote to "+collective+"_coltune.sh successfully!")

if __name__ == "__main__":
    main()

