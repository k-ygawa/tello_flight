from tello import Tello
import cv2

def main():
    drone = Tello(command_timeout=0.01)

    try:
        while True:
            frame = drone.read()
            if frame is None or frame.size == 0:
                continue
            cv2.imshow('tello camera', frame)
            cv2.waitKey(1)
    except Exception as ex:
        print(ex)
    finally:
        del drone

if __name__ == '__main__':
    main()
