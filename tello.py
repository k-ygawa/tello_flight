import socket
import threading
import time
import cv2

class Tello:
    #--------------------------------------------------------------------------------------------
    #  初期設定
    #
    #   :param local_ip (str):              バインドする(UDPサーバにする)ローカルのIPアドレス
    #   :param local_port (int):            バインドするローカルのポート番号
    #   :param command_timeout (int|float): コマンドの応答を待つ時間。デフォルトは0.3秒．
    #   :param tello_ip (str):              TelloのIPアドレス。デフォルトは192.168.10.1
    #   :param tello_port (int):            Telloのポート。デフォルトは8889
    #   :param debug_mode(bool):            Telloに送ったコマンドを表示するか否か。デフォルトはFalse
    def __init__(self,
                 local_ip='',
                 local_port=8889,
                 command_timeout=0.3,
                 tello_ip='192.168.10.1',
                 tello_port=8889,
                 debug_mode=False):
        self.debug_mode = debug_mode
        self.abort_flag = False
        self.command_timeout = command_timeout
        self.response = None

        self.frame = None

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.tello_address = (tello_ip, tello_port)

        self.last_height = 0
        self.socket.bind((local_ip, local_port))

        self.receive_thread = threading.Thread(target=self._receive_thread)
        self.receive_thread.daemon = True
        self.receive_thread.start()

        self.socket.sendto(b'command', self.tello_address)
        print('sent: command')
        self.socket.sendto(b'streamon', self.tello_address)
        print('sent: streamon')

        self.VS_UDP_IP = '0.0.0.0'
        self.VS_UDP_PORT = 11111
        self.udp_video_address = 'udp://@' + self.VS_UDP_IP + ':' + str(self.VS_UDP_PORT)
        self.cap = cv2.VideoCapture(self.udp_video_address)

        self.receive_video_thread = threading.Thread(target=self._receive_video_thread)
        self.receive_video_thread.daemon = True
        self.receive_video_thread.start()


    #==========================================
    #  デストラクタ
    def __del__(self):
        self.socket.close()
        self.cap.release()

   #==========================================
    #  Telloからの応答を取得
    def _receive_thread(self):
        while True:
            try:
                self.response, ip = self.socket.recvfrom(3000)
            except socket.error as exc:
                print("Caught exception socket.error : %s" % exc)

    #==========================================
    #  Telloからのストリーム動画を取得
    def _receive_video_thread(self):
        while True:
            ret, self.frame = self.cap.read()


    #------------------------------------------
    #  カメラで受信した最新の画像を返す
    #
    #  video_freeze(True)の場合、ビデオ出力を一時停止（最後の画像を送信）
    def read(self):
        return self.frame


    #------------------------------------------
    #  Telloへコマンド送信
    def send_command(self, command):
        if self.debug_mode:
            print(">> send cmd: {}".format(command))

        self.abort_flag = False
        timer = threading.Timer(self.command_timeout, self.set_abort_flag)

        self.socket.sendto(command.encode('utf-8'), self.tello_address)

        # self.command_timeout内に応答がなければ無視
        timer.start()
        while self.response is None:
            if self.abort_flag is True:
                break
        timer.cancel()
        response = None
        if self.response is not None:
            response = self.response.decode('utf-8')

        self.response = None
        return response


    #------------------------------------------
    #  強制終了
    def set_abort_flag(self):
        self.abort_flag = True


    #------------------------------------------
    #  スピードを設定
    def set_speed(self, speed):
        speed = int(round(float(speed) * 27.7778))
        return self.send_command('speed %s' % speed)


    #------------------------------------------
    #  応答を取得
    def get_response(self):
        return self.response

    #------------------------------------------
    #  高度を取得
    def get_height(self):
        height = self.send_command('height?')
        height = str(height)
        height = filter(str.isdigit, height)
        try:
            height = int(height)
            self.last_height = height
        except:
            height = self.last_height
        return height

    #------------------------------------------
    #  バッテリー残量を取得
    def get_battery(self):
        battery = self.send_command('battery?')
        try:
            battery = int(battery)
        except:
            battery = None
        return battery

    #------------------------------------------
    #  飛行時間を取得
    def get_flight_time(self):
        flight_time = self.send_command('time?')
        try:
            flight_time = int(flight_time)
        except:
            flight_time = None
        return flight_time

    #------------------------------------------
    #  速度を取得
    #
    #  Telloインスタンス生成時に
    def get_speed(self):
        speed = self.send_command('speed?')
        try:
            speed = round((float(speed) / 27.7778), 1)
        except:
            speed = None
        return speed


    #------------------------------------------
    #  離陸
    def takeoff(self):
        return self.send_command('takeoff')

    #------------------------------------------
    #  着陸
    def land(self):
        return self.send_command('land')

    #------------------------------------------
    #  フリップ
    #
    #  :param direction (str):  フリップする方向（f, b, l, r）
    def flip(self, direction):
        return self.send_command('flip %s' % direction)
