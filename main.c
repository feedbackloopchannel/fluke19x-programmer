#define BAUD 115200

#include <avr/io.h>
#include <util/setbaud.h>

inline void nop() { asm volatile("nop"); }
inline void nopn(uint8_t n) { while (n > 0) { nop(); --n; } }

inline void mempwr_on() { PORTB &= ~_BV(PB0); nopn(255); }
inline void mempwr_off() { PORTB |= _BV(PB0); }

inline void rom_enable() { PORTE &= ~_BV(PE2); nop(); }
inline void rom_disable() { PORTE |= _BV(PE2); }

inline void ram_enable() { PORTE &= ~_BV(PE3); nop(); }
inline void ram_disable() { PORTE |= _BV(PE3); }

inline void read_enable() { PORTE &= ~_BV(PE5); nop(); }
inline void read_disable() { PORTE |= _BV(PE5); }

inline void write_enable() { PORTE &= ~_BV(PE6); nop(); }
inline void write_disable() { PORTE |= _BV(PE6); }
inline void write_pulse() { write_enable(); write_disable(); }

inline void reset_enable() { PORTE &= ~_BV(PE7); }
inline void reset_disable() { PORTE |= _BV(PE7); nopn(255); }

inline void data_ports_in() { DDRA = 0; DDRC = 0; DDRD = 0; DDRF = 0; }
inline void data_ports_out() { DDRA = 0xff; DDRC = 0xff; DDRD = 0xff; DDRF = 0xff; }

inline void set_address(uint32_t addr) {
  PORTH = addr & 0xff;
  PORTJ = (addr >> 8) & 0x7f;
  PORTG = (addr >> 15) & 0x1f;
}

void module_enable() {
  mempwr_on();
  rom_disable();
  ram_disable();
  read_disable();
  write_disable();
  reset_disable();
}

void module_disable() {
  set_address(0);
  reset_enable();
  read_enable();
  write_enable();
  rom_enable();
  ram_enable();
  mempwr_off();
}

volatile uint8_t data[4];

inline void read_data() {
  read_enable();
  data[0] = PINA;
  data[1] = PINC;
  data[2] = PIND;
  data[3] = PINF;
  read_disable();
}

void uart_init() {
    UBRR0H = UBRRH_VALUE;
    UBRR0L = UBRRL_VALUE;

#if USE_2X
    UCSR0A |= _BV(U2X0);
#else
    UCSR0A &= ~_BV(U2X0);
#endif

    UCSR0C = _BV(UCSZ00) | _BV(UCSZ01); // 8-bit data
    UCSR0B = _BV(RXEN0) | _BV(TXEN0);   // enable RX and TX
}

inline void uart_tx(uint8_t byte) {
  loop_until_bit_is_set(UCSR0A, UDRE0); // wait until data register empty
  UDR0 = byte;
}

inline uint8_t uart_rx() {
  loop_until_bit_is_set(UCSR0A, RXC0); // wait for data
  return UDR0;
}

inline void tx_data() {
  uart_tx(data[0]);
  uart_tx(data[1]);
  uart_tx(data[2]);
  uart_tx(data[3]);
}

void write_command_sequence(uint8_t command) {
  set_address(0x5555);
  PORTA = 0xaa;
  PORTD = 0xaa;
  write_pulse();
  set_address(0x2aaa);
  PORTA = 0x55;
  PORTD = 0x55;
  write_pulse();
  set_address(0x5555);
  PORTA = command;
  PORTD = command;
  write_pulse();
}

void read_chip_ids() {
  module_enable();
  rom_enable();
  // software ID mode entry
  data_ports_out();
  write_command_sequence(0x90);
  // manufacturer's IDs
  data_ports_in();
  set_address(0);
  read_data();
  tx_data();
  // device IDs
  set_address(1);
  read_data();
  tx_data();
  module_disable();
}

// wait for both chips
inline void wait_for_completion() {
  uint8_t ready;
  do {
    read_enable();
    ready = (PINA ^ PORTA) & (PIND ^ PORTD) & 0x80;
    read_disable();
  } while (!ready);
}

