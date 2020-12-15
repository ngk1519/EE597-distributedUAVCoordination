#!/bin/bash

coredir=$(ls /tmp | grep pycore)
filedir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

#vcmd -c /tmp/$coredir/n1 -- killall track_target_grpc.py
#vcmd -c /tmp/$coredir/n2 -- killall track_target_grpc.py
#vcmd -c /tmp/$coredir/n3 -- killall track_target_grpc.py
#vcmd -c /tmp/$coredir/n4 -- killall track_target_grpc.py
#vcmd -c /tmp/$coredir/n6 -- killall track_target_grpc.py
#vcmd -c /tmp/$coredir/n7 -- killall track_target_grpc.py
#vcmd -c /tmp/$coredir/n8 -- killall track_target_grpc.py
#vcmd -c /tmp/$coredir/n9 -- killall track_target_grpc.py

pkill -f track_target_grpc.py

vcmd -c /tmp/$coredir/n1 -- core-python -u $filedir/track_target_grpc.py -my 1 -i 500 -p $1 > /tmp/track_n1.log 2>&1 &
vcmd -c /tmp/$coredir/n2 -- core-python -u $filedir/track_target_grpc.py -my 2 -i 500 -p $1 > /tmp/track_n2.log 2>&1 &
vcmd -c /tmp/$coredir/n3 -- core-python -u $filedir/track_target_grpc.py -my 3 -i 500 -p $1 > /tmp/track_n3.log 2>&1 &
vcmd -c /tmp/$coredir/n4 -- core-python -u $filedir/track_target_grpc.py -my 4 -i 500 -p $1 > /tmp/track_n4.log 2>&1 &
vcmd -c /tmp/$coredir/n6 -- core-python -u $filedir/track_target_grpc.py -my 6 -i 500 -p $1 > /tmp/track_n6.log 2>&1 &
vcmd -c /tmp/$coredir/n7 -- core-python -u $filedir/track_target_grpc.py -my 7 -i 500 -p $1 > /tmp/track_n7.log 2>&1 &
vcmd -c /tmp/$coredir/n8 -- core-python -u $filedir/track_target_grpc.py -my 8 -i 500 -p $1 > /tmp/track_n8.log 2>&1 &
vcmd -c /tmp/$coredir/n9 -- core-python -u $filedir/track_target_grpc.py -my 9 -i 500 -p $1 > /tmp/track_n9.log 2>&1 &



