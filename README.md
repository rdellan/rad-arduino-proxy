# rad-arduino-proxy
Reinvented rosserial for minimalism and finer-grained control

This started as a simple string-based method of communicating with a few arduinos.
It became more efficient and fault-tolerant over a few iterations.
I originally wrote this because I ran into problems with the ROS 1 rosserial libraries. 
I'm maintaining it because the ROS 2 equivalent of rosserial is now
too large to fit on smaller micro-controllers, and because I prefer a custom protocol that 
minimizes control latency.

Features:
* Can be easily used independent of Robot Operating System (ROS).
* Fits on smaller micro-controllers.
* Small protocol overhead (4-bytes).
* Detects corrupt packets using one length byte and a 16-bit checksum.
* Recovers/resyncs quickly after corrupt packets using explicit EOF byte.
* Uses Consistent Overhead Byte Stuffing (COBS) encoding to avoid overloading of EOF byte.
* Handles multiple Arduinos with one process.
* Identifies Arduinos independent of their assigned USB port.

## Dependencies:

### pyserial

Best to install from source

    wget https://github.com/pyserial/pyserial/archive/v3.4.tar.gz
    tar -xvf v3.4.tar.gz
    cd pyserial-3.4
    python3 -m pip install .

### cobs-python

https://pypi.org/project/cobs/

    git clone https://github.com/cmcqueen/cobs-python.git
    cd cobs-python
    python3 -m pip install .

### arduino packet-serial library

https://github.com/bakercp/PacketSerial

https://www.arduino.cc/reference/en/libraries/packetserial/

Install PacketSerial via Arduino IDE library manager.


### TODO:

Rewrite this documentation to follow the correct format.

Rewrite documentation of the code to work with Sphinx.

The arduino example code should be turned into an arduino library that can be easily imported to simplify things.
