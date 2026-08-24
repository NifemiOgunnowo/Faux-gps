from random import randint
import cv2 as cv

aruco_dict = cv.aruco.custom_dictionary(4, 4)

marker_id = randint(1,2)
marker_size = 200

marker_image = cv.aruco.drawMarker(aruco_dict, marker_id, marker_size)
padding = 20

img = cv.copyMakeBorder(marker_image,padding,padding+70,padding,padding,cv.BORDER_CONSTANT, value=[255,255,255])

cv.imwrite(f'original_{marker_id}.jpg', img)