#!/usr/bin/env micropython
#
# Copyright (c) 2020, Ian Chapman (Chapmip Consultancy)
#
# This software is licensed under the MIT license (see LICENSE.TXT)
#
# Low-level I/O classes to facilitate "bare-metal" access in Micropython
# to STM32 memory locations and device registers (for learning purposes)
#
# Created on a Pyboard (PYB) v1.1 (with STM32F405RGT6 microcontroller)
# but should be readily adaptable to other STM32 Micropython builds
#
# See README.md for information on typical usage of classes and methods


import machine
import sys
import stm


# Determine endian-ness of system

byteorder = sys.byteorder
if byteorder == 'little':
    little_endian = True
elif byteorder == 'big':
    little_endian = False
else:
    raise NameError("sys.byteorder returned '{}'".format(byteorder))


# Allowed value types with size (bits), little- and big-endian offsets

value_types = { "32":  (32, 0, 0),
                "16L": (16, 0, 2),
                "16H": (16, 2, 0),
                "8Ll": (8, 0, 3),
                "8Lh": (8, 1, 2),
                "8Hl": (8, 2, 1),
                "8Hh": (8, 3, 0),  }


# Get machine.mem{X} function for bits size (can also use stm.mem{X})

def get_mem_func(size):
    return eval("machine.mem" + str(int(size)))


# Check for valid bits size

def check_bits_size(size):
    if size not in (32, 16, 8):
        raise ValueError("size must be 32, 16 or 8")


# Check for bit number in range for bits size

def check_bit_num(bit_num, size):
    if not isinstance(bit_num, int):
        raise ValueError("bit numbers must be integers")
    if not 0 <= bit_num <= size - 1:
        raise ValueError("bit numbers must be 0-{}".format(size-1))


# Check for value in range for bits size

def check_val_size(val, size):
    max_val = (1 << size) - 1
    if not 0 <= val <= max_val:
        raise ValueError("val must be 0-{:X}".format(max_val))


# Check bit field parameters (for read or write)

def check_bit_field_parms(num_bits, low_posn, size=32):
    check_bits_size(size)
    if not 1 <= num_bits <= size:
        raise ValueError("num_bits must be 1-{}".format(size))
    if not 0 <= low_posn <= size - 1:
        raise ValueError("low_posn must be 0-{}".format(size-1))
    if not num_bits + low_posn <= size:
        err_fmt = "num_bits + low_posn must be <= {}"
        raise ValueError(err_fmt.format(size))


# Get selected bit field from value (for read)

def get_bit_field(val, num_bits, low_posn, size=32):
    check_bit_field_parms(num_bits, low_posn, size)
    check_val_size(val, size)
    shifted = (val >> low_posn)
    mask = (1 << num_bits) - 1
    return shifted & mask


# Get bit maps for changing selected bit field in value (for write)

def get_bit_maps(val, num_bits, low_posn, size=32):
    check_bit_field_parms(num_bits, low_posn, size)
    check_val_size(val, num_bits)
    shifted = (val << low_posn)
    mask = ((1 << num_bits) - 1) << low_posn
    return shifted, mask


# Read data value at address with specified bit size

def read_data(addr, size=32):
    check_bits_size(size)
    mem = get_mem_func(size)
    mask = (1 << size) - 1
    val = mem[addr] & mask
    return val


# Write data value to specified address with defined bit size

def write_data(addr, val, size=32):
    check_bits_size(size)
    check_val_size(val, size)
    mem = get_mem_func(size)
    mem[addr] = val


# Read value of specified bit field at address with defined bit size

def read_bit_field(addr, num_bits=None, low_posn=0, size=32):
    if num_bits is None:
        num_bits = size
    check_bit_field_parms(num_bits, low_posn, size)
    mem = get_mem_func(size)
    mask = (1 << size) - 1
    val = mem[addr] & mask
    return get_bit_field(val, num_bits, low_posn, size)


