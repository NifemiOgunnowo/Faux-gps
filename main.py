import time
import cv2 as cv
from Camera import find_markers

window = 'Detection'
framerate = 60
delay = 1/framerate

def main():
    cap = cv.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            print('Failed to grab frame')
            break
        else:
            find_markers(frame)
            cv.imshow(window, frame)
            time.sleep(delay)

        if cv.waitKey(1) & 0xFF == ord('q'):
            break


    cap.release()
    cv.destroyAllWindows()

if __name__ == '__main__':
    main()