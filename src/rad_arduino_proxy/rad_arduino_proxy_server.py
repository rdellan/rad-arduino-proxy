from typing import Union, List, Dict, Any, cast

import math, time, copy, os, sys
import serial, threading, queue, traceback, string, select, errno
import pickle
import signal  # tools to handle asynchronous unix system signals with callback functions
from serial.tools import list_ports # list_ports.comports()
import numpy as np

import struct
from builtins import bytes
from cobs import cobs


class ArduinoProxy:
    """ TODO TODO TODO
    """

    def __init__(self, baud=38400) -> None:
        self.BAD_PACKET      = b'\x00' # code indicating arduino received corrupt packet
        self.IDENTITY        = b'\x01' # code used to request arduino identity
        self.corrupt_packets = 0  # Number of corrupt packets since initialization.
        self.num_attempts    = 1  # Number of connection attempts.
        self.arduino_name    = {} # Dictionary of arduino names indexed by port name.
        self.port_name       = {} # TODO Shouldn't need two dictionaries for this.
        self._input_buffer   = {} # Dictionary of input buffers indexed by port name.
        self.prox            = USBProxy(baud=baud)
        self.prox.start()
        time.sleep(1.0)
        self.port_names      = self.prox.get_ports()
        for port in self.port_names: # https://en.wikipedia.org/wiki/Cyclic_redundancy_check
            self.arduino_name[port]  = b''
            self._input_buffer[port] = b''
        all_arduinos_identified = False
        while ((not all_arduinos_identified) and (self.num_attempts < 20)):
            self.num_attempts += 1
            self._request_identity()
            time.sleep(0.5)
            packets = self._get_packets()
            print('packets =', packets)
            for port, data in packets:
                name = data[-1] # Hex byte that is ID of arduino
                print('port, data =', port, data)
                if port != "" and name != b'' and name != 0:
                    self.arduino_name[port] = name
                    self.port_name[name] = port
            all_arduinos_identified = not (b'' in self.arduino_name.values())
        print("identified", len(self.arduino_name), "arduinos")
        print(self.arduino_name)

    def shutdown(self):
        self.prox.shutdown()

    # request identity of arduinos not yet identified.
    def _request_identity(self):
        msg = []
        for port in self.arduino_name:
            if self.arduino_name[port] == b'':
                msg.append((port, self.pack(self.IDENTITY))) # request identity of arduino
        if msg != []:
            print("requesting identity")
            self.prox.send_chars(msg)
        
    # return list of arduino names.
    def get_arduino_list(self):
        return self.port_name.keys()

    # read prox queue, decode packets, and return packet content in a list with sender labled by port.
    # TODO need to ensure this procedure doesn't block TODO
    def _get_packets(self): # Returns -> List...
        chars_by_port = self.prox.get_chars()
        # print "chars_by_port =", chars_by_port
        for port in chars_by_port:
            self._input_buffer[port] += chars_by_port[port] 
            # ^^^ append chars to buffer (contains left-overs from last time)
        valid_packets = []
        for port in self._input_buffer: # traverse buffer and extract complete packets.
            packets = []
            while self._input_buffer[port].count(b'\x00') > 0:
                packet = self._input_buffer[port][:self._input_buffer[port].find(b'\x00')+1]
                packets.append(packet)
                self._input_buffer[port] = self._input_buffer[port][self._input_buffer[port].find(b'\x00')+1:] # remainder
            for p in packets:
                content = self.unpack(packet)
                if content is not None:
                    valid_packets.append((port, content))
        return valid_packets

    # same as _get_packets except maps port names to arduino names.
    def get_packets(self):
        return [(self.arduino_name[port], content) for port, content in self._get_packets()]

    # send packets: format: [(arduino_name, content),(arduino_name, content),...]
    def send_packets(self, packets):
        packed_packets = []
        for arduino, content in packets:
            if arduino in self.port_name:
                packed_packets.append((self.port_name[arduino], self.pack(content)))
        self.prox.send_chars(packed_packets)

    def get_checksum(self, data):
        return sum(data) % 65536

    def pack(self, data):
        len_byte = bytes([((len(data) + 3) % 256)])
        #print('pack(): data =', data)
        #print('pack(): len(data), len_byte =', len(data), len_byte)
        packed   = len_byte + data
        checksum_int = self.get_checksum(packed)
        checksum_bytes = struct.pack('>H', checksum_int) # encode checksum as two bytes
        packed  = packed + checksum_bytes
        #print('pack(): packed =', packed)
        encoded = cobs.encode(packed) # encode with cobs to remove packet delimiter from data
        packet  = encoded + b'\x00' # Add packet delimiter
        #print('pack(): packet =', packet)
        return packet

    def unpack(self, packet):
        packet = packet[:-1] # Strip off packet delimiter byte: \x00
        try:
            decoded = cobs.decode(packet)
        except:
            self.corrupt_packets += 1
            print("Corrupt packet (failed cobs decode):", packet)
            return None
        if (len(decoded) < 4):
            self.corrupt_packets += 1
            print("Corrupt packet (packet too short):", decoded)
            return None
        #print('unpack.decoded =', decoded)
        len_byte = bytes([decoded[0]])
        content  = bytes(decoded[1:-2])
        chksum   = bytes(decoded[-2:])
        # Validate length
        if bytes([len(decoded)%256])[0] != len_byte[0]:
            self.corrupt_packets += 1
            print("Corrupt packet (packet length doesnt match):", decoded)
            return None
        # Validate checksum
        checksum_int = self.get_checksum(len_byte + content)
        checksum_bytes = struct.pack('>H', checksum_int)
        if checksum_bytes != chksum:
            self.corrupt_packets += 1
            print("Corrupt packet (packet checksum doesnt match):", decoded)
            return None
        return content


