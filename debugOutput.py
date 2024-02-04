import serial
import time
from threading import Thread, Event
from queue import Queue, Empty
from PySide6.QtCore import Signal, QObject


class SerialConnectionSettings:
    def __init__(self, portName):
        self.portName = portName
        self.baudrate = 1000000
        self.bytesize = serial.EIGHTBITS
        self.parity = serial.PARITY_NONE
        self.stopbits = serial.STOPBITS_ONE
        self.timeout = 0.5


class DebugOutput(QObject):
    dataAvailable = Signal(str)

    def __init__(self, settings: SerialConnectionSettings):
        super(DebugOutput, self).__init__()
        self.receiver = DebugOutputReceiver(settings)
        self.processor = DebugOutputDataProcessor(self.receiver.rxQueue)

        self.processor.dataAvailable.connect(self.dataAvailable)

    def start(self):
        if self.receiver.open_port():
            self.processor.start()
            self.receiver.start()
            return True
        else:
            return False

    def stop(self):
        self.receiver.stop()
        self.receiver.close_port()
        self.processor.stop()

    def getPortName(self):
        return self.receiver.settings.portName

    def isActive(self):
        return self.receiver.isReceiving()


class DebugOutputReceiver:
    def __init__(self, settings: SerialConnectionSettings):
        self.terminateEvent = Event()
        self.rxQueue = Queue()
        self.thread = None
        self.serialPort = None
        self.settings = settings

    def open_port(self) -> bool:
        if self.serialPort:
            self.serialPort.close()

        self.serialPort = serial.Serial()
        self.serialPort.port = self.settings.portName
        self.serialPort.baudrate = self.settings.baudrate
        self.serialPort.bytesize = self.settings.bytesize
        self.serialPort.parity = self.settings.parity
        self.serialPort.stopbits = self.settings.stopbits
        self.serialPort.timeout = self.settings.timeout

        try:
            self.serialPort.open()
        except serial.SerialException:
            # print("failed to open comport " + self.serialPort.port)
            return False
        return True

    def close_port(self):
        if self.serialPort:
            self.serialPort.close()
            self.serialPort = None

    def start(self):
        if self.thread is None:
            self.thread = Thread(target=self.receiveData, args=(self.rxQueue, self.terminateEvent))
            self.thread.start()
            print("started rx")

    def stop(self):
        if self.thread:
            self.terminateEvent.set()
            self.thread.join()
            self.thread = None
            self.terminateEvent.clear()
            print("stopped rx")

    def isReceiving(self):
        return self.thread and self.thread.is_alive()

    def receiveData(self, queue, terminateEvent):
        # try:
        #     self.serialPort.open()
        # except serial.SerialException:
        #     print("failed to open comport " + self.serialPort.port)
        #     return  # todo cleanup thread

        self.serialPort.reset_input_buffer()

        while not terminateEvent.is_set():
            received_data = self.serialPort.read(1)
            if len(received_data) > 0:
                # print(receivedData)
                queue.put(received_data)

        # self.serialPort.close()
        self.terminateEvent.clear()


class DebugOutputDataProcessor(QObject):
    dataAvailable = Signal(str)

    def __init__(self, rawDataQueue):
        super(DebugOutputDataProcessor, self).__init__()
        self.lastEmitTimestamp = self.getTimestamp()
        self.terminateEvent = Event()
        self.rawDataQueue = rawDataQueue
        self.thread = None

    def start(self):
        if self.thread is None:
            self.thread = Thread(target=self.processData, args=(self.rawDataQueue, self.terminateEvent))
            self.thread.start()
            print("started processor")

    def stop(self):
        if self.thread and self.thread.is_alive():
            self.terminateEvent.set()
            self.thread.join()
            self.thread = None
            self.terminateEvent.clear()
            print("stopped processor")

    def getTimestamp(self):
        return int(round(time.time() * 1000))

    def timeDiffSinceLastEmit(self):
        return self.getTimestamp() - self.lastEmitTimestamp

    def processData(self, queue, terminateEvent):
        data = bytearray()

        while not terminateEvent.is_set():
            try:
                rx_bytes = queue.get(timeout=0.2)
                data.extend(rx_bytes)
                # queue.task_done()
            except Empty:
                pass
            finally:
                if len(data) > 0:
                    try:
                        # TODO process data
                        self.dataAvailable.emit(data.decode("ascii"))
                    except:
                        pass
                    data = bytearray()
