import cv2 as cv #Version 3.4.17
import numpy as np
import datetime
import time
import math
from locations import locations

#                                --------------BEGIN CONFIG--------------
############
#GPS CONFIG#
############
#Start coordinates (should match the coordinates for the top left of the test area. default(0,0))
starting_lat = 0
starting_long = 0

# Dimensions of real area in meters
r_length = 100
r_width = 100

#Getting the conversion constants
m1 = 111132.92     # latitude calculation term 1
m2 = -559.82       # latitude calculation term 2
m3 = 1.175         # latitude calculation term 3
m4 = -0.0023       # latitude calculation term 4
p1 = 111412.84     # longitude calculation term 1
p2 = -93.5         # longitude calculation term 2
p3 = 0.118         # longitude calculation term 3

#Latitude degree per meter (for conversion)
lat_per_meter = 1 / (m1 + (m2 * math.cos(2 * math.radians(starting_lat))) +
                     (m3 * math.cos(4 * math.radians(starting_lat))) +
                     (m4 * math.cos(6 * math.radians(starting_lat))))
#Longitude degree per meter (for conversion)
long_per_meter = 1 / ((p1 * math.cos(math.radians(starting_lat))) +
                      (p2 * math.cos(3 * math.radians(starting_lat))) +
                      (p3 * math.cos(5 * math.radians(starting_lat))))


##############
#ARUCO CONFIG#
##############
#Video detection
window = 'Detection'
framerate = 30
delay = 1/framerate
cam = 0 #0 for built-in camera, 1 for external. default (0)

#Color outline for marker detection
selection_color = (125,50,125)

#Marker dictionary
aruco_dict = cv.aruco.custom_dictionary(4,4)

#                                --------------END CONFIG--------------
def get_gprmc_frame(raw_speed:float, coordinates:(float, float), timestamp:datetime.datetime, course:float):
    #Sentence type ($GPRMC, since it's the minimum requirement)
    sentence_type = '$GPRMC'

    #Frame structure; $GPRMC,time,status,latitude,n/s,longitude,e/w,speed,course,date,magnetic variation,mode*checksum
    frame_time = timestamp.strftime('%H%M%S.%f')[:-3] #UTC time in hhmmss.sss
    status = 'A' #Data validity; A=valid
    def get_lat(x): #latitude in ddmm.mmmm
        abs_lat = abs(x)
        lat_degree = int(abs_lat)
        lat_minute = (abs_lat-lat_degree)*60
        n_s = 'N' if x > 0 else 'S'
        return f'{lat_degree}{lat_minute:.4f},{n_s}'
    def get_long(x): #longitude in dddmm.mmmm
        abs_long = abs(x)
        long_degree = int(abs_long)
        long_minute = (abs_long - long_degree) * 60
        e_w = 'E' if x > 0 else 'W'
        return f'{long_degree}{long_minute:.4f},{e_w}'
    speed = round(raw_speed * 1.94384449,2) #speed over ground in knots from m/s
    course = round(course,1) #course over ground in degrees
    date = timestamp.strftime('%d%m%y') #date in ddmmyy
    mode = 'A' #A(Autonomous), D(DGPS), E(DR); Only in newer Nmea versions
    def get_checksum(nmea_str):
        cs = 0
        if '$' in nmea_str:
            nmea_str = nmea_str.replace('$','')
        for char in nmea_str:
            cs ^= ord(char)
        return f"{cs:02X}"
    sentence = (f'{sentence_type},{frame_time},{status},{get_lat(coordinates[0])},'
                f'{get_long(coordinates[1])},{speed},{course},{date},,{mode}')
    checksum = get_checksum(sentence)
    end = f'\r\n'
    return f'{sentence}*{checksum}{end}'  #magnetic variation is ignored


def main():
    cap = cv.VideoCapture(cam)

    while True:
        ret, frame = cap.read()
        if not ret:
            print('Failed to grab frame')
            break
        else:
            time.sleep(delay)
            ret2, frame2 = cap.read()
            current_time = datetime.datetime.now() #time at second frame being taken
            if not ret2:
                print('Failed to grab second frame')
                break
            else:
                frame_bw = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
                frame2_bw = cv.cvtColor(frame2, cv.COLOR_BGR2GRAY)


                def get_coordinates(rectangle: np.ndarray, mode=1):
                    def get_centre(area: np.ndarray):
                        #Get centre of square area
                        x = (area[0][0] + area[2][0]) / 2
                        y = (area[0][1] + area[2][1]) / 2
                        return x, y

                    # Dimensions of fake area
                    v_length = frame.shape[0]
                    v_width = frame.shape[1]

                    # Mapping
                    length_per_px = r_length / v_length
                    width_per_px = r_width / v_width
                    lat_per_px = length_per_px * lat_per_meter
                    long_per_px = width_per_px * long_per_meter

                    x, y = get_centre(rectangle)

                    if mode == 0:
                        return y*length_per_px, x*width_per_px

                    lat = starting_lat - (y * lat_per_px)
                    long = (x * long_per_px) + starting_long

                    short_lat = round(lat, 11)
                    short_long = round(long, 11)
                    return short_lat, short_long

                def get_distance(point1, point2):
                    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

                def get_course(point1, point2):
                    delta_y = point1[0]-point2[0] #inversed because (0,0) is top left instead of bottom left
                    delta_x = point2[1]-point1[1]
                    if delta_x == 0 and delta_y == 0: #Object is stationary
                        return 0

                    #Edge cases
                    if delta_x == 0 and delta_y > 0:
                        return 0
                    elif delta_x == 0 and delta_y < 0:
                        return 180
                    elif delta_y == 0 and delta_x > 0:
                        return 90
                    elif delta_y == 0 and delta_x < 0:
                        return 270


                    slope = delta_y/delta_x
                    angle_x = math.degrees(math.atan(slope)) #angle with the x-axis
                    angle_y = 90 - angle_x #angle with y-axis
                    course = angle_y + 180 if delta_x<0 else angle_y
                    return course

                # Aruco detection
                corners, ids, rejected = cv.aruco.detectMarkers(frame_bw, aruco_dict)
                corners2, ids2, rejected2 = cv.aruco.detectMarkers(frame2_bw, aruco_dict)

                # Marker processing
                if ids is not None and ids == ids2: #if same markers identified in both images
                    for i in range(len(ids)):
                        # Output
                        coordinates = get_coordinates(corners2[i][0])
                        point_a = get_coordinates(corners[i][0],0)
                        point_b = get_coordinates(corners2[i][0],0)

                        # Extract Identified Markers
                        locations[int(ids[i][0])] = get_gprmc_frame(get_distance(point_a, point_b) / delay
                                                                    , coordinates
                                                                    , current_time,
                                                                    get_course(point_a,point_b))
                        print(locations[int(ids[i][0])])

                    cv.aruco.drawDetectedMarkers(frame2, corners2, ids2)
                    cv.aruco.drawDetectedMarkers(frame, corners, ids)
                else: #if there are missing markers
                    pass

                # cv.imshow(window, frame)
                cv.imshow(window+'2', frame2)


        if cv.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv.destroyAllWindows()

if __name__ == '__main__':
    main()