# Write value to specified bit field at address with defined bit size

def write_bit_field(addr, val, num_bits=None, low_posn=0, size=32):
    if num_bits is None:
        num_bits = size
    check_bit_field_parms(num_bits, low_posn, size)
    shifted, mask = get_bit_maps(val, num_bits, low_posn, size)
    mem = get_mem_func(size)
    irq_state = machine.disable_irq()
    mem[addr] ^= (mem[addr] ^ shifted) & mask
    machine.enable_irq(irq_state)


# Iterate through matching STM32 register base and/or register names

def iter_names(match="", base=False, register=False):
    for name in dir(stm):
        if name[0] != "_" and not name[0].islower():
            if (base and not "_" in name) or (register and "_" in name):
                if name.startswith(match):
                    yield name


# Print out register bases and register names (external utility)

def list_names():
    bases = [name for name in iter_names(base=True)]
    registers = [name for name in iter_names(register=True)]
    print(bases)
    print()
    print(registers)


# Check for unique match from names (one and only one)

def match_name(match="", base=False, register=False):
    matches = []
    for name in iter_names(match, base, register):
        matches.append(name)
    if len(matches) == 1:
        return matches[0]               # Single match
    if match in matches:
        return match                    # Multiple matches, one exact
    raise ValueError("Unable to identify {} in names".format(match))


# Convert register base name into register prefix

def get_reg_prefix(base):
    prefix = base
    while prefix[-1].isdigit():         # Remove suffix digits
        prefix = prefix[:-1]
    if prefix.startswith("GPIO"):       # Letters instead of digits
        prefix = prefix[:-1]
    elif prefix == "UART":              # Special case: UART -> USART
        prefix = "USART"
    elif prefix.startswith("I2S"):      # Special case: I2SxEXT -> SPI
        prefix = "SPI"
    prefix += "_"
    return prefix


# Get register address from register base and register names

def get_reg_addr(base, register):
    base_val = getattr(stm, base)
    register_val = getattr(stm, register)
    return base_val + register_val


# Get register size from register name

def get_reg_size(name):
    if name[:-1].endswith("_BSRR"):     # Special cases: BSRRH and BSRRL
        return 16
    else:
        return 32


# Iterate through register names that match register base name and size

def iter_registers(base, size=32):
    check_bits_size(size)
    prefix = get_reg_prefix(base)
    for name in iter_names(prefix, register=True):
        reg_size = get_reg_size(name)
        if reg_size == size:
            yield name


# Print value with label as appropriate length hexadecimal and binary

def print_val(label, val, size=32):
    check_bits_size(size)
    check_val_size(val, size)
    nibbles = str(int(size/4))
    header_fmt = "{:<16s} {:^" + nibbles + "s} "
    content_fmt = "{:<16s} {:0" + nibbles + "X} "
    header = header_fmt.format("", "0x")
    content = content_fmt.format(label, val)
    for x in range(size, 0, -8):
        header += "  {:>2d}------{:<2d}".format(x-1, x-8)
        content += "   {:08b} ".format((val >> (x-8)) & 0xFF)
    print(header)
    print(content)


# Print register data from register base and register name

def print_reg(base, register, size=32):
    label = base + "." + register.split("_")[1]
    addr = get_reg_addr(base, register)
    val = read_data(addr, size)
    print_val(label, val, size)


# Print dump of all 32-bit and 16-bit registers for register base

def print_dump(base):
    for size in (32, 16):
        for register in iter_registers(base, size):
            print_reg(base, register, size)
        print()


# Get bit parameters from index key (including slice)

