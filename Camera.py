import cv2 as cv #Version 3.4.17
import numpy as np
import datetime as dt

from jupyter_server.auth import passwd

#                                --------------BEGIN CONFIG--------------
############
#GPS CONFIG#
############
#Latitude per meter (for conversion)
Lat_per_meter = 9.044289888*(10**(-6))
#Longitude per meter (for conversion)
Long_per_meter = 8.983031054*(10**(-6))

# Dimensions of real area in meters
r_length = 50
r_width = 40

#Start coordinates (should match the coordinates for the top left of the test area. default(0,0))
starting_lat = 0
starting_long = 0

##############
#ARUCO CONFIG#
##############

#Color outline for marker detection
selection_color = (125,50,125)

#Marker dictionary
aruco_dict = cv.aruco.custom_dictionary(4,4)

#                                --------------END CONFIG--------------

def find_markers(img):
    img_bw = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

    def get_centre(rectangle: np.ndarray):
        x = (rectangle[0][0] + rectangle[2][0]) / 2
        y = (rectangle[0][1] + rectangle[2][1]) / 2
        return x, y

    def get_coordinates(rectangle: np.ndarray):
        # Dimensions of fake area
        v_length = img.shape[0]
        v_width = img.shape[1]

        # Mapping
        length_per_px = r_length / v_length
        width_per_px = r_width / v_width
        lat_per_px = length_per_px * Lat_per_meter
        long_per_px = width_per_px * Long_per_meter

        x, y = get_centre(rectangle)

        lat = (y * lat_per_px) + starting_lat
        long = (x * long_per_px) + starting_long

        short_lat = round(lat, 11)
        short_long = round(long, 11)
        return short_lat, short_long

    #Aruco detection
    corners, ids, rejected = cv.aruco.detectMarkers(img_bw,aruco_dict)

    #Marker processing
    if ids is not None:
        for i in range(len(ids)):
            #Output
            print(f'{ids[i][0]};{get_coordinates(corners[i][0])};{dt.datetime.now().time()}') #Extract Identified Markers
        cv.aruco.drawDetectedMarkers(img, corners, ids)

def get_nmea_frame(coordinates,timestamp):
    #Sentence type ($GPRMC, as it's essential)
    sentence_type = '$GPRMC'

    #Frame structure; $GPRMC,time,status,latitude,n/s,longitude,e/w,speed,course,date,magnetic variation,mode,checksum
    time = timestamp #UTC time in hhmmss.sss
    status = 'A' #Data validity; A=valid
    def get_lat(x): #latitude in ddmm.mmmm
        value = 0
        n_s = ''
        return f'{value},{n_s}'
    def get_long(x): #longitude in dddmm.mmmm
        value = 0
        e_w = ''
        return f'{value},{e_w}'
    speed = 0 #speed over ground in knots
    course = 0 #course over ground in degrees
    date = 0 #date in ddmmyy
    mode = 'A' #A(Autonomous), D(DGPS), E(DR)
    check_sum = '*10'
    end = f'\r\n'
    return f'{sentence_type},{time},{status},{get_lat(coordinates[0])},{get_long(coordinates[1])},{speed},{course},{date},,{mode},{check_sum}{end}'



def main(test_file):
    img = cv.imread(test_file,1)
    find_markers(img)

    # Show
    cv.imshow(test_file,img)
    cv.waitKey(0)
    cv.destroyAllWindows()

if __name__ == '__main__':
    main(f'IMGx4.jpg')
    # main('image.jpg')