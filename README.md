Copyright (c) 2020      Amazon.com, Inc. or its affiliates.  All Rights
                        reserved.

$COPYRIGHT$

Additional copyrights may follow

$HEADER$

===========================================================================

Collectives Tuning

===========================================================================

Prerequisites:

        Python3.6
        SGE scheduler/Slurm scheduler
        OSU Micro Benchmarks
        Intel Micro Benchmarks

===========================================================================

Installing OSU Micro Benchmarks:

Run these commands to install osu micro benchmarks. Change $INSTALL_PATH
to be your desired install path. Change $MPI_INSTALL_PATH to your Open MPI
install path.

```
wget http://mvapich.cse.ohio-state.edu/download/mvapich/osu-micro-benchmarks-5.6.2.tar.gz
tar -xvf osu-micro-benchmarks-5.6.2.tar.gz
cd osu-micro-benchmarks-5.6.2
./configure --prefix=$INSTALL_PATH CC=$MPI_INSTALL_PATH/bin/mpicc CXX=$MPI_INSTALL_PATH/bin/mpicxx
make
make install
```

===========================================================================

Installing Intel Micro Benchmarks:

Run these commands to install IMB-MPI1. Change $MPI_INSTALL_PATH to your
Open MPI install path.

```
git clone https://github.com/intel/mpi-benchmarks.git
cd mpi-benchmarks
make IMB-MPI1 CC=$MPI_INSTALL_PATH/bin/mpicc CXX=$MPI_INSTALL_PATH/bin/mpicxx
```

===========================================================================

This repository is intended to create scripts and analyze results of
collectives to create a tuning decision file for Open MPI.

Currently, the only binaries supported are for OSU Micro Benchmarks and
Intel Micro Benchmarks for the following collectives:

        allgather
        allgatherv
        allreduce
        alltoall
        alltoallv
        barrier
        bcast
        gather
        reduce
        reduce_scatter_block
        reduce_scatter
        scatter

Currently, you need to create a config file - see "./examples/config" in order
to choose collectives, OMB collectives directory, IMB-MPI1 binary path,
cluster sizes, number of ranks, number of nodes, number of ranks per node,
and number of runs.

If you need to adjust the number of algorithms or exclude certain
algorithms, please adjust the file "./collective_jobs/<collective>.job"

In order to run the scripts, please run inside this directory
```
./run_and_analyze.sh -c <your config file>
```

If you wish to run with slurm instead of SGE, you must pass the "--with-slurm"
flag. It is recommended to run this flag inside tmux, screen, or similar
software as the slurm -W flag is utilized.
```
./run_and_analyze.sh -c <your config file> --with-slurm
```

This script will run and analyze all collectives specified. The output
will be saved under the ./output directory.

A decision file will be written under ./output/decision.file

Each collective will have a detailed output and a best output file under
./output/<collective>/detail.out and ./output/<collective>/best.out
respectively.
