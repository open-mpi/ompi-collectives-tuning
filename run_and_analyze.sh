#!/bin/bash
# Copyright (c) 2020      Amazon.com, Inc. or its affiliates.  All Rights
#                         reserved.
#
# $COPYRIGHT$
#
# Additional copyrights may follow
#
# $HEADER$
#

numcoll=0
config_file=""
scheduler="SGE"

usage()
{
    echo "Usage:
        $0
           -c | --config-file <config>
           --scheduler (PBS|SGE|slurm)
Options:
           -h,--help
            Print help message
           --config-file (string)
            The file containing global configurations.
           --scheduler (string)
            Specify scheduler to use, available options are PBS,SGE,slurm (default SGE)." 1>&2; exit 1;

}

OPTIONS=$(getopt -o :c:h -l help,scheduler:,config-file: -- "$@")

if [[ $? -ne 0 ]]; then
        echo "Command line error"
        usage
        exit 1
fi

eval set -- "$OPTIONS"
while true; do
        case "$1" in
            '-h'|'--help') usage; exit 0 ;;
            '-c'|'--config-file')
                case "$2" in
                    "") shift 2 ;;
                    *) config_file=$2; shift 2 ;;
                esac
            ;;
            '--scheduler')
                case "$2" in
                    "") shift 2 ;;
                    *) scheduler=$2; shift 2 ;;
                esac
            ;;
                '--')
                        shift
                        break
            ;;
                *) echo "Internal error!"; usage; exit 1 ;;
    esac
done

if [ "$config_file" = "" ]; then
    echo "Error: No config file specified."
    usage
    exit 1
fi

collectives=$(cat $config_file | grep "collectives")
collectives=$(cut -d ":" -f 2 <<< "$collectives")
work_dir=$(realpath $(dirname "$0"))

case "$scheduler" in
    "slurm")
        python coltune_script.py $config_file slurm
        if [ $? -ne 0 ]; then
            echo "Failed to create job scripts. Exiting.."
            exit 1;
        fi
        for collective in ${collectives// / } ; do
            sbatch -W $work_dir/output/$collective/${collective}_coltune.sh
        done
        python coltune_analyze.py $config_file
    ;;
    "SGE")
        python coltune_script.py $config_file sge
        if [ $? -ne 0 ]; then
            echo "Failed to create job scripts. Exiting.."
            exit 1;
        fi

        for collective in ${collectives// / } ; do
            qsub -N $collective -cwd $work_dir/output/$collective/${collective}_coltune.sh
        done
        collective_string=$(echo $collectives | sed 's/ /,/g')
        qsub -hold_jid $collective_string $work_dir/analyze.sh -c $config_file
    ;;
    "PBS")
        python coltune_script.py $config_file pbs
        if [ $? -ne 0 ]; then
            echo "Failed to create job scripts. Exiting.."
            exit 1;
        fi

        for collective in ${collectives// / } ; do
            pushd $work_dir/output/$collective/
            qsub ${collective}_coltune.sh
            popd
        done
    ;;
    *) echo "Error: Unknown scheduler '$scheduler'."; usage; exit 1 ;;
esac

exit
