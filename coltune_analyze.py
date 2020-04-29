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
from common import Params

imb_collectives = ["reduce_scatter_block"]
def coll_id_from_name(collective):
    switch = {
        "allgather": 0,
        "allgatherv": 1,
        "allreduce": 2,
        "alltoall": 3,
        "alltoallv": 4,
        "alltoallw": 5,
        "barrier": 6,
        "bcast": 7,
        "exscan": 8,
        "gather": 9,
        "gatherv": 10,
        "reduce": 11,
        "reduce_scatter": 12,
        "reduce_scatter_block": 13,
        "scan": 14,
        "scatter": 15,
        "scatterv": 16,
    }
    id = switch.get(collective, "Invalid collective")
    return id

def load_single_result(file_name, collective):
    if collective in imb_collectives:
        return load_imb_single_result(file_name, collective)
    else:
        return load_omb_single_result(file_name, collective)

def load_imb_single_result(file_name, collective):
    from string import atoi, atof, split
    try:
        f = open(file_name)
    except Exception as e:
        print "Error, cannot find file "+file_name+". Exiting.."
        sys.exit()
    l = f.readline()
    while l.find("Benchmarking") < 0:
        l = f.readline()
        if l == "":
            print "Error parsing "+file_name+" No data found. Exiting.."
            sys.exit()
    result = []
    l = f.readline()
    l = f.readline()
    l = f.readline()
    pattern_arr = l.split()
    if pattern_arr == ['#repetitions', 't_min[usec]', 't_max[usec]', 't_avg[usec]']:
        expected_len = 4
        avg_lat_column = 3
    elif pattern_arr == ['#bytes', '#repetitions', 't[usec]', 'Mbytes/sec', 'defects']:
        expected_len = 5
        avg_lat_column = 2
    elif pattern_arr == ['#bytes', '#repetitions', 't_min[usec]', 't_max[usec]', 't_avg[usec]']:
        expected_len = 5
        avg_lat_column = 4
    elif pattern_arr == ['#bytes', '#repetitions', 't_min[usec]', 't_max[usec]', 't_avg[usec]', 'defects']:
        expected_len = 6
        avg_lat_column = 4
    elif pattern_arr == ['#bytes', '#repetitions', 't_min[usec]', 't_max[usec]', 't_avg[usec]', 'Mbytes/sec', 'defects']:
        expected_len = 7
        avg_lat_column = 4
    else:
        print("Error parsing "+file_name+". Unknown data pattern! Exiting..")
        sys.exit()

    l = f.readline()
    while len(l) > 0:
        itmlst = split(l)
        if len(itmlst) == expected_len:
            try:
                if collective == "barrier":
                    msg_siz = 0
                else:
                    msg_siz = atoi(itmlst[0])
                lat = atof(itmlst[avg_lat_column])
                result.append((msg_siz,lat))
            except Exception as e:
                print "Error parsing "+file_name+". Data corrupted. Exiting.."
                sys.exit()
        elif len(itmlst) == 0:
            break
        else:
            print "Error parsing "+file_name+". Data format doesn't match. Exiting.."
            sys.exit()
        l = f.readline()
    return result

def load_omb_single_result(file_name, collective):
    from string import atoi, atof, split
    try:
        f = open(file_name)
    except Exception as e:
        print "Error, cannot find file "+file_name+". Exiting.."
        sys.exit()
    l = f.readline()
    l = f.readline()
    while l.find("#")==0:
        l = f.readline()
        if l == "":
            print "Error parsing "+file_name+" No data found. Exiting.."
            sys.exit()
    result = []
    if (collective == "barrier"):
        expected_len = 1
        avg_lat_column = 0
    else:
        expected_len = 2
        avg_lat_column = 1
    while len(l)>0:
        itmlst = split(l)
        if len(itmlst) == expected_len:
            try:
                if collective == "barrier":
                    msg_siz = 0
                else:
                    msg_siz = atoi(itmlst[0])
                lat = atof(itmlst[avg_lat_column])
                result.append((msg_siz,lat))
            except Exception as e:
                print "Error parsing "+file_name+". OMB Data corrupted. Exiting.."
                sys.exit()
        else:
            print "Error parsing "+file_name+". Data format doesn't match. Exiting.."
            sys.exit()
        l = f.readline()
    return result

