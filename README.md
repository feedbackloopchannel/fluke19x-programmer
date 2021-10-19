# fluke19x-programmer

https://www.youtube.com/watch?v=klQPO-uYMEA

Random notes:
- ZIP file contains gerbers and such. This file was used to submit to JLCPCB.
- A fixed baud rate of 115200 was used, which should work everywhere. Other speeds were not tested.
- 12MHz crystal was used, which should result in about 7.5% baud rate error, wich was not a problem.
- Forgot to mark LEDs and polarized caps on silkscreen (used non-polarized ceramic caps in practice).
- MCU is marked 3290PA on the schematic, but 3290A can be used just fine
- Be careful aligning memory modules in this connector since the slot in the connector is slightly longer.