def get_bit_parms(key, size=32):
    err_msg = "index must be [bit] or [bit_h : bit_l] or [:]"
    if isinstance(key, int):            # [bit]
        hi = lo = key
    elif isinstance(key, slice):
        hi = key.start
        lo = key.stop
        if key.step is not None:        # [* : * : value]
            raise ValueError(err_msg)
        if hi is None and lo is None:   # [:]
            hi = size - 1
            lo = 0
        elif hi is None or lo is None:  # [* :] or [: *]
            raise ValueError(err_msg)
        elif lo > hi:                   # [bit_l:bit_h] -> [bit_h:bit_l]
            hi, lo = lo, hi
    else:
        raise ValueError("Unexpected key: {}".format(key))
    for val in hi, lo:
        check_bit_num(val, size)
    num_bits = (hi - lo) + 1
    low_posn = lo
    return num_bits, low_posn


# Memory class (base class for arbitrary non-labelled addresses)

class Mem:
    """
    Examples:
      Mem(0x40020014)
      Mem(0x4002001A, 16)
    """

    def __init__(self, addr, size=32):
        check_bits_size(size)
        addr = addr & 0xFFFFFFFF
        self.label = "Mem_0x{:08X}".format(addr)
        self.addr = addr
        self.size = size


    def read(self, *, size=None):
        if size is None:
            size = self.size
        return read_data(self.addr, size)


    def write(self, val, *, size=None):
        if size is None:
            size = self.size
        write_data(self.addr, val, size)


    def __getitem__(self, key):
        num_bits, low_posn = get_bit_parms(key, self.size)
        return read_bit_field(self.addr, num_bits, low_posn, self.size)


    def __setitem__(self, key, val):
        num_bits, low_posn = get_bit_parms(key, self.size)
        write_bit_field(self.addr, val, num_bits, low_posn, self.size)


    def bits(self, *bit_nums):
        bit_vals = []
        reg_val = self.read()
        for bit_num in bit_nums:
            check_bit_num(bit_num, self.size)
            bit_vals.append(1 if reg_val & (1 << bit_num) else 0)
        return tuple(bit_vals)


    def print(self):
        val = read_data(self.addr, self.size)
        print_val(self.label, val, self.size)


    def derive(self, new_type):
        info = value_types.get(new_type)
        if info is None:
            raise ValueError("No such value type")
        new_size, le_offset, be_offset = info
        offset = le_offset if little_endian else be_offset
        new_addr = (self.addr & ~3) + offset
        return Mem(new_addr, new_size)


    def __str__(self):
        return "{} at 0x{:08X} ({} bits)".format(self.label,
               self.addr, self.size)


# ADC common register mappings (not covered in STM32 module)

adc_common_base_name = "ADC123_COMMON"

adc_common = {  "CSR": "ADC_SR",
                "CCR": "ADC_CR1",
                "CDR": "ADC_CR2",  }


# Get register identifiers from input fields

def get_reg_id(fields):
    if fields[0] == "ADC":
        base_name = adc_common_base_name
        reg_name = adc_common.get(fields[1])
        if reg_name is None:
            err_fmt = "{} is not a valid ADC common register"
            raise ValueError(err_fmt.format(fields[1]))
    else:
        base_name = match_name(fields[0], base=True)
        prefix = get_reg_prefix(base_name)
        reg_name = match_name(prefix + fields[1], register=True)
    return base_name, reg_name


# Dump ADC common registers

def dump_adc_common():
    for item in adc_common:
        label = "ADC." + item
        addr = get_reg_addr(adc_common_base_name, adc_common[item])
        val = read_data(addr)
        print_val(label, val)


# Register class (extends Memory class to include STM32 register labels)

class Reg(Mem):
    """
    Examples:
      Reg("GPIOA.ODR")
      Reg("GPIOA.BSRRH")
      Reg("TIM2.PSC", 16)
    """

    def __init__(self, label, size=None):
        fields = label.split(".")
        if len(fields) != 2:
            raise ValueError("label must be 'base.reg'")
        base_name, reg_name = get_reg_id(fields)
        addr = get_reg_addr(base_name, reg_name)
        if size is None:
            size = get_reg_size(reg_name)
        super().__init__(addr, size)

        self.label = label
        self.base_name = base_name
        self.reg_name = reg_name


    def dump(self):
        if self.base_name == adc_common_base_name:
            dump_adc_common()
        else:
            print_dump(self.base_name)


    def __str__(self):
        return super().__str__() + ": {} + {}".format(self.base_name,
                                                      self.reg_name)