class AlgResult:

    def __init__(self, raw_dir, num_rank, alg, num_run, collective):
        from math import sqrt
        self.m_msgsizlst = []
        sum_list = []
        sum_sqr_list = []
        for i in xrange(num_run):
            file_name = "%s/%s_%dranks_run%d.out" %(raw_dir, alg, num_rank, i)
            single_result = load_single_result(file_name, collective)
            if i == 0:
                for m,v in single_result:
                    self.m_msgsizlst.append(m)
                    sum_list.append(v)
                    sum_sqr_list.append(v*v)
            else:
                assert len(self.m_msgsizlst) == len(single_result)
                for j,(m,v) in enumerate(single_result):
                    assert self.m_msgsizlst[j] == m
                    sum_list[j] += v
                    sum_sqr_list[j] += v*v

        self.m_latlst = [None] * len(self.m_msgsizlst)
        self.m_sgmlst = [None] * len(self.m_msgsizlst)

        if num_run == 1:
            self.m_latlst[:] = sum_list[:]
            self.m_sgmlst[:] = 0.0
        else:
            for j in xrange(len(self.m_msgsizlst)):
                self.m_latlst[j] = sum_list[j]/num_run
                # Standard deviation calculation
                var = (sum_sqr_list[j] - sum_list[j]*sum_list[j]/num_run)/(num_run-1)
                if var <= 0:
                    self.m_sgmlst[j] = 0
                else:
                    self.m_sgmlst[j] = sqrt((sum_sqr_list[j] - sum_list[j]*sum_list[j]/num_run)/(num_run-1))

    def msgsizlst(self):
        return self.m_msgsizlst

    # Latency list
    def latlst(self):
        return self.m_latlst
    # Sigma list (Standard deviation)
    def sgmlst(self):
        return self.m_sgmlst

class NumRankResult:

    def __init__(self, config, num_alg, exclude_alg, two_proc_alg, raw_dir, num_rank, collective):
        num_run = config.getInt("number_of_runs_per_test")
 
        self.m_msgsizlst = None
        self.m_result = {}
        self.m_refalg = 0
        for alg in range(num_alg + 1):
            if alg in exclude_alg or (alg == two_proc_alg and num_rank > 2):
                continue
            self.m_result[alg] = AlgResult(raw_dir, num_rank, alg, num_run, collective)
            if self.m_msgsizlst is None:
                self.m_msgsizlst = self.m_result[alg].msgsizlst()[:]
            else:
                assert len(self.m_msgsizlst) == len(self.m_result[alg].msgsizlst())
                for j,m in enumerate(self.m_msgsizlst):
                    assert(m == self.m_msgsizlst[j])

        self.m_selectAlg = [None]*len(self.m_msgsizlst)
        self.m_selectLat = [None]*len(self.m_msgsizlst)
        self.m_selectSgm = [None]*len(self.m_msgsizlst)

        for i in xrange(len(self.m_msgsizlst)):
            for alg in self.m_result.keys():
                if alg == 0:
                    continue
                result = self.m_result[alg]
                if (self.m_selectAlg[i] is None) or self.m_selectLat[i] > result.latlst()[i]:
                        self.m_selectAlg[i] = alg
                        self.m_selectLat[i] = result.latlst()[i]
                        self.m_selectSgm[i] = result.sgmlst()[i]

    def msgsizlst(self):
        return self.m_msgsizlst

    def selectAlg(self):
        return self.m_selectAlg

    def selectLat(self):
        return self.m_selectLat

    def selectSgm(self):
        return self.m_selectSgm

    def refalg(self):
        return self.m_refalg

    def reflat(self):
        return self.m_result[self.m_refalg].latlst()

    def refsgm(self):
        return self.m_result[self.m_refalg].sgmlst()

    def alglatstr(self, alg, i):
        lat = self.m_result[alg].latlst()[i]
        sgm = self.m_result[alg].sgmlst()[i]
        if sgm==0.0:
            return "%.2f" % lat
        else:
            return "%.2f(%.2f)" % (lat,sgm)

def writeResult(num_rank_list, coll_result, outfil):
    TITLES = ["#Nranks", "Message_size", "Best_Algorithm", "Best_Latency", "Ref_Algorithm", "Ref_Latency", "Speedup"]
    WIDTHS = [10,        12,             15,               20,             15,              20,             15]
    f = open(outfil, "w")

    print >> f, ""

    fmtlst = [None]*len(TITLES)
    for i,t in enumerate(TITLES):
        fmtlst[i] = "%-" + str(WIDTHS[i]) + "s"
        print >> f, (fmtlst[i] % t),
    print >> f, ""

    for num_rank in num_rank_list:
        nod_result = coll_result[num_rank]
        for i,msg_siz in enumerate(nod_result.msgsizlst()):
            select_alg = nod_result.selectAlg()[i]
            ref_alg = nod_result.refalg()

            print >> f, (fmtlst[0] % str(num_rank)),
            print >> f, (fmtlst[1] % str(msg_siz)),
            print >> f, (fmtlst[2] % select_alg),
            print >> f, (fmtlst[3] % nod_result.alglatstr(select_alg,i)),
            print >> f, (fmtlst[4] % ref_alg),
            print >> f, (fmtlst[5] % nod_result.alglatstr(ref_alg, i)),

            selectLat = nod_result.selectLat()[i]
            reflat = nod_result.reflat()[i]
            ratstr = "%.2f" % (reflat/selectLat)
            print >> f, (fmtlst[6] % ratstr)