class USBProxy:
    """ Creates simultanious connections to multiple USB devices that all have a particular
        pattern in their name. Manages threads and queues to provide a simple interface for
        listing connected devices, sending bytes to specific devices, and reading buffered bytes
        from said devices.
    """

    def __init__(self, pattern='ttyACM', baud=38400, verbose=False):
        global _shutdown
        _shutdown           = False     # TODO Can't this just be self.shutdown?
        self.verbose        = verbose
        self._input_queues  = {}
        self._output_queues = {}
        self.bufsize        = 65536
        self.threads        = []
        self.serials        = {}
        #serial_params = {'port':None,
        #                 'parity':serial.PARITY_EVEN,
        #                 'timeout':0,
        #                 'baudrate':baud,
        #                 'rtscts':False
        #                }
        serial_params = {'port':None,
                         'timeout':0.001953125,
                         'baudrate':baud,
                         'rtscts':False
                        }
        for s in list_ports.comports():
            serial_params['port'] = s[0]
            try:
                if s[0].count(pattern) > 0:
                    self.serials[s[0]] = serial.Serial(**serial_params)
            except:
                print('exception opening one of the usb ports:', s)
                raise SystemExit(1)

    def start(self):
        for serial in self.serials: # reader thread for each serial port
            self._input_queues[serial] = queue.Queue()
            self._output_queues[serial] = queue.Queue()
            self.threads.append(threading.Thread(target=self.reader,args=(serial, self._input_queues[serial])))
        self.threads.append(threading.Thread(target=self.writer)) # just one writer thread.
        for thread in self.threads:
            thread.daemon = True
            thread.start()

    def join(self):
        for thread in self.threads:
            while thread.isAlive():
                thread.join(0.1)

    def reader(self, serial, q):
        """ serial: serial.Serial
            q: queue.Queue
        """
        global _shutdown
        print('reader thread is alive.')
        try:
            while not _shutdown:
                data = self.serials[serial].read(size=1) # self.bufsize)
                #if data != b'':
                #    print('received data =', data)
                #print('data =', data)
                #if (not data is None) and (not data == b''):
                #    raise Exception('read returned EOF')
                q.put(data)
            if self.verbose:
                print('shutdown reader thread')
        except Exception as e:
            print('exception while reading serial data')
            print(e)
            os._exit(1)

    def writer(self):
        global _shutdown
        try:
            while not _shutdown:
                time.sleep(0.001953125) # ~512 Hz
                for port in self._output_queues:
                    q = self._output_queues[port]
                    chars = b''
                    try:
                        while (True):
                            ch = q.get(0)
                            chars += ch
                    except queue.Empty:
                        pass
                    if chars != b'':
                        #print('serials[',port,'].write(',chars,')')
                        self.serials[port].write(chars)
            if self.verbose:
                print('Shutdown writer thread')
        except Exception as e:
            print('exception while writing to serial')
            print(e)
            os._exit(1)
    
    def shutdown(self):
        global _shutdown
        _shutdown = True # Alter global variable to tell all threads to shutdown.
        self.join()

    def get_chars(self):
        """ Return read buffer content from each device: [('port','chars'),('port','chars')]
        """
        chars_by_port = {}
        for port in self._input_queues:
            q = self._input_queues[port]
            chars_by_port[port] = b''
            try:
                while (True):
                    ch = q.get(0)
                    chars_by_port[port] += ch
            except queue.Empty:
                pass
        return chars_by_port

    def send_chars(self, lst):
        """ Send chars to each device in lst. [('port','chars'),('port','chars')]
        """
        #print('send_chars =', lst)
        for port, chars in lst:
            self._output_queues[port].put(chars)
    
    def get_ports(self):
        """ Return list connected devices.
        """
        return self.serials.keys()


if __name__ == "__main__":
    # Function codes
    LASER_TILT_SERVO  = b'\x02' # set position/vel/accel for laser tilt servo
    ARDUINO_LED       = b'\x08' # set arduino debug led state: 0x00 = off, 0x01 = on
    # predefined commands
    down       = struct.pack('<cH', LASER_TILT_SERVO, 5000)
    level      = struct.pack('<cH', LASER_TILT_SERVO, 6000)
    up         = struct.pack('<cH', LASER_TILT_SERVO, 7000)
    led_off    = struct.pack('<cc', ARDUINO_LED, b'\x00')
    led_on     = struct.pack('<cc', ARDUINO_LED, b'\x01')
    # Create an arduino server server
    prox = ArduinoProxy()
    # send some packets to arduino with id 1
    prox.send_packets([(1, up)])
    prox.send_packets([(1, down)])
    # shutdown the arduino server
    prox.shutdown()






