# fluke19x-programmer

Video: https://www.youtube.com/watch?v=klQPO-uYMEA

# Random notes:
- ZIP file contains gerbers and such. This file was submitted to JLCPCB.
- A fixed baud rate of 115200 was used, which should work everywhere. Other speeds were not tested.
- 12MHz crystal was used, which should result in about 7.5% baud rate error, wich was not a problem.
- Forgot to mark LEDs and polarized caps on silkscreen (used non-polarized ceramic caps in practice).
- MCU is marked 3290PA on the schematic, but 3290A can be used just fine.
- Be careful aligning memory modules (card edge type) in this connector since the slot in the connector is slightly longer.
- Be careful about the correct orientation of memory modules in the connector (see video if not sure).

# Usage

Chip IDs:

	$ python programmer.py -i
	manufacturer's IDs (U3 U4): 00bf 00bf
	device IDs (U3 U4): 2781 2781

RAM test:

	$ python programmer.py -t
	error count: 0

Read flash:

	$ python programmer.py -r firmware.bin

Write flash:

	$ python programmer.py -w firmware.bin
