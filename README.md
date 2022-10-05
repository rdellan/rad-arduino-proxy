# rad-arduino-proxy
Reinvented rosserial for minimalism and finer-grained control

This started as a simple string-based method of communicating with a few arduinos.
It became more efficient and fault-tolerant over a few iterations.
I originally wrote this because I ran into problems with the ROS 1 rosserial libraries. 
I'm maintaining it because the ROS 2 equivalent of rosserial is now
too large to fit on smaller micro-controllers, and because I prefer a custom protocol that 
minimizes control latency.

Useful features of this protocol:
* Compact library that easily fits on smaller micro-controllers.
* Small protocol overhead (4-bytes).
* Detects corrupt packets using one length byte and a 16-bit checksum.
* Recovers/resyncs quickly after corrupt packets thanks to explicit EOF byte.
* Uses Consistent Overhead Byte Stuffing (COBS) encoding to avoid overloading of EOF byte.
* Handles multiple Arduinos with one process.
* Identifies Arduinos independent of their assigned USB port.

References:

https://en.wikipedia.org/wiki/Consistent_Overhead_Byte_Stuffing

https://www.arduino.cc/reference/en/libraries/packetserial/

Dependencies:

https://pypi.org/project/cobs/

https://github.com/bakercp/PacketSerial

TODO:

This needs to be turned into a python package that can be installed.

Python packages shouldn't be installed using sudo. Fix that.

The arduino example code should be turned into an arduino library that can be easily imported to simplify things.
