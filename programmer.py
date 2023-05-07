#!/usr/bin/python

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

parser.add_argument('-R', '--Read', nargs = '?', const = True, default = False) # for testing
parser.add_argument('-W', '--Write', nargs = '?', const = True, default = False) # for testing

parser.add_argument('-s', '--scopemeter', nargs = '?', const = True, default = False) # read model and serial number

args = parser.parse_args()

flash_size_words = 512 * 1024
if args.old:
  flash_size_words *= 2;

ser = serial.Serial(args.device, 115200, timeout = 20)

if args.test: # RAM test
  ser.write(b't')
  errors_u1 = ser.read(4)
  errors_u2 = ser.read(4)
  print("error count U1: {}".format(int.from_bytes(errors_u1, 'little')))
  print("error count U2: {}".format(int.from_bytes(errors_u2, 'little')))

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
        ser.write(data)
        count += 1
        if count == 16 * 1024:
          print('.', end = '', flush = True)
          count = 0
      print()

elif args.Read:
  ser.write(b'r')
  start_addr = 0
  size_words = 64
  ser.write(start_addr.to_bytes(4, 'little'))
  ser.write(size_words.to_bytes(4, 'little'))
  addr = 0
  count = 0
  for i in range(size_words * 4):
    if count == 0:
      print("{0:08x}".format(addr), end = '')
    data = ser.read(1)
    print(" {0:02x}".format(int.from_bytes(data, 'little')), end = '')
    count += 1
    if count == 16:
      print()
      count = 0
      addr += 16
  print()

elif args.Write:
  ser.write(b'w')
  start_addr = 1
  size_words = 8
  ser.write(start_addr.to_bytes(4, 'little'))
  ser.write(size_words.to_bytes(4, 'little'))
  ser.write(0x11223344.to_bytes(4, 'big'));
  ser.write(0x55667788.to_bytes(4, 'big'));
  ser.write(0x88776655.to_bytes(4, 'big'));
  ser.write(0x44332211.to_bytes(4, 'big'));
  ser.write(0x11223344.to_bytes(4, 'big'));
  ser.write(0x55667788.to_bytes(4, 'big'));
  ser.write(0x88776655.to_bytes(4, 'big'));
  ser.write(0x44332211.to_bytes(4, 'big'));

elif args.scopemeter:
  # model
  ser.write(b'r')
  start_addr = 0x201a
  size_words = 1
  ser.write(start_addr.to_bytes(4, 'little'))
  ser.write(size_words.to_bytes(4, 'little'))
  model = ''
  for i in range(size_words * 4):
    data = ser.read(1)
    if data != 0:
      model = model + data.decode('utf-8')
  print("Model: {}".format(model))

  # serial number
  ser.write(b'r')
  start_addr = 0x2022
  size_words = 2
  ser.write(start_addr.to_bytes(4, 'little'))
  ser.write(size_words.to_bytes(4, 'little'))
  sn = ''
  for i in range(size_words * 4):
    data = ser.read(1)
    if data != 0:
      sn = sn + data.decode('utf-8')
  print("SN: {}".format(sn))

ser.close()
