#
#
#
from tello import Tello
import pygame
import datetime
import time
import numpy as np
import cv2

fly_flag = False        # 飛行中/着陸中 = True/False
flyInterLoc = True      # 飛行中/着陸中 切り換え用のインターロック
emerInterLoc = True     # 緊急着陸 インターロック

auto_flag = False       # Auto/Manual = True/False
autoInterLoc = True     # Auto/Manual 切り換え用のインターロック

camera_flag = False     # 動画/静止画 = True/False
cameraInterLoc = True   # 動画/静止画 切り替え用のインターロック

photo_flag = 0          # 撮影せず/写真撮影/動画開始/撮影中/動画終了 = 0/1/2/3/4
photoInterLoc = True    # インターロック

frame_rate = 24.0

#----------------------------------------------------------------
# 現在の日時を返す
def getDateTime():
    t_delta = datetime.timedelta(hours=9)
    JST = datetime.timezone(t_delta, 'JST')
    now = datetime.datetime.now(JST)
    return now.strftime('%Y_%m_%d_%H_%M_%S')

#----------------------------------------------------------------
# ジョイスティックでTelloを制御
#
#   :param  drone (object):     Telloオブジェクト
#   :param  joy(object):        Joysticオブジェクト
#
def joy_control(drone, joy):
    global fly_flag, flyInterLoc, emerInterLoc
    global auto_flag, autoInterLoc
    global camera_flag, cameraInterLoc
    global photo_flag, photoInterLoc

    pygame.event.pump() 

    # Joystickの読み込み
    #   get_axisは　-1.0〜0.0〜+1.0 で変化するので100倍して±100にする
    #   プラスマイナスの方向が逆の場合は-100倍して反転させる
    rl = int( joy.get_axis(0) *  100 )      # 左右  右+, 左-
    fb = int( joy.get_axis(1) * -100 )      # 前後  前+, 後-
    ud = int( joy.get_axis(2) * -100 )      # 左側スロットル　手前- 奥+
    t_rl1 = int( joy.get_axis(5) * 100 )    # 右スティックひねり　右+ 左-
    t_rl2 = int( joy.get_axis(6) * 100 )    # 左スロットの左右　　右+ 左-

    btn0 = joy.get_button(0)    # R1: 写真撮影/動画撮影（開始/終了）
    btn1 = joy.get_button(1)    # L1: 離陸/着陸
#    btn2 = joy.get_button(2)    # R3:
    btn3 = joy.get_button(3)    # L3: 強制着陸モード
#   btn4 = joy.get_button(4)    # □
#   btn5 = joy.get_button(5)    # ×
#   btn6 = joy.get_button(6)    # 〇
#   btn7 = joy.get_button(7)    # △
#   btn8 = joy.get_button(8)    # R2
#   btn9 = joy.get_button(9)    # L2
    btn10 = joy.get_button(10)  # SHARE: Auto/Manual 切り替え
    btn11 = joy.get_button(11)  # OPTIONS: 動画/静止画 切り替え

    x, y = joy.get_hat(0)   # x: 右+ 左-
                            # y: 上+ 下-
    #　ドローン制御
    if not auto_flag:
        if x == 0 and y == 1:
            drone.flip('f')
        elif x == 0 and y == -1:
            drone.flip('b')
        elif x == 1 and y == 0:
            drone.flip('r')
        elif x == -1 and y == 0:
            drone.flip('l')
        else:
            drone.send_command( 'rc %s %s %s %s'%(rl, fb, ud, t_rl2) )

    # 離陸/着陸
    if btn1 == 1 :
        if flyInterLoc:
            flyInterLoc = False
            if not fly_flag:
                fly_flag = True
                drone.takeoff()
            else:
                fly_flag = False
                drone.land()
    else:
        flyInterLoc = True

    # 強制着陸
    if btn3 == 1:
        if emerInterLoc:
            emerInterLoc = False
            fly_flag = False
            drone.land()
    else:
        emerInterLoc = True

    # 動画/静止画 切り替え
    if btn11 == 1:
        if cameraInterLoc:
            cameraInterLoc = False
            camera_flag = not bool(camera_flag)
    else:
      cameraInterLoc = True

    # 撮影
    if btn0 == 1:
        if photoInterLoc:
            photoInterLoc = False
            if camera_flag:
                if photo_flag == 0:
                    photo_flag = 2
                else:
                    photo_flag = 4
            else:
                photo_flag = 1
    else:
        photoInterLoc = True

    # Auto/Manual 切り替え
    if btn10 == 1:
        if autoInterLoc:
            autoInterLoc = False
            auto_flag = not bool(auto_flag)
    else:
        autoInterLoc = True


#----------------------------------------------------------------
# メイン関数
#
def controlLoop():
    global photo_flag
    pygame.init()
    joy = pygame.joystick.Joystick(0)
    joy.init()
    l_h, l_b = '0', '0'

    drone = Tello(command_timeout=0.01)
    print('Let\'s Fly !!')

    try:
        while True:
            joy_control(drone, joy)

            # 960x720x3
            frame = drone.read()
            if frame is None or frame.size == 0:
                continue
            frame = cv2.resize(frame, dsize=(800, 600))

            if photo_flag == 1:
                # 写真撮影
                fileName = getDateTime()
                cv2.imwrite(f'{fileName}.jpg', frame)
                photo_flag = 0
            elif photo_flag == 2:
                # 動画開始
                fmt = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
                fileName = getDateTime()
                writer = cv2.VideoWriter(f'{fileName}.mp4', fmt, frame_rate, (800, 600))
                photo_flag = 3
            elif photo_flag == 3:
                # 動画撮影中
                writer.write(frame)
                pass
            elif photo_flag == 4:
                # 動画終了
                writer.release()
                photo_flag = 0

            # 高度と残りバッテリー
            msg_h = drone.get_height()
            msg_b = drone.get_battery()
            if msg_h is not None:
                l_h = str(msg_h)
            if msg_b is not None:
                l_b = str(msg_b)
            cv2.putText(frame,
                        text='Height : '+l_h,
                        org=(10, 20),
                        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale=0.5,
                        color=(0, 255, 255),
                        thickness=2)
            cv2.putText(frame,
                        text='Battery: '+l_b,
                        org=(10, 40),
                        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale=0.5,
                        color=(0, 255, 255),
                        thickness=2)

            cameraType = 'Photos'
            if camera_flag:
                cameraType = 'Movies'
            cv2.putText(frame,
                        text=cameraType,
                        org=(670, 590),
                        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale=1.0,
                        color=(0, 255, 255),
                        thickness=2)

            if photo_flag == 3:
                cv2.putText(frame,
                            text='*REC',
                            org=(670, 590),
                            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                            fontScale=1.0,
                            color=(0, 0, 255),
                            thickness=2)

            ctrlType = 'Manual'
            if auto_flag:
                ctrlType = 'Auto'
                # ここに自動制御が入る予定
            cv2.putText(frame,
                        text=ctrlType,
                        org=(10, 590),
                        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale=1.0,
                        color=(0, 255, 255),
                        thickness=2)

            cv2.imshow('tello flight', frame)
            cv2.waitKey(1)
            time.sleep(0.03)

    except Exception as ex:
        print('Exception fly>>', ex)
    finally:
        del drone

if __name__ == '__main__':
    controlLoop()
