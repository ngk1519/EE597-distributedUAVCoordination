#!/usr/bin/python

# Advance a vehicle towards a target and then move in a circle
# pattern around it

import sys
import math
import time
import subprocess

import threading

from core.api.grpc import client
from core.api.grpc import core_pb2

from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import sys

filepath = "/tmp/"

targets = dict()
iconpath = "/data/uas-core/icons/uav/"


#---------------
# Change icon of node based on the color
#---------------
def SetColor(core, session_id, node_id, color, nodetype):
  if nodetype == "uav":
    iconname = color + '_plane.png'
  if nodetype == "target":
    iconname = color + '_dot.png'
  iconfile = iconpath + iconname
  response = core.edit_node(session_id=session_id, node_id=node_id, icon=iconfile)  
  response = core.get_node(session_id, node_id)  
  print("SetColor for Node %d: %s" % (response.node.id, response.node.icon))


#---------------
# Determine the color to set for the target
#---------------
def ColorTarget(core, session_id, uavnode):
  color = 'grey'

  if uavnode.oldtrackid != -1 and uavnode.trackid == -1:
    SetColor(core, session_id, uavnode.oldtrackid, color, "target")

  if uavnode.oldtrackid == -1 and uavnode.trackid != -1: 
    color_id = uavnode.trackid % len(colors)
    color = colors[color_id]
    SetColor(core, session_id, uavnode.trackid, color, "target")

#---------------
# Calculate the distance between two points (on a map)
#---------------
def Distance(x1, y1, x2, y2):
  return math.sqrt(math.pow(y2-y1, 2) + math.pow(x2-x1, 2))


#---------------
# Define a CORE UAV node
#---------------
class CoreUav():
  def __init__(self, core, session_id, node_id, x, y, wypt_x, wypt_y):
      self.core = core
      self.session_id = session_id
      self.node_id = node_id
      self.target = -1
      self.position = (x,y)
      self.orig_wypt = (wypt_x,wypt_y)
      self.track_wypt = (wypt_x,wypt_y)

  def getPosition(self):
    return self.position
    
  def setPosition(self, x, y):
    self.position = (x, y)
    return True

  def getTarget(self):
    return self.target
    
  def setTarget(self, target):
    self.target = target
    color = "grey"
    if target in targets: 
      color = targets[target]
    SetColor(self.core, self.session_id, self.node_id, color, "uav")
    return color

  def getPotentialTargets(self, covered_zone=1200, track_range=600):
    potential_targets = []

    for target_id in targets: 

      response = self.core.get_node(self.session_id, target_id)
      node = response.node
      target_x, target_y = node.position.x, node.position.y
      uav_x, uav_y = self.position[0], self.position[1]
      distance = Distance(uav_x, uav_y, target_x, target_y)

      if target_x <= covered_zone:
        if Distance(uav_x, uav_y, target_x, target_y) <= track_range:
          potential_targets.append(target_id)

    return potential_targets
    
  def getWypt(self):
    return self.track_wypt

  def setWypt(self, x, y):
    self.track_wypt = (x,y)
    return True

  def getOriginalWypt(self):
    return self.orig_wypt

  def setOriginalWypt(self, x, y):
    self.orig_wypt = (x,y)
    return True

#---------------
# Find the new position as a vehicle moves towards a waypoint
#---------------
def MoveToWaypoint(xold, yold, xwypt, ywypt, speed, duration):
  movedist = speed * duration
  totaldist = Distance(xold, yold, xwypt, ywypt)
  ratio = movedist/totaldist

  xnew = xold + (xwypt-xold)*ratio
  ynew = yold + (ywypt-yold)*ratio

  return xnew, ynew

#---------------
# Move a node clock-wise around a circle
#---------------
def MoveOnCircle(xnode, ynode, xcenter, ycenter, radius, distance):
  posangle = math.atan2(ynode-ycenter, xnode-xcenter)
  moveangle = -distance/radius # That's negative for counter-clockwise,
                               # but in CORE Y coordinates are reversed...
  xnew = xcenter + radius*math.cos(posangle-moveangle)
  ynew = ycenter + radius*math.sin(posangle-moveangle)
    
  return xnew, ynew
  

