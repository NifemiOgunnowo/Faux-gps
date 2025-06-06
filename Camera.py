import cv2 as cv #Version 3.4.17
import numpy as np
import datetime
import time
import math

#                                --------------BEGIN CONFIG--------------
############
#GPS CONFIG#
############
#Latitude per meter (for conversion)
Lat_per_meter = 9.044289888*(10**(-6))
#Longitude per meter (for conversion)
Long_per_meter = 8.983031054*(10**(-6))

# Dimensions of real area in meters
r_length = 100
r_width = 100

#Start coordinates (should match the coordinates for the top left of the test area. default(0,0))
starting_lat = 0
starting_long = 0

##############
#ARUCO CONFIG#
##############
#Video detection
window = 'Detection'
framerate = 0.5
delay = 1/framerate

#Color outline for marker detection
selection_color = (125,50,125)

#Marker dictionary
aruco_dict = cv.aruco.custom_dictionary(4,4)

#                                --------------END CONFIG--------------
def get_nmea_frame(raw_speed:float,coordinates:(float,float),timestamp:datetime.datetime):
    #Sentence type ($GPRMC, since it's the minimum requirement)
    sentence_type = '$GPRMC'

    #Frame structure; $GPRMC,time,status,latitude,n/s,longitude,e/w,speed,course,date,magnetic variation,mode,checksum
    frame_time = timestamp.strftime('%H%M%S.%f')[:-3] #UTC time in hhmmss.sss
    status = 'A' #Data validity; A=valid
    def get_lat(x): #latitude in ddmm.mmmm
        value = 0
        n_s = ''
        return f'{value},{n_s}'
    def get_long(x): #longitude in dddmm.mmmm
        value = 0
        e_w = ''
        return f'{value},{e_w}'
    speed = round(raw_speed * 1.94384449,2) #speed over ground in knots from m/s
    course = 0 #course over ground in degrees
    date = timestamp.strftime('%d%m%y') #date in ddmmyy
    mode = 'A' #A(Autonomous), D(DGPS), E(DR)
    check_sum = '*10'
    end = f'\r\n'
    return (f'{sentence_type},{frame_time},{status},{get_lat(coordinates[0])},'
            f'{get_long(coordinates[1])},{speed},{course},'
            f'{date},,{mode},{check_sum}{end}') #magnetic variation is ignored


def main():
    cap = cv.VideoCapture(0)

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
                    lat_per_px = length_per_px * Lat_per_meter
                    long_per_px = width_per_px * Long_per_meter

                    x, y = get_centre(rectangle)

                    if mode == 0:
                        return y*length_per_px, x*width_per_px

                    lat = (y * lat_per_px) + starting_lat
                    long = (x * long_per_px) + starting_long

                    short_lat = round(lat, 11)
                    short_long = round(long, 11)
                    return short_lat, short_long

                def get_distance(point1, point2):
                    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)


                # Aruco detection
                corners, ids, rejected = cv.aruco.detectMarkers(frame_bw, aruco_dict)
                corners2, ids2, rejected2 = cv.aruco.detectMarkers(frame2_bw, aruco_dict)

                # Marker processing
                if ids is not None and ids == ids2: #if same markers identified in both images
                    for i in range(len(ids)):
                        # Output
                        coordinates = get_coordinates(corners2[i][0])
                        print(get_nmea_frame(get_distance(get_coordinates(corners[i][0],0)
                                                          ,get_coordinates(corners2[i][0],0))/delay
                                             ,coordinates,current_time))# Extract Identified Markers
                    cv.aruco.drawDetectedMarkers(frame2, corners2, ids2)
                    cv.aruco.drawDetectedMarkers(frame, corners, ids)
                else: #if there are missing markers
                    pass
                    # for i in range(len(ids)):
                    #     # Output
                    #     coordinates = get_coordinates(corners[i][0])
                    #     print(
                    #         f'a;{ids[i][0]};{coordinates};{current_time}')  # Extract Identified Markers
                    # cv.aruco.drawDetectedMarkers(frame, corners, ids)
                    #
                    # if ids2 is not None:
                    #     for i in range(len(ids2)):
                    #         # Output
                    #         coordinates2 = get_coordinates(corners2[i][0])
                    #         print(
                    #             f's;{ids2[i][0]};{coordinates2};{current_time2}')  # Extract Identified Markers
                    #     cv.aruco.drawDetectedMarkers(frame2, corners2, ids2)


                cv.imshow(window, frame)
                cv.imshow(window+'2', frame2)


        if cv.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv.destroyAllWindows()

if __name__ == '__main__':
    main()
