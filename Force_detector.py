import cv2
import cv2.aruco as aruco

# List of all known predefined dictionary constants
all_dicts = [
    aruco.DICT_4X4_50, aruco.DICT_4X4_100, aruco.DICT_4X4_250, aruco.DICT_4X4_1000,
    aruco.DICT_5X5_50, aruco.DICT_5X5_100, aruco.DICT_5X5_250, aruco.DICT_5X5_1000,
    aruco.DICT_6X6_50, aruco.DICT_6X6_100, aruco.DICT_6X6_250, aruco.DICT_6X6_1000,
    aruco.DICT_7X7_50, aruco.DICT_7X7_100, aruco.DICT_7X7_250, aruco.DICT_7X7_1000,
    aruco.DICT_ARUCO_ORIGINAL
]

image = cv2.imread("IMGx4.jpg")
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

found = False

for dict_id in all_dicts:
    aruco_dict = aruco.getPredefinedDictionary(dict_id)
    corners, ids, rejected = aruco.detectMarkers(gray,aruco_dict)

    if ids is not None and len(ids) > 0:
        print(f"Marker detected! Dictionary: {dict_id}, ID: {ids[0][0]}")
        aruco.drawDetectedMarkers(image, corners, ids)
        found = True
        break

if not found:
    print("No known dictionary matched.")

cv2.imshow("Marker Detection", image)
cv2.waitKey(0)
cv2.destroyAllWindows()
