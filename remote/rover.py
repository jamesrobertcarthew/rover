import serial
import curses
from time import sleep
from xyzplotlyhandler import XYZPlotlyHandler


def float2string(i):
    return '{:+06.2f}'.format(i)


class Rover(object):
    def __init__(self, address):
        self.address = address
        self.ir = {'FRONT': 0, 'REAR': 0}
        self.accel = {'X': 0, 'Y': 0, 'Z': 0, 'BIASX': 0, 'BIASY': 0, 'BIASZ': 0}
        self.gyro = {'X': 0, 'Y': 0, 'Z': 0, 'BIASX': 0, 'BIASY': 0, 'BIASZ': 0}
        self.compass = {'X': 0, 'Y': 0, 'Z': 0, 'BIASX': 0, 'BIASY': 0, 'BIASZ': 0}
        self.pose = {'X': 0, 'Y': 0, 'Z': 0}
        self.connected = False
        self.accel_plot = None
        self.gyro_plot = None
        self.compass_plot = None
        self.message_length = 0  # Set by Arduino upon connect
        self.message_number = 0

    def plot_accel(self):
        if self.accel_plot is None:
            self.accel_plot = XYZPlotlyHandler("Rover1", "Accelerometer Data", 0, "G-FORCES", 1.5)
        else:
            self.accel_plot.update(self.accel)

    def plot_compass(self):
        if self.compass_plot is None:
            self.compass_plot = XYZPlotlyHandler("Rover1", "Compass Data", 3, "DEGREES", 180)
        else:
            self.compass_plot.update(self.compass)

    def plot_gyro(self):
        if self.gyro_plot is None:
            self.gyro_plot = XYZPlotlyHandler("Rover1", "Gyro Data", 7, "DEGREES/SEC", 180)
        else:
            self.gyro_plot.update(self.gyro)

    def connect(self):
        self.serial = serial.Serial(self.address, 38400)
        MOTD = ' '
        while True:
            MOTD = self.serial.readline()
            if 'Hello, World!' in MOTD:
                self.connected = True
                break
        # self.message_length = int(self.serial.readline().rstrip())
        # self.accel['BIASX'] = float(self.serial.readline().rstrip())
        # self.accel['BIASY'] = float(self.serial.readline().rstrip())
        # self.accel['BIASZ'] = float(self.serial.readline().rstrip())
        # self.gyro['BIASX'] = float(self.serial.readline().rstrip())
        # self.gyro['BIASY'] = float(self.serial.readline().rstrip())
        # self.gyro['BIASZ'] = float(self.serial.readline().rstrip())

    def write2motors(self, m1, m2):
        motor1 = m1
        motor2 = m2
        dir1 = 0x00     # #define DIRF            0x00        // Forward
        dir2 = 0x00     # #define DIRR            0x01        // Reversion
        if m1 < 0:
            dir1 = 0x01
            motor1 = motor1*(0-1)
        if m2 < 0:
            dir2 = 0x01
            motor2 = motor2*(0-1)
        if m1 > 100:
            motor1 = 20
        if m2 > 100:
            motor2 = 20
        msg = bytearray('m')
        msg.append(chr(motor1))
        msg.append(dir1)
        msg.append(chr(motor2))
        msg.append(dir2)
        self.write(msg)

    def write(self, msg):
        # +--------+----------------+---------+------>
        # | Header | Message Length | Data ID | Data
        # +--------+----------------+---------+------>
        msg_length = chr(len(msg))
        s = bytearray('~')
        s.append(msg_length)
        s = s + msg
        for c in s:
            self.serial.write(chr(c))

    def read_serial_as_float(self):
        return float(self.serial.readline().rstrip())

    def read(self):
        self.write(bytearray('r'))
        # Accelerometer
        self.accel['X'] = self.read_serial_as_float()
        self.accel['Y'] = self.read_serial_as_float()
        self.accel['Z'] = self.read_serial_as_float()
        # Gyro
        self.gyro['X'] = self.read_serial_as_float()
        self.gyro['Y'] = self.read_serial_as_float()
        self.gyro['Z'] = self.read_serial_as_float()
        # Compass
        self.compass['X'] = self.read_serial_as_float()
        self.compass['Y'] = self.read_serial_as_float()
        self.compass['Z'] = self.read_serial_as_float()
        # IR
        self.ir['FRONT'] = self.read_serial_as_float()
        self.ir['REAR'] = self.read_serial_as_float()

    def log2cli(self):
        print('Accelerometer')
        print(self.accel['X'])
        print(self.accel['Y'])
        print(self.accel['Z'])
        print('Gyro')
        print(self.gyro['X'])
        print(self.gyro['Y'])
        print(self.gyro['Z'])
        print('Compass')
        print(self.compass['X'])
        print(self.compass['Y'])
        print(self.compass['Z'])
        print('IR')
        print(self.ir['FRONT'])
        print(self.ir['REAR'])
        print(self.ir['REAR'] + self.ir['REAR'])

    def log2curses(self, screen, y_offset=3):
        dims = screen.getmaxyx()
        clear = [' '] * (dims[1] - 1)
        delimiter = ['-'] * len(clear)
        clear = ''.join(clear)
        delimiter = ''.join(delimiter)
        for i in range(0, 8):
            screen.addstr(y_offset + i, 1, clear)
        # ACCEL
        screen.addstr(y_offset + 0,        1,                       'Accelerometer', curses.A_BOLD)
        screen.addstr(y_offset + 1,        1,                       'X:', curses.A_DIM)
        screen.addstr(y_offset + 1,        dims[1]/3,               'Y:', curses.A_DIM)
        screen.addstr(y_offset + 1,        2*dims[1]/3,             'Z:', curses.A_DIM)
        screen.addstr(y_offset + 1,        4,                       float2string(self.accel['X']))
        screen.addstr(y_offset + 1,        (3 + dims[1]/3),         float2string(self.accel['Y']))
        screen.addstr(y_offset + 1,        (3 + 2*dims[1]/3),       float2string(self.accel['Z']))
        # GYRO
        screen.addstr(y_offset + 2,        1,                       'Gyroscope', curses.A_BOLD)
        screen.addstr(y_offset + 3,        1,                       'X:', curses.A_DIM)
        screen.addstr(y_offset + 3,        dims[1]/3,               'Y:', curses.A_DIM)
        screen.addstr(y_offset + 3,        2*dims[1]/3,             'Z:', curses.A_DIM)
        screen.addstr(y_offset + 3,        4,                       float2string(self.gyro['X']))
        screen.addstr(y_offset + 3,        (3 + dims[1]/3),         float2string(self.gyro['Y']))
        screen.addstr(y_offset + 3,        (3 + 2*dims[1]/3),       float2string(self.gyro['Z']))
        # COMPASS
        screen.addstr(y_offset + 4,        1,                       'Compass', curses.A_BOLD)
        screen.addstr(y_offset + 5,        1,                       'X:', curses.A_DIM)
        screen.addstr(y_offset + 5,        dims[1]/3,               'Y:', curses.A_DIM)
        screen.addstr(y_offset + 5,        2*dims[1]/3,             'Z:', curses.A_DIM)
        screen.addstr(y_offset + 5,        4,                       float2string(self.compass['X']))
        screen.addstr(y_offset + 5,        (3 + dims[1]/3),         float2string(self.compass['Y']))
        screen.addstr(y_offset + 5,        (3 + 2*dims[1]/3),       float2string(self.compass['Z']))
        # IR
        screen.addstr(y_offset + 6,        1,                        'IR', curses.A_BOLD)
        screen.addstr(y_offset + 7,        1,                        'F: ', curses.A_DIM)
        screen.addstr(y_offset + 7,        dims[1]/3,                'R: ', curses.A_DIM)
        screen.addstr(y_offset + 7,        4,                        float2string(self.ir['FRONT']))
        screen.addstr(y_offset + 7,        (3 + dims[1]/3),          float2string(self.ir['REAR']))
        # END OF OUPUT
        screen.addstr(y_offset + 8, 1, delimiter)
        screen.refresh()
        return (y_offset + 9)
