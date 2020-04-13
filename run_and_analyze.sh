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
with_slurm=false

usage()
{
	echo "Usage:
		$0
		   -c | --config-file <config>
		   --with-slurm
Options:
		   --config-file (string)
			The file containing global configurations.
		   --with-slurm
			Use slurm instead of the default SGE." 1>&2; exit 1;

}

OPTIONS=$(getopt -o :c: --long with-slurm,config-file: -- "$@")

if [[ $? -ne 0 ]]; then
        usage
        exit 1
fi

eval set -- "$OPTIONS"
while true; do
        case "$1" in
                '-c'|'--config-file')
                        case "$2" in
				"") shift 2 ;;
				*) config_file=$2; shift 2 ;;
			esac
			;;
		'--with-slurm')
			with_slurm=true
			shift
			;;
                '--')
                        shift
                        break
			;;
                *) echo "Internal error!"; usage; exit 1 ;;
	esac
done

if [ "$config_file" = "" ]; then
	usage
	exit 1
fi

collectives=$(cat $config_file | grep "collectives")
collectives=$(cut -d ":" -f 2 <<< "$collectives")
work_dir=$(dirname "$0")

if [ $with_slurm = true ]; then
	python coltune_script.py $config_file slurm
	if [ $? -ne 0 ]; then
		echo "Failed to create job scripts. Exiting.."
		exit 1;
	fi
	for collective in ${collectives// / } ; do
		sbatch -W $work_dir/output/$collective/${collective}_coltune.sh
	done
	python coltune_analyze.py $config_file
else
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
fi

exit
