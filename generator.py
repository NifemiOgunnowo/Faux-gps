from random import randint
import cv2 as cv
from cv2 import aruco
from Camera import aruco_dict

marker_id = randint(1,50)
marker_size = 200

marker_image = aruco.generateImageMarker(aruco_dict, marker_id, marker_size)
padding = 20

img = cv.copyMakeBorder(marker_image,padding,padding+70,padding,padding,cv.BORDER_CONSTANT, value=[255,255,255])

cv.imwrite(f'original_{marker_id}.jpg', img)