void erase_chips() {
  module_enable();
  rom_enable();
  data_ports_out();
  write_command_sequence(0x80);
  write_command_sequence(0x10);
  data_ports_in();
  wait_for_completion();
  uart_tx(0); // signal completion
  module_disable();
}

inline uint32_t rx_word() {
  uint32_t word = uart_rx();
  word |= (uint32_t)uart_rx() << 8;
  word |= (uint32_t)uart_rx() << 16;
  word |= (uint32_t)uart_rx() << 24;
  return word;
}

void read_flash() {
  const uint32_t from_addr = rx_word();
  const uint32_t size_words = rx_word();
  const uint32_t to_addr = from_addr + size_words;
  module_enable();
  rom_enable();
  for (uint32_t addr = from_addr; addr < to_addr; ++addr) {
    set_address(addr);
    read_data();
    tx_data();
  }
  module_disable();  
}

void write_flash() {
  const uint32_t from_addr = rx_word();
  const uint32_t size_words = rx_word();
  const uint32_t to_addr = from_addr + size_words;
  module_enable();
  rom_enable();
  for (uint32_t addr = from_addr; addr < to_addr; ++addr) {
    data_ports_out();
    write_command_sequence(0xa0);
    set_address(addr);
    PORTA = uart_rx();
    PORTC = uart_rx();
    PORTD = uart_rx();
    PORTF = uart_rx();
    write_pulse();
    data_ports_in();
    wait_for_completion();
    nopn(200);
  }
  module_disable();  
}

void test_ram() {
  module_enable();
  ram_enable();
  data_ports_out();

  // fill memory with pseudorandom numbers
  static const uint32_t SIZE = 256 * 1024ul;
  static const uint32_t START = 123456789; // arbitrary number to start with
  uint32_t delta = 2654435769; // based on golden ratio
  uint32_t word = START;
  for (uint32_t addr = 0; addr < SIZE; ++addr) {
    set_address(addr);
    PORTA = word & 0xff;
    PORTC = (word >> 8) & 0xff;
    PORTD = (word >> 16) & 0xff;
    PORTF = (word >> 24) & 0xff;
    write_pulse();
    word += delta;
  }
  data_ports_in();
  // generate the same sequence, read and compare
  word = START;
  uint32_t errors_u1 = 0;
  uint32_t errors_u2 = 0;
  for (uint32_t addr = 0; addr < SIZE; ++addr) {
    set_address(addr);
    read_data();
    if (data[0] != (word & 0xff)) ++errors_u1;
    if (data[1] != ((word >> 8) & 0xff)) ++errors_u1;
    if (data[2] != ((word >> 16) & 0xff)) ++errors_u2;
    if (data[3] != ((word >> 24) & 0xff)) ++errors_u2;
    word += delta;
  }
  uart_tx(errors_u1);
  uart_tx(errors_u1 >> 8);
  uart_tx(errors_u1 >> 16);
  uart_tx(errors_u1 >> 24);
  uart_tx(errors_u2);
  uart_tx(errors_u2 >> 8);
  uart_tx(errors_u2 >> 16);
  uart_tx(errors_u2 >> 24);

  module_disable();
}

int main() {
  MCUCR |= _BV(PUD); // disable pull-up

  // controls on port B
  mempwr_off();
  DDRB = _BV(PB0) | _BV(PB4) | _BV(PB5) | _BV(PB6) | _BV(PB7);

  // controls on port E
  DDRE = _BV(PE2) | _BV(PE3) | _BV(PE5) | _BV(PE6) | _BV(PE7);

  // address outputs
  DDRH = 0xff;
  DDRJ = 0x7f;
  DDRG = 0x1f;

  uart_init();

  while (1) {
    char c = uart_rx();
    if (c == 'i') {
      read_chip_ids();
    } else if (c == 'e') {
      erase_chips();
    } else if (c == 'r') {
      read_flash();
    } else if (c == 'w') {
      write_flash();
    } else if (c == 't') {
      test_ram();
    }
  }
}
