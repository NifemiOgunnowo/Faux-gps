import cv2 as cv #Version 3.4.17
import numpy as np
import datetime
import time
import math

class Detector:
    # Conversion constants
    M1 = 111132.92  # latitude calculation term 1
    M2 = -559.82  # latitude calculation term 2
    M3 = 1.175  # latitude calculation term 3
    M4 = -0.0023  # latitude calculation term 4
    P1 = 111412.84  # longitude calculation term 1
    P2 = -93.5  # longitude calculation term 2
    P3 = 0.118  # longitude calculation term 3

    # Output storage
    __locations = {}
    __compass_directions = {}

    def __init__(self):
        ####################
        #GPS Initialization#
        ####################

        self.long_per_meter = 1
        self.lat_per_meter = 1

        # Start coordinates (should match the coordinates for the top left of the test area.) Default values
        self.starting_lat, self.starting_long = 50.937503679689584, -1.3978696903998111

        # Dimensions of real area in meters. Default Values
        self.r_length, self.r_width = 100, 100

        # Conversion variables
        self.set_conversion_vars()

        ######################
        #ARUCO Initialization#
        ######################
        # Video detection
        self.window_name = 'Detector'
        self.framerate = 30
        self.cam = 0  # 0 for built-in camera, 1 for external. default (0)

        # Color outline for marker detection
        self.selection_color = (125, 50, 125)

        # Marker dictionary
        self.aruco_dict = cv.aruco.custom_dictionary(4, 4)

    def set_coordinates(self, lat, long):
        # Coordinates should match top left of the test area
        self.starting_lat, self.starting_long = lat, long

    def set_real_dimensions(self, length, width):
        self.r_length, self.r_width = length, width

    def set_conversion_vars(self):
        # Latitude degree per meter (for conversion)
        self.lat_per_meter = 1 / (Detector.M1 + (Detector.M2 * math.cos(2 * math.radians(self.starting_lat))) +
                                  (Detector.M3 * math.cos(4 * math.radians(self.starting_lat))) +
                                  (Detector.M4 * math.cos(6 * math.radians(self.starting_lat))))

        # Longitude degree per meter (for conversion)
        self.long_per_meter = 1 / ((Detector.P1 * math.cos(math.radians(self.starting_lat))) +
                                   (Detector.P2 * math.cos(3 * math.radians(self.starting_lat))) +
                                   (Detector.P3 * math.cos(5 * math.radians(self.starting_lat))))

    def set_framerate(self, new_framerate):
        self.framerate = new_framerate

    def set_aruco_dict(self, new_aruco_dict):
        self.aruco_dict = new_aruco_dict

    def get_gprmc_frame(self, raw_speed: float, coordinates: (float, float), timestamp: datetime.datetime, course: float):
        # Sentence type
        sentence_type = '$GPRMC'

        # Frame structure; $GPRMC,time,status,latitude,n/s,longitude,e/w,speed,course,date,magnetic variation,mode*checksum
        frame_time = timestamp.strftime('%H%M%S.%f')[:-3]  # UTC time in hhmmss.sss
        status = 'A'  # Data validity; A=valid

        def get_lat(x):  # latitude in ddmm.mmmmm
            abs_lat = abs(x)
            lat_degree = int(abs_lat)
            lat_minute = (abs_lat - lat_degree) * 60
            n_s = 'N' if x > 0 else 'S'
            return f'{lat_degree:02}{lat_minute:08.5f},{n_s}'

        def get_long(x):  # longitude in dddmm.mmmmm
            abs_long = abs(x)
            long_degree = int(abs_long)
            long_minute = (abs_long - long_degree) * 60
            e_w = 'E' if x > 0 else 'W'
            return f'{long_degree:03}{long_minute:08.5f},{e_w}'

        speed = round(raw_speed * 1.94384449, 2)  # speed over ground in knots from m/s
        course = round(course, 1)  # course over ground in degrees
        date = timestamp.strftime('%d%m%y')  # date in ddmmyy
        mode = 'A'  # A(Autonomous), D(DGPS), E(DR); Only in newer Nmea versions

        def get_checksum(nmea_str):
            cs = 0
            if '$' in nmea_str:
                nmea_str = nmea_str.replace('$', '')
            for char in nmea_str:
                cs ^= ord(char)
            return f"{cs:02X}"  # Uppercase 2 digit hexadecimal

        sentence = (f'{sentence_type},{frame_time},{status},{get_lat(coordinates[0])},'
                    f'{get_long(coordinates[1])},{speed},{course},{date},,{mode}')
        checksum = get_checksum(sentence)
        end = f'\r\n'
        return f'{sentence}*{checksum}{end}'  # magnetic variation is ignored

    def get_gpgga_frame(self, coordinates:(float, float), timestamp:datetime.datetime):
        #Sentence type
        sentence_type = '$GPGGA'

        #Frame structure;
        #$GPGGA,time,latitude,n/s,longitude,e/w,quality,no_satellites,HDOP,altitude,alt_unit,undulation,und_unit,age,stn_ID*checksum
        frame_time = timestamp.strftime('%H%M%S.%f')[:-3] #UTC time in hhmmss.sss

        def get_lat(x): #latitude in ddmm.mmmmm
            abs_lat = abs(x)
            lat_degree = int(abs_lat)
            lat_minute = (abs_lat-lat_degree)*60
            n_s = 'N' if x > 0 else 'S'
            return f'{lat_degree:02}{lat_minute:08.5f},{n_s}'

        def get_long(x): #longitude in dddmm.mmmmm
            abs_long = abs(x)
            long_degree = int(abs_long)
            long_minute = (abs_long - long_degree) * 60
            e_w = 'E' if x > 0 else 'W'
            return f'{long_degree:02}{long_minute:08.5f},{e_w}'

        quality = '4' #Gps fix quality (x); 4 = RTK fixed ~2cm accuracy
        sat_no = '09' #Number of satellites used (xx); 9 = decent amount for ~2cm accuracy
        hdop = '0.5' #Horizontal dilution of precision (x.x); Quality of the horizontal position, based on satellite geometry, 0.5 = good
        alt = '50.9,M' #Altitude above mean sea level (x.x) and unit; placeholder,M = meters
        und = '46.9,M' #Relationship between the geoid and the WGS84 ellipsoid (x.x) and unit; placeholder,M = meters

        def get_checksum(nmea_str):
            cs = 0
            if '$' in nmea_str:
                nmea_str = nmea_str.replace('$','')
            for char in nmea_str:
                cs ^= ord(char)
            return f"{cs:02X}" #Uppercase 2 digit hexadecimal

        sentence = (f'{sentence_type},{frame_time},{get_lat(coordinates[0])},'
                    f'{get_long(coordinates[1])},{quality},{sat_no},{hdop},{alt},{und},')
        checksum = get_checksum(sentence)
        end = f'\r\n'
        return f'{sentence}*{checksum}{end}'  #Age and station id are ignored

    def get_nmea_frames(self, raw_speed: float, coordinates: (float, float), timestamp: datetime.datetime, course: float):
        rmc = self.get_gprmc_frame(raw_speed, coordinates, timestamp, course)
        gga = self.get_gpgga_frame(coordinates, timestamp)
        return f'{rmc}{gga}'

    def get_compass_direction(self, corners: list[np.array]) -> float:
        edge = corners[1] - corners[0]  # Top edge of the marker

        # Angle of that edge relative to image x-axis
        # Note: image y-axis points DOWN, so negate for standard math convention
        angle_rad = np.arctan2(-edge[1], edge[0])
        angle_deg = np.degrees(angle_rad) % 360

        return angle_deg

    def get_locations(self):
        return Detector.__locations

    def get_compass_directions(self):
        return Detector.__compass_directions

    # HELPERS
    def get_coordinates(self, rectangle: np.ndarray, frame, return_intermediate = False):
        def get_centre(area: np.ndarray):
            # Get centre of square area
            x = (area[0][0] + area[2][0]) / 2
            y = (area[0][1] + area[2][1]) / 2
            return x, y

        # Dimensions of fake area
        v_length = frame.shape[0]
        v_width = frame.shape[1]

        # Mapping
        length_per_px = self.r_length / v_length
        width_per_px = self.r_width / v_width
        lat_per_px = length_per_px * self.lat_per_meter
        long_per_px = width_per_px * self.long_per_meter

        x, y = get_centre(rectangle)

        if return_intermediate:
            return y * length_per_px, x * width_per_px

        lat = self.starting_lat - (y * lat_per_px)
        long = (x * long_per_px) + self.starting_long

        short_lat = round(lat, 11)
        short_long = round(long, 11)
        return short_lat, short_long

    def get_distance(self, point1, point2):
        return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

    def get_course(self, point1, point2):
        delta_y = point1[0] - point2[0]  # inversed because (0,0) is top left instead of bottom left
        delta_x = point2[1] - point1[1]
        if delta_x == 0 and delta_y == 0:  # Object is stationary
            return 0

        # Edge cases
        if delta_x == 0 and delta_y > 0:
            return 0
        elif delta_x == 0 and delta_y < 0:
            return 180
        elif delta_y == 0 and delta_x > 0:
            return 90
        elif delta_y == 0 and delta_x < 0:
            return 270

        slope = delta_y / delta_x
        angle_x = math.degrees(math.atan(slope))  # angle with the x-axis
        angle_y = 90 - angle_x  # angle with y-axis
        course = angle_y + 180 if delta_x < 0 else angle_y
        return course

    def scan(self):
        cap = cv.VideoCapture(self.cam)
        delay = 1/self.framerate

        while True:
            ret, frame = cap.read()
            if not ret:
                print('Failed to grab frame')
                break
            else:
                time.sleep(delay)
                ret2, frame2 = cap.read()
                current_time = datetime.datetime.now()  # time at second frame being taken
                if not ret2:
                    print('Failed to grab second frame')
                    break
                else:
                    frame_bw = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
                    frame2_bw = cv.cvtColor(frame2, cv.COLOR_BGR2GRAY)

                    # Aruco detection
                    corners, ids, rejected = cv.aruco.detectMarkers(frame_bw, self.aruco_dict)
                    corners2, ids2, rejected2 = cv.aruco.detectMarkers(frame2_bw, self.aruco_dict)

                    # Marker processing
                    if ids is not None and np.array_equal(np.unique(ids),
                                                          np.unique(ids2)):  # if same markers identified in both images
                        for i in range(len(ids)):
                            # Output
                            coordinates = self.get_coordinates(corners2[i][0], frame2_bw)
                            point_a = self.get_coordinates(corners[i][0], frame_bw)
                            point_b = coordinates
                            compass_direction = self.get_compass_direction(corners2[i][0])

                            # Extract Identified Marker Info
                            Detector.__locations[int(ids[i][0])] = self.get_nmea_frames(self.get_distance(point_a, point_b) / delay
                                                                        , coordinates
                                                                        , current_time,
                                                                        self.get_course(point_a, point_b))
                            Detector.__compass_directions[int(ids[i][0])] = compass_direction

                            print(
                                f"location -> {self.__locations[int(ids[i][0])]} direction -> {self.__compass_directions[int(ids[i][0])]}\n")

                        cv.aruco.drawDetectedMarkers(frame2, corners2, ids2)
                        cv.aruco.drawDetectedMarkers(frame, corners, ids)

                    else:  # if there are missing markers
                        pass

                    # cv.imshow(window, frame)
                    cv.imshow(self.window_name + '2', frame2)

            if cv.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv.destroyAllWindows()

if __name__ == '__main__':
    test = Detector()
    test.set_framerate(2)
    test.scan()