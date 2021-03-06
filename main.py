from bluepy.btle import Scanner, DefaultDelegate, Peripheral, BTLEManagementError, BTLEDisconnectError
import struct
import time
import threading


# thread to read weight from the scale
class ReadWeightThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.name = READ_THREAD_NAME

    def run(self):
        try:

            weight = self.read_scale()

            # if we successfully got the weight, set the last_measurement time
            if weight:
                global last_measurement
                last_measurement = time.time()

                # do something with the measurement here

        except Exception as e:
            print(e)

    # connect to the scale and return the weight once the measurement is completed
    def read_scale(self):

        # connect to the scale
        p = Peripheral(SCALE_ADDRESS, 'public')

        # create the delegate
        delegate = BLEDelegate()
        p.setDelegate(delegate)

        # enable notifications
        p.writeCharacteristic(NOTIFY_HANDLE, NOTIFY_VALUE, withResponse=True)

        # start the weight notifications
        p.writeCharacteristic(MEASUREMENT_HANDLE, BEGIN_MEASUREMENT_VALUE)

        start_time = time.time()

        # wait until measurement is done;
        while not delegate.measurement_done:

            # if it takes longer than 60 seconds then something is probably wrong so stop
            if (time.time() - start_time) > 60:
                break

            if p.waitForNotifications(1.0):
                continue

        # if we successfully took a measurement
        if delegate.measurement_done:
            print('measurement done! weight is {} kg, {:.1f} lbs'.format(delegate.weight, delegate.weight * 2.20462))

        # disconnect from the scale
        p.disconnect()

        return delegate.weight


def is_thread_active(thread_name):
    for thread in threading.enumerate():
        if thread_name == thread.name:
            return True


# delegate class used with bluepy
# combines the scan and notification delegates into a single class
class BLEDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)
        self.weight = None
        self.measurement_done = False

    # function that will be called when new devices are discovered
    def handleDiscovery(self, dev, is_new_dev, is_new_data):

        # if the newly discovered device is the scale
        # dev.addr is lowercase so make sure the SCALE_ADDRESS is as well
        if is_new_dev and dev.addr == SCALE_ADDRESS.lower():

            # make sure the read weight thread isn't already running
            # the MEASUREMENT_COOLDOWN should prevent this from happening but just to be sure...
            if is_thread_active(READ_THREAD_NAME):
                print('thread already started!')
                return

            if not last_measurement or time.time() - last_measurement > MEASUREMENT_COOLDOWN:

                print('starting read weight thread')
                read_weight_thread = ReadWeightThread()
                read_weight_thread.setDaemon(True)
                read_weight_thread.start()

    # function that will be called when notifications are received
    def handleNotification(self, handle, data):

        # the weight notification starts with \x10
        if data[0] == 16:

            # convert the 4th and 5th bytes to decimal and then divide by 100
            #  to get the weight in kilograms
            weight = int(data[3:5].hex(), 16) / 100
            print('weight is {} kg'.format(weight))

            # once the measurement is done byte #6 should be set to 1
            # this will coincide with the weight on the scale flashing
            if data[5] == 1:
                print('measurement done, final weight is {}'.format(weight))
                self.measurement_done = True
                self.weight = weight


# the mac address of the scale
SCALE_ADDRESS = '04:ac:44:0a:14:be'

# the bluetooth handle used to enable notifications
NOTIFY_HANDLE = 0x0016

# the value that needs to be written to the above handle to enable notifications
NOTIFY_VALUE = struct.pack('<BB', 0x01, 0x00)

# the bluetooth handle used to start weight notifications
MEASUREMENT_HANDLE = 0x0013

# the value that needs to be written to the above handle to start weight notifications
BEGIN_MEASUREMENT_VALUE = struct.pack('<BBBBBBBB', 0x20, 0x08, 0x15, 0xda, 0xb9, 0xe8, 0x25, 0xdd)

# the scale will still be discoverable and connectable for a short time after the display turns off
# to prevent repeated connections, set a cooldown between measurements
MEASUREMENT_COOLDOWN = 900

READ_THREAD_NAME = 'Read Weight Thread'

# global var to track when we last took a measurement
last_measurement = None

while True:
    try:
        scanner = Scanner().withDelegate(BLEDelegate())

        # make sure the read thread isn't active before starting another scan
        if not is_thread_active(READ_THREAD_NAME):
            scanner.scan(MEASUREMENT_COOLDOWN, passive=True)
        else:
            print('read thread active, not starting new scan, sleeping for 10 seconds')
            time.sleep(10)

    except BTLEDisconnectError as e:
        print('device disconnected? {}'.format(e))
        time.sleep(1)

    except BTLEManagementError as e:
        print('something wrong with bluetooth device? {}'.format(e))
        time.sleep(1)

    except KeyboardInterrupt:
        break