// ------------------ Packet Management ----------------
#include <PacketSerial.h>
PacketSerial_<COBS, 0, 128> myPacketSerial; // Use Consistent Overhead Byte Stuffing (COBS) encoding.
// ^^ PacketMarker defaults to 0 and BufferSize defaults to 256 bytes.
// https://github.com/bakercp/PacketSerial/blob/master/docs/GETTING_STARTED.md
unsigned long now = millis();
unsigned long heartbeat = millis();
const int heartbeat_timeout = 120; // 120 miliseconds until PC is considered dead.
boolean comm_timeout = false;   // true if a packet hasn't been received in heartbeat_timeout millis
boolean corrupt_packet = false; // true if most recent packet received was corrupt
uint8_t response[64]; // Response buffer up to 128 bytes.
uint16_t input_pos = 1; // position in input buffer
uint16_t output_pos = 1; // position in output buffer
uint8_t func_code = 0x00; // current function code being processed
typedef void (* CallbackTemplate)(const uint8_t*);
CallbackTemplate callback_table[128]; // table of callback functions
uint16_t checksum = 0; // stores checksums during calculation
uint8_t byte0 = 0x00;
uint8_t byte1 = 0x00;
uint16_t uint16 = 0;
uint16_t body_end_idx = 0;
// ----------------------------------------------------
// ---------- Standard Function Codes -----------------
const uint8_t BAD_PACKET = 0x00; // indicates corrupt packet was sent/received
const uint8_t IDENTITY   = 0x01; // identity request/response function code
// ----------------------------------------------------
// ==== ^^ EVERYTHING ABOVE THIS POINT IS STANDARD ====

// ---------- Custom Imports and objects --------------

// ---- MUST SET TO UNIQUE BYTE VALUE FOR EACH ARDUINO-
const uint8_t MYID = 0x01; // Unique identifier for this arduino
// ---------- Custom Function Codes -------------------
//const uint8_t LASER_TILT_SERVO  = 0x02; // set position/vel/accel for laser tilt servo
//const uint8_t ARDUINO_LED       = 0x08; // set arduino debug led state: 0x00 = off, 0x01 = on
// ---------- pin vars --------------------------------
//const int pin_led          = 13; // active high status LED control pin.
// ----------------------------------------------------

void setup() {
  // ---------------- Set modes for all pins ---------------------
  // pinMode(pin_led, OUTPUT);
  // ---------------- Custom init steps --------------------------
  // ...
  // ---------------- Set function-code handler callbacks --------
  //register_callback(LASER_TILT_SERVO, &cb_laser_tilt_servo);
  //register_callback(ARDUINO_LED, &cb_arduino_led);
  // ---------------- Standard Packet Management -----------------
  //Serial.begin(9600, SERIAL_5E1); // 0x20 Configure serial to use 1 bit even parity.
  register_callback(BAD_PACKET, &cb_bad_packet);
  register_callback(IDENTITY, &cb_identity);
  Serial.begin(38400);
  myPacketSerial.setStream(&Serial);
  myPacketSerial.setPacketHandler(&onPacketReceived);
}

void loop() {
  // ---- Standard protocol maintenance stuff -----------
  myPacketSerial.update();  // Process incoming packets
  if (myPacketSerial.overflow()) {
    set_response_bad_packet();
    send_response();
  }
  corrupt_packet = false; // reset corrupt_packet flag
  now = millis();
  if (now - heartbeat > heartbeat_timeout) {
    comm_timeout = true;
    digitalWrite(pin_led, HIGH);
  }
  else {
    comm_timeout = false;
    digitalWrite(pin_led, LOW);
  }
  // -------- Your custom code goes here ------------------
  // Do stuff in response to variables that have been set in callback functions:
}

//------------- Custom callback functions -------------------- 

// set arduino led to specified state
/*
void cb_arduino_led(const uint8_t* input_buffer) {
  if (input_buffer[input_pos++] == 0x00) {
    digitalWrite(pin_led, LOW);
  }
  else {
    digitalWrite(pin_led, HIGH);
  }
  response[output_pos++] = func_code; // explicit confirm
}
*/

