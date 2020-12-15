# Distributed UAV Coordination

Author: Kevin Ng, Xinhong Liu

## Project implementation description

This project was the final project of the course EE-597 Wireless Networks with the collaboration of Boeing at the Viterbi School of Engineering, University of Southern California.

The goal of this project was to design and build a reliable communication protocol for unmanned aerial vehicle (UAV) using User Datagram Protocol (UDP). The main mission was the following: each UAV can only track a single target at a time. Once a UAV has locked into a target, the UAV cannot change its target. All UAVs cannot switch targets unless the current one gets out of range.

The project was all done in the Common Open Research Emulator (CORE), a network emulator by Boeing.

## Source files

The following are the files and scripts in this project:

1. track_target_grpc.py
  The main file with the agreement protocol for UAVs tracking.

2. move_node_grpc.py
  This file is responsible for the basic movements of all UAVs and potential targets.

3. start_tracking_grpc.sh
  The main script for starting the tracking process with the UAVs.

4. uav8-notrack-new-gui.xml
  This file is responsible for setting up the swarm scenario for the UAVs and targets.

5. INTRO.txt
  The instruction for installing and setting up the necessary software before running this project.