#---------------
# Move the vehicle towards the target if it's far away,
# or on a circle around the target if it's close enough
#---------------
def MoveVehicle(xold, yold, xtrgt, ytrgt, rad, speed, duration):
  # Check whether the vehicle is outside the circle around the target  
  trgtdist = Distance(xold, yold, xtrgt, ytrgt)
  movedist = speed * duration
  if trgtdist >= rad:
    # Check if the vehicle would still be outside the circle after moving
    if trgtdist - movedist >= rad:
      xnew, ynew = MoveToWaypoint(xold, yold, xtrgt, ytrgt, speed, duration)
      return xnew, ynew
    else:
      # Moving to the circle and then moving on the circle for the rest of
      # the distance
      if trgtdist == 0:      # Special case: vehicle is collocated with 
        return xold, yold    # the target and radius is zero
      
      tocircledist = trgtdist - rad
      circledist = movedist - tocircledist
      ratio = tocircledist/trgtdist
      xcircle = xold + (xtrgt-xold)*ratio
      ycircle = yold + (ytrgt-yold)*ratio

      xnew, ynew = MoveOnCircle(xcircle, ycircle, xtrgt, ytrgt, rad, circledist)
      return xnew, ynew
  else:
    # Vehicle is inside the circle; needs to move away from the target to
    # join the circle

    # Find the waypoint on the circle in straight move
    tocircledist = rad - trgtdist
    if trgtdist == 0:   #Special case: vehicle is collocated with target
      xcircle = xtrgt+rad
      ycircle = ytrgt
    else:
      ratio = rad/trgtdist
      xcircle = xtrgt + (xold-xtrgt)*ratio
      ycircle = ytrgt + (yold-ytrgt)*ratio

    # Check if the vehicle would still be outside the circle after moving 
    if movedist + trgtdist <= rad:
      # Moving in a straight line inside the circle
      xnew, ynew = MoveToWaypoint(xold, yold, xcircle, ycircle, speed, duration)
      return xnew, ynew
    else:
      # Moving straight to the circle until hitting the circle waypoint and then
      # moving on the circle from there for the rest of the distance 
      circledist = movedist - tocircledist
      xnew, ynew = MoveOnCircle(xcircle, ycircle, xtrgt, ytrgt, rad, circledist)
      return xnew, ynew

#---------------
# Initialize XML RPC Server for CORE scenario
#---------------
class StartXmlRpcServerThread(threading.Thread):
  def __init__(self, core_uav):
    threading.Thread.__init__(self)
    self.uav = core_uav

  def run(self):
    StartXmlRpcServer(self.uav)

def StartXmlRpcServer(core_uav):
  while 1: 
    with SimpleXMLRPCServer(("localhost", 8000)) as server:
      server.register_instance(core_uav, allow_dotted_names=True)
      server.register_multicall_functions()
      print('Serving XML-RPC on localhost port 8000')
      try:
          server.serve_forever()
      except:
          print("\nKeyboard interrupt received, exiting.")
          sys.exit(0)


#---------------
# main
#---------------
def main():
  global targets

  # Original waypoints
  original_wypts = {1: (100,150), 2: (100, 300), 3: (100, 450), 4: (100, 600), 
                    6: (400, 150), 7: (400, 300), 8: (400, 450), 9: (400, 600)}

  # Targets colors
  colors = ['blue', 'yellow', 'green', 'red', 'lime', 'orange', 'pink', 'purple', 'lavender', 'cyan']
  targets = {11: colors[0], 12: colors[1], 13: colors[2], 14: colors[3], 
            16: colors[4], 17: colors[5], 18: colors[6], 19: colors[7]}

  # Get command line inputs 
  if len(sys.argv) >= 7:
    node_id  = int(sys.argv[1])
    xuav  = int(sys.argv[2])
    yuav  = int(sys.argv[3])
    rad   = int(sys.argv[4])
    speed = float(sys.argv[5])
    msecduration  = float(sys.argv[6])
    duration = msecduration/1000
  else:
    print("move_node.py nodenum xuav yuav radius speed duration(msec)\n")
    sys.exit()

  # Create grpc client
  core = client.CoreGrpcClient("172.16.0.254:50051")
  core.connect()
  response = core.get_sessions()
  if not response.sessions:
    raise ValueError("no current core sessions")
  session_summary = response.sessions[0]
  session_id = int(session_summary.id)
  session = core.get_session(session_id).session

  # Set CORE UAV
  node_wypt = original_wypts[node_id]
  core_uav = CoreUav(core, session_id, node_id, xuav, yuav, node_wypt[0], node_wypt[1])

  # Initialize targets
  SetColor(core, session_id, node_id, 'grey', "uav")
  for target_id, color in targets.items():
    SetColor(core, session_id, target_id, color, "target")

  print("Start XML RPC thread")

  # Initiate xmlrpc server
  xml_rpc_server_thread = StartXmlRpcServerThread(core_uav)
  xml_rpc_server_thread.start()

  print("Start MOVE UAV thread")

  # Move UAV node
  while 1:
    time.sleep(duration)
    position = core_uav.getWypt()
    xtrgt, ytrgt = position[0], position[1] 
    xuav, yuav = MoveVehicle(xuav, yuav, xtrgt, ytrgt, rad, speed, duration)
    #print("xuav: %d, yuav: %d" % (xuav, yuav))

    # Find UAV color to set
    target_id = core_uav.target
    color = "grey"
    if target_id in targets: 
      color = targets[target_id]
    icon_file_path = iconpath + color + "_plane.png"

    # Set position and keep current UAV color
    pos = core_pb2.Position(x = xuav, y = yuav)
    response = core.edit_node(session_id=session_id, node_id=node_id, position=pos, icon=icon_file_path)
    core_uav.setPosition(xuav, yuav)


      
if __name__ == '__main__':
  main()
