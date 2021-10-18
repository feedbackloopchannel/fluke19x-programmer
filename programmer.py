import argparse
import serial

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--device', default = '/dev/ttyUSB0')
parser.add_argument('-t', '--test', nargs = '?', const = True, default = False)
parser.add_argument('-i', '--id', nargs = '?', const = True, default = False)
parser.add_argument('-e', '--erase', nargs = '?', const = True, default = False)
parser.add_argument('-r', '--read', default = '')
parser.add_argument('-w', '--write', default = '')
# old version has 16Mbit (1M words) Flash chips (as opposed to 8Mbit in new version)
parser.add_argument('-o', '--old', nargs = '?', const = True, default = False)
args = parser.parse_args()

flash_size_words = 512 * 1024
if args.old:
  flash_size_words *= 2;

ser = serial.Serial(args.device, 115200, timeout = 12)

if args.test: # RAM test
  ser.write(b't')
  data = ser.read(4)
  print("error count: {}".format(int.from_bytes(data, 'little')))

elif args.id:
  ser.write(b'i')
  m_id1 = int.from_bytes(ser.read(2), 'little')
  m_id2 = int.from_bytes(ser.read(2), 'little')
  print("manufacturer's IDs (U3 U4): {0:04x} {1:04x}".format(m_id1, m_id2))
  d_id1 = int.from_bytes(ser.read(2), 'little')
  d_id2 = int.from_bytes(ser.read(2), 'little')
  print("device IDs (U3 U4): {0:04x} {1:04x}".format(d_id1, d_id2))

elif args.erase:
  val = input("erase FLASH (y/n): ")
  if val == 'y':
    ser.write(b'e')
    ser.read(1) # wait for completion

elif len(args.read) > 0:
  with open(args.read, 'wb') as f:
    ser.write(b'r')
    start_addr = 0
    size_words = flash_size_words
    ser.write(start_addr.to_bytes(4, 'little'))
    ser.write(size_words.to_bytes(4, 'little'))
    count = 0
    for i in range(size_words * 4):
      data = ser.read(1)
      f.write(data)
      count += 1
      if count == 16 * 1024:
        print('.', end = '', flush = True)
        count = 0
    print()

elif len(args.write) > 0:
  val = input("write FLASH (y/n): ")
  if val == 'y':

    # erase first
    ser.write(b'e')
    ser.read(1) # wait for completion

    with open(args.write, 'rb') as f:
      ser.write(b'w')
      start_addr = 0
      size_words = flash_size_words
      ser.write(start_addr.to_bytes(4, 'little'))
      ser.write(size_words.to_bytes(4, 'little'))
      count = 0
      for i in range(size_words * 4):
        data = f.read(1)
        ser.write(data);
        count += 1
        if count == 16 * 1024:
          print('.', end = '', flush = True)
          count = 0
      print()

ser.close()
