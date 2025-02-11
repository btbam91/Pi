#!/etc/bin/python2.7

import pygame, time, sys
from omrond6t import *
from pygame.locals import *
import RPi.GPIO as GPIO


omron = OmronD6T(arraySize=16)

time_delay = .05
temp_difference = 13



#GPIO Initializers
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)
p = GPIO.PWM(18, 50)  # channel=12 frequency=50Hz
p.start(0)
p.ChangeDutyCycle(70.0/10.0)
time.sleep(time_delay)

SCREEN_DIMS = [500, 500]
xSize = 4 
ySize = 4 
arraySize = xSize * ySize
screen = pygame.display.set_mode(SCREEN_DIMS)
pygame.display.set_caption('Omron D6T Temperature Array')
pygame.mouse.set_visible(False)
pygame.init()
font = pygame.font.Font(None, 36)
font2 = pygame.font.Font(None, 72)

X = []
Y = []
temp_hit = 0
square = []
center = []
rect = [Rect] * arraySize

cellWidth = (SCREEN_DIMS[0]) / xSize
cellHeight = SCREEN_DIMS[1] / ySize
cellWidthCenter = cellWidth / 2 
if cellHeight > cellWidth:
  cellHeight = cellWidth
cellHeightCenter = cellHeight / 2 

#Calculate cell edge pixel in x direction 
for x in range(xSize):
    X.append(x * cellWidth)

#Calculate cell edge pixel in the y direction
for y in range(ySize):
    Y.append(y*cellWidth) #(y * cellHeight) + (SCREEN_DIMS[1] - cellHeight))

for y in range(ySize):
  for x in range(xSize):
    square.append((X[x], Y[y], cellWidth, cellHeight))
    center.append((X[x] + cellWidthCenter, Y[y] + cellHeightCenter))

def temp_to_rgb(temp):
  if temp < 76:
    return (0, 0, 192)
  elif temp >= 76 and temp < 90:
    return (255, 128, 0)
  elif temp > 90:
    return (255, 0, 0)

hit_start_time = time.time()
hit_time = 11
person_detect = False

text = font.render('Omron D6T Thermal Sensor', 1, (255,255,255))
text_pos = text.get_rect()
text_pos.center = ((SCREEN_DIMS[0])/4,SCREEN_DIMS[1] - cellHeight - 18)
screen.blit(text, text_pos)


# define the function blocks


def Cell_One():
    row = [temperature[maxCell]]
    row.insert(1,temperature[maxCell+1])
    row.insert(2,temperature[maxCell+2])
    row.insert(3,temperature[maxCell+3])
#multiply  based on max-min
    setDutyCycle(row)


def Cell_Two():
    row = [temperature[maxCell-1]]
    row.insert(1,temperature[maxCell])
    row.insert(2,temperature[maxCell+1])
    row.insert(3,temperature[maxCell+2])
    setDutyCycle(row)

def Cell_Three():
    row = [temperature[maxCell-2]]
    row.insert(1,temperature[maxCell-1])
    row.insert(2,temperature[maxCell])
    row.insert(3,temperature[maxCell+1])
    setDutyCycle(row)
    
def Cell_Four():
    row = [temperature[maxCell-3]]
    row.insert(1,temperature[maxCell-2])
    row.insert(2,temperature[maxCell-1])
    row.insert(3,temperature[maxCell])
    setDutyCycle(row)

def setDutyCycle(values):
    print "Temp Value Read: ", ["%.2f" % member for member in values]

    if((max(values)-min(values)) > temp_difference):
	multiplier = [values[0]-min(values),values[1]-min(values),values[2]-min(values),values[3]-min(values)]
	mValues = [multiplier[0]*values[0],multiplier[1]*values[1],multiplier[2]*values[2],multiplier[3]*values[3]]
	mulAvg  = sum(mValues)/len(mValues)
	weightedValue = [mValues[0]/mulAvg, mValues[1]/mulAvg, mValues[2]/mulAvg, mValues[3]/mulAvg]

	ServoValues = [weightedValue[0]*5,weightedValue[1]*7,weightedValue[2]*8,weightedValue[3]*10]

	DC = sum(ServoValues)/len(ServoValues)
    else:
    	print "Row: ", values, "\tMax-Min: ", (max(values)-min(values))
	DC = 7.5

    p.ChangeDutyCycle(DC)
    time.sleep(time_delay)

    print "DC: ", DC, "\n"
    

# map the inputs to the function blocks
function = {
            1 : Cell_One,
            2 : Cell_Two,
            3 : Cell_Three,
            0 : Cell_Four
}

while True:
  for event in pygame.event.get():
    if event.type == QUIT:
      pygame.display.quit()
      sys.exit(0)
    if event.type == KEYDOWN:
      if event.key == K_q or event.key == K_ESCAPE:
        pygame.display.quit()
        sys.exit(0)

  bytes_read, temperature = omron.read()
  #Something is wrong with the room temp. It is much greater than the other cells
  #print omron.roomTemp
  temp_hit = 0
  maxCell = -1
  for i in range(arraySize):
    if temperature[i] >= 76:
      temp_hit += 1
    
    #print(temperature[i],  i) 
    screen.fill(temp_to_rgb(temperature[i]), square[i])
    #Can this calculation be done before the loop? BP
    if max(temperature) > 70:
	    maxCell = temperature.index(max(temperature))
	    #print ["%.2f" % member for member in temperature]
	    #print maxCell, ": ", temperature[maxCell], "\n"
	    print "\n"
	    function[(maxCell+1)%4]()
    else:
	p.ChangeDutyCycle(7.0)
	time.sleep(time_delay)
 
    
    
    #text = font.render(str(i+1), 12, (255,255,255))
    #text_pos = text.get_rect()
    #text_pos.center = (center[i][0], SCREEN_DIMS[1] - cellHeight + 18)
    #screen.blit(text, text_pos)
    
    if maxCell !=-1 & i != maxCell:
    	text = font.render(str(int(temperature[i]))+" "+str(i+1) + chr(0xb0) + "F", 1, (255,255,255))
    else:
	text = font.render(str(int(temperature[i]))+" "+str(i+1) + chr(0xb0) + "F", 1, (0,0,0)) 
    text_pos = text.get_rect()
    text_pos.center = center[i]
    screen.blit(text, text_pos)
  
  #Trigger Person Detection###############################################################
  hit_time = time.time() - hit_start_time

  if temp_hit > 3:
    person_detect = True
    hit_start_time = time.time()
  elif temp_hit <= 3 and hit_time > 10:
    person_detect = False

  if person_detect:    
    #screen.fill((0,0,0), (0,180,SCREEN_DIMS[0],180))
    #screen.fill((255,0,0), (0,0,SCREEN_DIMS[0],180))
    text = font2.render('RESERVED', 1, (255,255,255))
    text_pos = text.get_rect()
    text_pos.center = (SCREEN_DIMS[0]/2,90)
    screen.blit(text, text_pos)
    

  else:
    text = font2.render('AVAILABLE', 1, (255,255,255))
    text_pos = text.get_rect()
    text_pos.center = (SCREEN_DIMS[0]/2,90)
    screen.blit(text, text_pos)
    

  pygame.display.update()
  time.sleep(0.01)