# Get bit parameters to isolate field in register array

def get_field_parms(key, reg_arr):
    if not isinstance(key, int):
        raise ValueError("index must be an integer")
    max_index = (reg_arr.num_regs * reg_arr.fields_per_reg) - 1
    if not 0 <= key <= max_index:
        raise ValueError("index must be 0-{}".format(max_index))
    elem, pos = divmod(key, reg_arr.fields_per_reg)
    lo_bit = pos * reg_arr.bits_per_field
    hi_bit = lo_bit + reg_arr.bits_per_field - 1
    return elem, hi_bit, lo_bit


# Format description of value to include plural 's' if not one

def format_plural(val, desc):
    if val == 1:
        return str(val) + ' ' + desc
    else:
        return str(val) + ' ' + desc + 's'


# Register Array class (fixed-length bit fields spanning 1+ registers)

class RegArr:
    """
    Examples:
      RegArr("GPIOA.MODER", 16, 2)
      RegArr("GPIOA.AFR0, AFR1", 8,4)
      RegArr("SYSCFG.EXTICR0, EXTICR1, EXTICR2, EXTICR3", 4, 4)
      RegArr("ADC1.SMPR2, SMPR1", 10, 3)
    """

    def __init__(self, labels, fields_per_reg, bits_per_field):
        fields = labels.split('.')
        if len(fields) != 2:
            raise ValueError("labels must be 'base.reg_L, ... ,reg_H'")
        base = fields[0]
        regs = fields[1].split(',')

        self.reg_array = []
        for reg in regs:
            label = base + '.' + reg.lstrip()
            self.reg_array.append(Reg(label))
            if self.reg_array[-1].size != 32:
                raise ValueError("Registers in array must be 32 bits")

        if not 1 <= fields_per_reg * bits_per_field <= 32:
            raise ValueError("{} fields x {} bits must be 1-32".format(
                             fields_per_reg, bits_per_field))

        self.num_regs = len(self.reg_array)
        self.fields_per_reg = fields_per_reg
        self.bits_per_field = bits_per_field


    def __getitem__(self, key):
        elem, hi_bit, lo_bit = get_field_parms(key, self)
        return self.reg_array[elem][hi_bit:lo_bit]


    def __setitem__(self, key, val):
        elem, hi_bit, lo_bit = get_field_parms(key, self)
        self.reg_array[elem][hi_bit:lo_bit] = val


    def print(self):
        header_fmt = "{:<16s} {:^8s}   "
        label_fmt = "{:<16s} {:08X}   "
        above_fmt = "{:^" + str(self.bits_per_field + 1) + "d} "
        field_fmt = "{:0" + str(self.bits_per_field) + "b}  "

        idx = (self.num_regs * self.fields_per_reg) - 1
        field_count = self.fields_per_reg
        for reg in reversed(self.reg_array):
            print(header_fmt.format("", "0x"), end='')
            for num in range(field_count):
                print(above_fmt.format(idx - num), end='')
            print()
            print(label_fmt.format(reg.label, reg.read()), end='')
            for num in range(field_count):
                print(field_fmt.format(self[idx - num]), end='')
            print()
            idx -= field_count


    def dump(self):
        self.print()
        print()
        for reg in self.reg_array:
            reg.print()


    def __str__(self):
        s = "Array of " + format_plural(self.num_regs, "register")
        s += " with " + format_plural(self.fields_per_reg, "field")
        s += "/register, " + format_plural(self.bits_per_field, "bit")
        s += "/field"
        for i, reg in enumerate(self.reg_array):
            s += "\n[{}]: ".format(i) + str(reg)
        return s
