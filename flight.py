from tello import Tello
import pygame
import time
import numpy as np

fly_flag = False    # 飛行中か否か
auto_flag = False   # Auto/Manual = True/False
interLoc = True     # Auto/Manual引き換え用のインターロック

#----------------------------------------------------------------
# ジョイスティックでTelloを制御
#
#   :param  drone (object):     Telloオブジェクト
#   :param  joy(object):        Joysticオブジェクト
#
def joy_control(drone, joy):
    global auto_flag, interLoc

    pygame.event.pump() 

    # Joystickの読み込み
    #   get_axisは　-1.0〜0.0〜+1.0 で変化するので100倍して±100にする
    #   プラスマイナスの方向が逆の場合は-100倍して反転させる
    rl = int( joy.get_axis(0) *  100 )      # 左右  右+, 左-
    fb = int( joy.get_axis(1) * -100 )      # 前後  前+, 後-

    ud = int( joy.get_axis(2) * 100 )       # 左側スロットル　手前+ 奥-
    t_rl1 = int( joy.get_axis(5) * 100 )    # 右スティックひねり　右+ 左-
    t_rl2 = int( joy.get_axis(6) * 100 )    # 左スロットの左右　　右+ 左-

    btn0 = joy.get_button(0)    # R1: 離陸
    btn1 = joy.get_button(1)    # L1: 写真撮影(動画？)
    btn2 = joy.get_button(2)    # R3: 着陸
    btn3 = joy.get_button(3)    # L3: Auto/Manual 切り替え
#   btn4 = joy.get_button(4)    # □
#   btn5 = joy.get_button(5)    # ×
#   btn6 = joy.get_button(6)    # 〇
#   btn7 = joy.get_button(7)    # △
#   btn8 = joy.get_button(8)    # R2
#   btn9 = joy.get_button(9)    # L2
#   btn10 = joy.get_button(10)  # SHARE
#   btn11 = joy.get_button(11)  # OPTIONS

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
        if fly_flag:
            fly_flag = True
            drone.takeoff()
    elif btn3 == 1:
        if not fly_flag:
            fly_flag = False
            drone.land()

    # Auto/Manual 切り替え
    if btn2 == 1:
        if interLoc:
            auto_flag = not bool(auto_flag)
            interLoc = False
    else:
        interLoc = True


#----------------------------------------------------------------
# メイン関数
#
def controlLoop():
    pygame.init()
    joy = pygame.joystick.Joystick(0)
    joy.init()

    drone = Tello(command_timeout=0.01)
    print('Let\'s Fly !!')

    try:
        while True:
            frame = drone.read()
            if frame is None or frame.size == 0:
                continue
            cv2.imshow('tello flight', frame)
            cv2.waitKey(1)

            joy_control(drone, joy, auto_flag)
            
            if auto_flag:
                # ここに自動制御が入る予定
                print('Auto!')
                pass
            else:
                print('Manual!')

            time.sleep(0.03)

    except Exception as ex:
        print('Exception>>', ex)
    finally:
        del drone

if __name__ == '__main__':
    controlLoop()
