#!/bin/sh
#
#$ -j y
#
#$ -cwd
#
# Copyright (c) 2020      Amazon.com, Inc. or its affiliates.  All Rights
#                         reserved.
#
# Additional copyrights may follow
#

config_file=""

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

python coltune_analyze.py $config_file
