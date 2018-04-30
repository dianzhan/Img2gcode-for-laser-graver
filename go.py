#!/usr/bin/env python
from PIL import Image
import sys
import numpy as np
from pprint import pprint
from time import sleep

mmsize = 25.4 # from inc to mm
laser_resolution = 0.07 # in mm
laser_power = 250 # 0 - min, 255 - max
laser_burn_speed = 400 # speed laser maybe good
laser_move_speed = 400 # travel speed

start_gcode = """
G21 ; Set units to metric
G90 ; Absolute coordinates
G1 X0 Y0
G4 S3
"""
end_gcode = """
M106 P0 S255
"""

matrix_low_setpoint_threshold = 0.95 # used in get_matrix_low_dot for determine is dot set or not

img = Image.open("roads.bmp")

img_len_x = len(np.array(img)[0])
img_len_y = len(np.array(img))

matrix = [[0 for x in range(img_len_x)] for y in range(img_len_y)] # create matrix with image resolution

img_dpi = img.info.get('dpi')[0]
img_res_x = img_len_x*1.0/img_dpi*mmsize # img size in mm X
img_res_y = img_len_y*1.0/img_dpi*mmsize # img size in mm Y
dpi_mm = img_dpi*1.0/mmsize # dpi in mm
dots_in_sector = dpi_mm * laser_resolution # laser dot size in image resolution

arr = list(img.getdata())

def step_dot_pos(size):
  return int(round(size*dots_in_sector))
def step_dot_pos_float(size):
  return float(size*dots_in_sector)

def get_matrix_low_dot(step_x,step_y):
  points_sum = 0
  points_total = 0
  for x in range( step_dot_pos(step_x), step_dot_pos(step_x+1) ):
		for y in range( step_dot_pos(step_y), step_dot_pos(step_y+1) ):
			points_sum += matrix[y][x]
			points_total += 1
  if points_sum*1.0/points_total > matrix_low_setpoint_threshold :
		return 1
  else:
    return 0

def tomatrix(): # convert image array to matrix with img_len_x and img_len_y params
  i = 0
  j = 0
  for elem in arr:
    if i == img_len_x:
      j += 1
      i = 0
    if (elem == 255):
      matrix[j][i] = 0
    if (elem == 0):
      matrix[j][i] = 1
    i += 1

def show_matrix(): # show main matrix
  result = ''
  for row in matrix:
    for elem in row:
      if elem == 0:
        result += ' '
      if elem == 1:
        result += 'O'
    result += '\n'
  return result

def show_matrix_low(): # show low matrix 
  result = ''
  for row in matrix_low:
    for elem in row:
      if elem == 0:
        result += ' '
      if elem == 1:
        result += 'O'
    result += '\n'
  return result

def fill_matrix_low():
  #global stemps_x
  for x in range(0, steps_x-1):
    for y in range(0, steps_y-1):
      matrix_low[x][y] = get_matrix_low_dot(y,x)

def output_matrix():
  f = open('matrix.txt', 'w')
  f.write(show_matrix())
  f.close()

def output_matrix_low():
  f = open('matrix_low.txt', 'w')
  f.write(show_matrix_low())
  f.close()
  
def find_nearby_poligon(x_cur,y_cur):
  max_pos = steps_y
  x_pos = x_cur
  y_pos = y_cur
  x_result = x_cur
  y_result = y_cur
  module = 10000000 # big number ))
  if steps_x > steps_y:
    max_pos = steps_x
  for i in range(1, max_pos):
    for j in range(i*-1, i+1):
      for k in range(i*-1, i+1):
        x_pos = x_cur + j
        y_pos = y_cur + k
        if x_pos > steps_x:
          x_pos = steps_x-1
        if y_pos > steps_y:
          y_pos = steps_y-1
        if x_pos < 0:
          x_pos = 0
        if y_pos < 0:
          y_pos = 0
        try:
          if (matrix_low[x_pos][y_pos] == 1) and ( j != 0 ) and ( k != 0 ):
            if (abs(j) + abs(k)) < module:
              module = abs(j) + abs(k)
              x_result = x_pos
              y_result = y_pos
        except Exception:
          awd=1
    if (x_result != x_cur) or (y_result != y_cur):
	    return x_result, y_result
          #print x_pos,y_pos,"-----"
  exit(0)
	  