def writeDetail(params, coll_result, outfil, num_alg, exclude_alg, two_proc_alg, num_run, num_rank_list):
    f = open(outfil, "w")
    print >> f, "%-10s" % "#Nnodes",
    print >> f, "%-12s" % "Message_size",
    for alg in range(num_alg + 1):
        if alg in exclude_alg:
            continue
        print >> f, "%-20s" % alg,
    print >> f, ""
    for num_rank in num_rank_list:
        result = coll_result[num_rank]
        for i,msg_siz in enumerate(result.msgsizlst()):
            print >> f, "%-10d" % num_rank,
            print >> f, "%-12d" % msg_siz,
            for alg in range(num_alg + 1):
                if alg in exclude_alg:
                    continue
                elif alg == two_proc_alg and num_rank > 2:
                    lat_str = "No data"
                else:
                    lat_str = result.alglatstr(alg, i)
                print >> f, "%-20s" % lat_str,

            print >> f, "%-20s" % result.alglatstr(result.refalg(),i)


def writeDecision(config, dir_path, outfil):
    collective_list = config.getStrlst("collectives")
    num_rank_list = config.getIntlst("number_of_ranks")
    num_run = config.getInt("number_of_runs_per_test")

    num_coll = len(collective_list)
    output_dir = dir_path+"/output"
    job_dir = dir_path+"/collective_jobs"
    f = open(outfil, "w")
    print >> f, "%-10s" % num_coll, "# Number of collectives"
    for collective in collective_list:
        if not os.path.exists(dir_path+"/output/"+collective):
            print "Collective "+collective+" output not detected. Exiting."
            return

        params = Params( job_dir+"/"+collective+".job" )
        num_alg = params.getInt("number_of_algorithms")
        exclude_alg = params.getIntlst("exclude_algorithms")
        two_proc_alg = -1
        try:
            two_proc_alg = params.getInt("two_proc_alg")
        except Exception as e:
            print "No two proc algorithm for "+collective
        raw_dir = dir_path+"/output/"+collective

        coll_result = {}
        for num_rank in num_rank_list:
            coll_result[num_rank] = NumRankResult(config, num_alg, exclude_alg, two_proc_alg, raw_dir, num_rank, collective)

        writeResult(num_rank_list, coll_result, raw_dir+"/best.out")
        print "Result wrote for "+collective+" to "+collective+"/best.out"

        print >> f, "%-10s" % coll_id_from_name(collective), "# Collective ID for", collective

        com_sizes = len(num_rank_list)
        print >> f, "%-10s" % com_sizes, "# Number of com sizes"
        for num_rank in num_rank_list:
            nod_result = coll_result[num_rank]
            print >> f, "%-10s" % num_rank, "# Com size"
            best = Params( output_dir+"/"+collective+"/best.out" )
            best_alg = 0
            # Open MPI requires that all data should start from msg size 0.
            # The default one is `0 0 0 0\n`
            # For collective data starts from msg size 0 (barrier or
            # collectives benchmarked by IMB) this line could be updated.
            if nod_result.msgsizlst()[0] == 0:
                num_sizes = 0
                size_output = ""
            else:
                num_sizes = 1
                size_output = "0 0 0 0\n"
            for i,msg_siz in enumerate(nod_result.msgsizlst()):
                new_alg = nod_result.selectAlg()[i]
                if new_alg == best_alg:
                    continue
                best_alg = new_alg
                num_sizes += 1
                size_output += str(msg_siz)
                size_output += " " + str(best_alg)
                size_output += " 0"
                size_output += " 0\n"
            print >> f, "%-10s" % num_sizes, "# Number of msg sizes"
            print >> f, size_output,
        writeDetail(params, coll_result, raw_dir+"/detail.out", num_alg, exclude_alg, two_proc_alg, num_run, num_rank_list)

def main():
    from sys import argv
    dir_path = os.path.dirname(os.path.realpath(__file__))
    if not os.path.exists(dir_path+"/output"):
        print "No output detected. Exiting."
        return

    config = Params( argv[1] )

    writeDecision(config, dir_path, "output/decision.file")
    print "Tuning file written to output/decision.file"

if __name__ == "__main__":
    main()