/*
void cb_laser_tilt_servo(const uint8_t* input_buffer) {
  byte0 = input_buffer[input_pos++];
  byte1 = input_buffer[input_pos++];
  merge_uint16(uint16, byte0, byte1);
  // equivalent microsecond value is uint16 / 4
  if (uint16 >= 4000 and uint16 <= 8000) {
    maestro.setTarget(3, uint16);
  }
  response[output_pos++] = func_code; // explicit confirm
}
*/

// ----------------------------------------------------------------

// ----------------- Standard helper functions --------------------

// Callback function for new packet received
void onPacketReceived(const uint8_t* buffer, size_t size) {
  if (validate_packet(buffer, size) == false) {
    set_response_bad_packet();
  }
  else {
    heartbeat = millis();
    // Process each code and following args (if any):
    body_end_idx = size - 3; // position of last data byte in input buffer
    input_pos = 1; // position in input buffer
    output_pos = 1; // position in output buffer
    while (input_pos <= body_end_idx) {
      func_code = buffer[input_pos++];
      if (callback_table[func_code] == NULL) {
        set_response_bad_packet();
        break;
      }
      else {
        callback_table[func_code](buffer);
      }
    }
  }
  send_response(); // every received packet has a corresponding response packet
  // ^ this sends whatever is in the response buffer up to ouput_pos
}

// Package and send contents of response buffer up to output_pos.
void send_response() {
  pack_response();
  myPacketSerial.send(response, output_pos);
}

// register a callback function to handle function code "code"
// provide a pointer to the callback function ("func_ptr")
void register_callback(uint8_t code, CallbackTemplate func_ptr) {
  callback_table[(int)code] = func_ptr;
}

// Callback that handles case where corrupt packet is received.
void cb_bad_packet(const uint8_t* input_buffer) {
  // Host reported a bad packet. TODO
}

// Callback that handles identity request.
void cb_identity(const uint8_t* input_buffer) {
  response[output_pos++] = IDENTITY;
  response[output_pos++] = MYID;
}

// Populates the response buffer with the standard bad packet message
// and sets the global corrupt_packet flag to true.
void set_response_bad_packet() {
  output_pos = 1;
  response[output_pos++] = BAD_PACKET;
  corrupt_packet = true;
}

// Set length byte, calc checksum, and send packet
// Note: buffer should leave a blank byte at index 0 to make
// room for the length byte. "size" should reflect length of
// data plus one for the length byte.
void pack_response() {
  // Set response length byte:
  response[0] = (uint8_t)((output_pos+2) % 256);
  // Set checksum for response:
  checksum = 0;
  for (int i = 0; i < output_pos; ++i)
    checksum += (uint16_t)response[i];
  split_uint16(checksum, byte0, byte1);
  response[output_pos++] = byte0;
  response[output_pos++] = byte1;
}

// Splits "int16" into two bytes "byte0" and "byte1"
// Note: "byte0" is most significant byte and "byte1" is least significant
void split_uint16(uint16_t& int16, uint8_t& byte0, uint8_t& byte1) {
  byte0 = ((uint8_t) ((int16) >> 8));
  byte1 = ((uint8_t) ((int16) & 0xff));
}

// Merges "byte0" and "byte1" into a "uint16"
// Note "byte0" is most significant byte and "byte1" is least significant
void merge_uint16(uint16_t& int16, uint8_t& byte0, uint8_t& byte1) {
  int16 = ((uint16_t)byte1 << 8) + ((uint16_t)byte0);
}

// Check packet for corruption. Return "true" if packet passes,
// return "false" otherwise.
boolean validate_packet(const uint8_t* buffer, size_t size) {
  if (size < 3) {
    // Packet should have one length byte and two checksum bytes.
    return false;
  }
  // validate packet length:
  if (buffer[0] != (uint8_t)(size % 256)) {
    // Packet length incorrect. Corrupt bytes likely.
    return false;
  }
  // validate packet checksum:
  byte0 = buffer[size-1];
  byte1 = buffer[size-2];
  merge_uint16(checksum, byte0, byte1);
  // calculate checksum:
  for (int i = 0; i < size-2; ++i)
    checksum -= (uint16_t)buffer[i];
  if (checksum != 0) {
    // if checksums match, then subtracting all byte should bring it back to zero.
    return false;
  }
  return true; // Packet passed validation.
}
// ----------------------------------------------------------------