def print_gcode():
  pos_prev = 0
  print start_gcode
  for y in range(0, steps_y):
    if y % 2 == 1 :
      for x in range(0, steps_x):
        pos = matrix_low[y][x]
        if pos != pos_prev:
          x_cur = x
          if (pos == 1) :
            print "M106 P0 S" + str(laser_power)
            print "G1 X" + str(x*laser_resolution) + " Y" + str(y*laser_resolution) + " F" + str(laser_burn_speed)
          else:
            print "M106 P0 S0"
            print "G1 X" + str(x*laser_resolution) + " Y" + str(y*laser_resolution) + " F" + str(laser_move_speed)
        pos_prev = pos
    else:
      for x in range(steps_x-1, 0, -1):
        pos = matrix_low[y][x]
        if pos != pos_prev:
          x_cur = x
          if (pos == 1) :
            print "M106 P0 S" + str(laser_power)
            print "G1 X" + str(x*laser_resolution) + " Y" + str(y*laser_resolution) + " F" + str(laser_burn_speed)
          else:
            print "M106 P0 S0"
            print "G1 X" + str(x*laser_resolution) + " Y" + str(y*laser_resolution) + " F" + str(laser_move_speed)
        pos_prev = pos
  print end_gcode

def print_polygon(x,y):
  dir_cur = 'd'
  dir_cur2 = 'd'
  dir_exist = 1
  while (dir_exist > 0):
    dir_exist = 0

    if dir_cur2 == 'd': 
      if matrix_low[x][y-1] == 1: 
        dir_cur = 'd'
        dir_exist += 1
      elif matrix_low[x+1][y] == 1: 
        dir_cur = 'r'
        dir_exist += 1
      elif matrix_low[x][y+1] == 1: 
        dir_cur = 'u'
        dir_exist += 1
      elif matrix_low[x-1][y] == 1: 
        dir_cur = 'l'
        dir_exist += 1
    
    if dir_cur2 == 'r':
      if matrix_low[x+1][y] == 1:
        dir_cur = 'r'
        dir_exist += 1
      elif matrix_low[x][y+1] == 1:
        dir_cur = 'u'
        dir_exist += 1
      elif matrix_low[x-1][y] == 1:
        dir_cur = 'l'
        dir_exist += 1
      elif matrix_low[x][y-1] == 1:
        dir_cur = 'd'
        dir_exist += 1

    if dir_cur2 == 'u':
      if matrix_low[x][y+1] == 1:
        dir_cur = 'u'
        dir_exist += 1
      elif matrix_low[x-1][y] == 1:
        dir_cur = 'l'
        dir_exist += 1
      elif matrix_low[x][y-1] == 1:
        dir_cur = 'd'
        dir_exist += 1
      elif matrix_low[x+1][y] == 1:
        dir_cur = 'r'
        dir_exist += 1

    if dir_cur2 == 'l':
      if matrix_low[x-1][y] == 1:
        dir_cur = 'l'
        dir_exist += 1
      elif matrix_low[x][y-1] == 1:
        dir_cur = 'd'
        dir_exist += 1
      elif matrix_low[x+1][y] == 1:
        dir_cur = 'r'
        dir_exist += 1
      elif matrix_low[x][y+1] == 1:
        dir_cur = 'u'
        dir_exist += 1

    dir_cur2 = dir_cur
    matrix_low[x][y] = 0

    if dir_cur == 'd':
      (y,x) = (y-1,x)
      #print x,y
      print "G1 X" + str(x) + " Y" + str(y)
    if dir_cur == 'r':
      (y,x) = (y,x+1)
      #print x,y
      print "G1 X" + str(x) + " Y" + str(y)
      #simple gcode
    if dir_cur == 'u':
      (y,x) = (y+1,x)
      #print x,y
      print "G1 X" + str(x) + " Y" + str(y)
      #simple gcode
    if dir_cur == 'l':
      (y,x) = (y,x-1)
      #print x,y
      print "G1 X" + str(x) + " Y" + str(y)
      #simple gcode
    #sleep(0.1)
    if dir_exist == 0:
      return x,y

steps_x = int(round(img_len_x/step_dot_pos_float(1))) # number lines in matrix with laser_resolution X
steps_y = int(round(img_len_y/step_dot_pos_float(1))) # number lines in matrix with laser_resolution Y

matrix_low = [[0 for x in range(steps_x)] for y in range(steps_y)] # matrix for laser with laser_resolution

tomatrix()
fill_matrix_low()

#print_gcode()
output_matrix()
output_matrix_low()

(x,y) = find_nearby_poligon(0,0)
for i in range(1,100):
  (x,y) = print_polygon(x,y)
  (x,y) = find_nearby_poligon(x,y)

