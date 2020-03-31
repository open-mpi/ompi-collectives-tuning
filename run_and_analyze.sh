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

usage()
{
	echo "Usage:
		$0
		   -c | --config-file <config>
Options:
		   --config-file (string)
			The file containing global configurations." 1>&2; exit 1;

}

OPTIONS=$(getopt -o :c: --long config-file: -- "$@")
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
				*) config_file=$2; shift 2;;
			esac;;
                '--')
                        shift
                        break
                ;;
                *) echo "Internal error!"; usage; exit 1 ;;
	esac
done

python coltune_script.py $config_file
if [ $? -ne 0 ]; then
	echo "Failed to create job scripts. Exiting.."
	exit 1;
fi
collectives=$(cat $config_file | grep "collectives")
collectives=$(cut -d ":" -f 2 <<< "$collectives")
work_dir=$(dirname "$0")

# Some work needed to automatically create qsub jobs and wait for completion
for collective in ${collectives// / } ; do
	qsub -N $collective -cwd $work_dir/output/$collective/${collective}_coltune.sh
done

collective_string=$(echo $collectives | sed 's/ /,/g')
qsub -hold_jid $collective_string $work_dir/analyze.sh -c $config_file

exit
