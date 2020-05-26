# The `iol.py` module

**This is the user manual for the `iol.py` module.  It is currently a working draft that is still under review.**

# Quick summary

* Low-level I/O classes to facilitate "bare-metal" access in Micropython to STM32 memory locations and peripheral registers (for learning purposes)

* Created on a Pyboard (PYB) v1.1 (with STM32F405RGT6 microcontroller) but should be readily adaptable to other STM32 Micropython builds

# Quick links
* [History](https://github.com/Chapmip/micropython-stm32-iol#history)
* [Getting started](https://github.com/Chapmip/micropython-stm32-iol#getting-started)
* [Source code](https://github.com/Chapmip/micropython-stm32-iol#source-code)
* [Class  `iol.Reg`](https://github.com/Chapmip/micropython-stm32-iol#class-iolreg--low-level-io-access-to-a-single-stm32-peripheral-register)
* [Class `iol.RegArr`](https://github.com/Chapmip/micropython-stm32-iol#class-iolregarr--low-level-io-access-to-one-or-more-stm32-peripheral-registers-containing-uniform-array-of-bit-fields)
* [Class `iol.Mem`](https://github.com/Chapmip/micropython-stm32-iol#class-iolmem--low-level-io-access-to-a-single-stm32-memory-location)
* [Gotchas!](https://github.com/Chapmip/micropython-stm32-iol#gotchas)
* [References](https://github.com/Chapmip/micropython-stm32-iol#references)

# History

I created the `iol.py` module when I wanted to experiment with "bare metal" access to STM32 peripheral registers on a Pyboard v1.1.  I had obtained the Udemy course [*"Embedded Systems Bare-Metal Programming Ground Up™ (STM32)"*](https://www.udemy.com/course/embedded-systems-bare-metal-programming/) but was unable to use the examples directly as I didn't have a Windows PC on which to run the required Keil uVision environment.  I therefore chose to create classes to simulate "bare metal" access in Micropython rather than C.

I wasn't sure whether the Micropython system footprint would get in the way of "bare metal" accesses to peripheral registers, but I didn't find this generally to be the case.  In most cases, I have been able to work around issues of contention by reading carefully the Micropython documentation and avoiding a few on-chip peripheral functions that are dedicated to Micropython.

Inevitably, code written in Micropython will run considerably slower than C code.  I only found this to be a problem, though, during one experiment with the SPI bus, in which Micropython code is unable to keep up with the high speed of the bus (up to 21 MHz).  Even in this case, I was able to work around this limitation by re-writing the critical section of code using inline assembler code.

My code examples inspired by the Udemy course (but using the `iol.py` module and Micropython) can be found in my separate repository [here](https://github.com/Chapmip/micropython-stm32-examples).

# Getting started

When plugged into the USB port of a computer (using a Micro-USB B to USB A lead), the Pyboard is configured to appear as  both:

* An **MSC (Mass Storage Class) device** ⁠— for mounting into the filesystem of the computer as a dedicated drive showing the files in the flash memory of the Pyboard (either its inbuilt flash or an installed MicroSD card)

* A **VCP (Virtual Com Port) device** ⁠— for access via a serial terminal program on the computer to the REPL (Read–Evaluate–Print-Loop) environment on the Pyboard

On the Chromebook, I found that the Pyboard filesystem appeared automatically in the "Files" application a few seconds after inserting the USB connector.  I was then able to access the REPL prompt by installing the Chrome OS [Serial Term](https://chrome.google.com/webstore/detail/serial-term/fnjkimblohniildfepjhejeppenokhie) app and configuring the settings as per the screenshot below:

![Chrome OS Serial Terminal settings for Pyboard](/photos/Chrome%20OS%20Serial%20Terminal%20settings%20for%20Pyboard.png?raw=true "Chrome OS Serial Terminal settings for Pyboard")

To add the `iol.py` module to the Pyboard, copy it from the computer into the top folder of the Pyboard filesystem.  From the REPL environment, the module can then be brought into operation after issuing an `import iol` instruction, as illustrated below:

![Using iol module to access ports directly](/photos/Using%20iol%20module%20to%20access%20ports%20directly.png?raw=true "Using iol module to access ports directly")

**Note:** To avoid possible corruption of the Pyboard filesystem, it is important that the "Eject" operation is performed in the Chrome OS "Files" app before either:

* Disconnecting the USB cable; or
* Pressing the reset button on the Pyboard

In general, the reset button should be used as a last resort for a "cold start" of the Pyboard ⁠— for example, if the REPL environment has crashed.  In most other cases, it is adequate to perform a "warm start" by issuing a `<CONTROL-D>` on a blank line of the REPL prompt.

# Source code

The source code for `iol.py` can be viewed and downloaded [`here`](/iol.py).  The following sections describe further the classes and associated methods exposed by the module.

# Class `iol.Reg` ⁠— low-level I/O access to a single STM32 peripheral register

The `iol.Reg` class enables a single STM32 peripheral register to be manipulated in a more fluent way from Micropython.

## Constructor for `iol.Reg`

Create a new `iol.Reg` object corresponding to an STM32 register and assign it to `reg_obj`:

    reg_obj = iol.Reg(label, size=32)

* `label` is a string of the form `"<base>.<register>"`, where `<base>` is the name of an STM32 peripheral block (e.g. "GPIOA") and `<register>` is the name of an individual register within that block (e.g. "ODR").

* `size` is an optional integer value that specifies the size of the register (32, 16 or 8 bits), overriding the inference built in to the module (usually 32 bits).  Use this feature with caution, as some STM32 registers can only be accessed in larger sizes (check the STM32 data sheet and reference manuals for specifics — see [References](https://github.com/Chapmip/micropython-stm32-iol#references)).

Examples:

    pa_odr = iol.Reg("GPIOA.ODR")
    t2_psc = iol.Reg("TIM2.PSC", 16)

Notes:

The STM32 `<base>` and `<register>` values are derived from the Micropython `stm` module, which is included in compatible builds.  A completes list of these values can be obtained by invoking the module-level method `iol.list_names()`.

The `iol.py` module also handles a few special cases in which the `stm` manual falls short (for example, the common registers for ADC1,2,3 which are not defined in the `stm` module but can be accessed using the special `label` strings "ADC.CSR", "ADC.CCR" and "ADC.CDR").

## Methods for `iol.Reg`

### `iol.Reg.read()`

Read the current value held in the STM32 register associated with the `iol.Reg` object assigned to `reg_obj`:
 
    reg_value = reg_obj.read(*, size=None)
    
* `size` is an optional integer value (not valid as a positional parameter ⁠— must be assigned explictly by name) that specifies the bit width of the read operation (32, 16 or 8 bits), overriding the inference built in to the module (usually 32 bits).  Refer to the warning in the [constructor section](https://github.com/Chapmip/micropython-stm32-iol#constructor-for-iolreg) about overriding the default read size.

* The return value (`reg_value`) will be a positive integer (or zero) corresponding to the size being read.

Note that the alternative terser syntax `value = reg_obj[:]` can also be used for this operation.

### `iol.Reg.write()`

Write a value to the STM32 register associated with the `iol.Reg` object assigned to `reg_obj`:
 
    reg_obj.write(value, *, size=None)

* `value` is the positive integer (or zero) value to be written into the STM32 register.  It must be within the range of the bit width defined by the explicit `size` parameter (see below) if included, and the bit width defined for the `iol.Reg` object when it was constructed.
    
* `size` is an optional integer value (not valid as a positional parameter ⁠— must be assigned explictly by name) that specifies the bit width of the read operation (32, 16 or 8 bits), overriding the inference built in to the module (usually 32 bits).  Refer to the warning in the [constructor section](https://github.com/Chapmip/micropython-stm32-iol#constructor-for-iolreg) about overriding the default read size.

It may also be possible to use the alternative terser syntax `reg_obj[:] = value` for this operation.  Note, however, that the latter option causes a read operation to be made to the STM32 register before the write is carried out.  If there is a risk that this may cause unwanted side-effects, then the `reg_obj.write()` method (which only leads to a write operation) is a safer option.

### `iol.Reg[bit]` for read

Read a single bit from the STM32 register associated with the `iol.Reg` object assigned to `reg_obj`:**
 
    bit_value = reg_obj[bit_number]

* `bit_number` is the positive integer (or zero) number of the bit to be read from the STM32 register.  It must be within the range of the bit width defined for the `iol.Reg` object when it was constructed.

* The return value (`bit_value`) is always one of the integers 0 or 1

### `iol.Reg[bit]` for write

Write to a single bit in the STM32 register associated with the `iol.Reg` object assigned to `reg_obj`:
 
    reg_obj[bit_number] = bit_value

* `bit_number` is the positive integer (or zero) number of the bit to be read from the STM32 register.  It must be within the range of the bit width defined for the `iol.Reg` object when it was constructed.

* `bit_value` must evaluate to one of the integers 0 or 1

### `iol.Reg[high:low]` for read

Read a contiguous bit field from the STM32 register associated with the `iol.Reg` object assigned to `reg_obj`:**
 
    bit_field_value = reg_obj[bit_high:bit_low]

* `bit_high` and `bit_low` are the positive integer (or zero) numbers of the highest bit and the lowest bit in the contiguous bit field to be read from the STM32 register.  Both values must be within the range of the bit width defined for the `iol.Reg` object when it was constructed.

* If `bit_high` < `bit_low`, then these values will be swapped so that the return value always has its least significant bit corresponding to the least significant bit of the bit field in the STM32 register.

* The return value (`bit_field_value`) is shifted right as necessary to ensure that its least significant bit corresponds to the least significant bit of the contiguous bit field in the STM32 register.

*Note that this adaptation of the Python "slicing" notation `[a:b]` is convenient for bit fields but, by design, is inconsistent with the general Python approach to the slicing of objects, in which `a` is always a starting position and `b` is **one greater** than the finishing position (i.e. not included).  This is unfortunate but a pragmatic choice, as references in the STM32 documentation to bit fields within registers (such as "TIMx_CR1[9:8]" for the 2 bit CKD clock division value) always include the upper bit value within the bit field, so it would be confusing to do otherwise.*

### `iol.Reg[high:low]` for write

Write to a contiguous bit field in the STM32 register associated with the `iol.Reg` object assigned to `reg_obj`:
 
    reg_obj[bit_high:bit_low] = bit_field_value

* `bit_high` and `bit_low` are the positive integer (or zero) numbers of the highest bit and the lowest bit in the contiguous bit field to be read from the STM32 register.  Both values must be within the range of the bit width defined for the `iol.Reg` object when it was constructed.

* If `bit_high` < `bit_low`, then these values will be swapped so that the least significant bit of `bit_field_value` is always written to the least significant bit of the bit field in the STM32 register.

* `bit_field_value` must be a positive integer (or zero) within the range of the number of bits for the bit field defined by `bit_high` and `bit_low` (e.g. 0 to 7 for a 3-bit field).

*See note in ["for read" section](https://github.com/Chapmip/micropython-stm32-iol#iolreghighlow-for-read) regarding the non-standard adaptation of the Python "slicing" notation.*

### `iol.Reg.bits()`

Read a non-contiguous collection of bits from the STM32 register associated with the `iol.Reg` object assigned to `reg_obj`:
 
    bit_vals_tuple = reg_obj.bits(bit_nums_tuple)

* `bit_nums_tuple` is a tuple containing one or more positive integer (or zero) numbers of the individual bits to be read from the STM32 register.  All values in the tuple must be within the range of the bit width defined for the `iol.Reg` object when it was constructed.

* The return value (`bit_vals_tuple`) is a tuple containing one of the integers 0 or 1 corresponding to the bit value in the STM32 register for each of the bit numbers specified in `bit_nums_tuple`, in the same order as the input tuple.

*This method is useful for checking the states of multiple bits in a single register without the need for individual reads or repeated "AND-masking" of the read value in the user's code.*

### `iol.Reg.print()`

Print in human-friendly format the current value held in the STM32 register associated with the `iol.Reg` object assigned to `reg_obj`:
 
    reg_obj.print()
    
*This method is useful for debugging problems with "bare-metal" code in which it is necessary to inspect the contents of STM32 peripheral registers at a hexadecimal level or an individual bit level.*

### `iol.Reg.dump()`

Dump in human-friendly format the contents of all of the STM32 registers associated with the STM32 peripheral block (e.g. "GPIOA") specified when constructing the `iol.Reg` object:

    reg_obj.dump()
    
The output of `dump()` is an iteration of the `print()` output for each of the defined registers in the STM32 peripheral block.

**Note that this method is not available for [`iol.Mem`](https://github.com/Chapmip/micropython-stm32-iol#class-iolmem--low-level-io-access-to-a-single-stm32-memory-location) objects.**

*This method is useful for debugging problems with "bare-metal" code in which it is necessary to inspect the contents of the whole set of related STM32 peripheral registers at a hexadecimal level or an individual bit level.*

### `iol.Reg.derive()`

Derive an [`iol.Mem`](https://github.com/Chapmip/micropython-stm32-iol#class-iolmem--low-level-io-access-to-a-single-stm32-memory-location) object of a specified type from an `iol.Reg` (or `iol.Mem`) object assigned to `reg_obj`:
 
    mem_obj = reg_obj.derive(new_type)

* `new_type` is a string specifying the size of the memory location to be applied to the new `iol.Mem` object and its offset from the memory location stored in `reg_obj`.   The string is a concatenation of the required size ("32", "16" or "8") with an appropriate offset specifier:

  * for 32 bits: none
  * for 16 bits: "L" or "H" for lower or upper half
  * for 8 bits: "Ll", "Lh", "Hl" and "Hh" (note the lower-case "L"s) — in order from least significant to most significant byte

The endian-ness of the system (big- or little-endian) is taken into account to ensure that the correct offset is applied for 16 bit and 8 bit addressing. 

# Class `iol.RegArr` ⁠— low-level I/O access to one or more STM32 peripheral registers containing uniform array of bit fields

The `iol.RegArr` class enables a set of STM32 peripheral registers (one or more) containing a uniform array of bit fields to be manipulated as a single array from Micropython.

## Constructor for `iol.RegArr`

Create a new `iol.RegArr` object corresponding to a set of STM32 registers (one or more) and assign it to `reg_arr_obj`:

    reg_arr_obj = iol.RegArr(labels, fields_per_reg, bits_per_field)

* `labels` is a string of the form `"<base>.<register1>,<register2>...,<registerN>"`, where `<base>` is the name of an STM32 peripheral block (e.g. "GPIOA") and each `<registerX>` is the name of an individual register within that block (e.g. "ODR").  Either a single `<register1>` or multiple `<registerX>` may be specified ⁠— in the latter case the register with the least significant bit field (for addressing the array as a whole) must be specified first, with the other registers following in increasing order of significance in the array.

* `fields_per_reg` is a positive integer value that specifies the number of uniformly sized bit fields contained in each register.

* `bits_per_field` is a positive integer value that specifies the size of each bit field within each register.

* By definition for a 32 bit register, `fields_per_reg` * `bits_per_field` must be less than or equal to 32.

Examples:

    pa_moder = iol.RegArr("GPIOA.MODER", 16, 2)
    pa_afr = iol.RegArr("GPIOA.AFR0,AFR1", 8, 4)
    adc1_smpr = iol.RegArr("ADC1.SMPR2,SMPR1", 10, 3)

## Methods for `iol.RegArr`

### `iol.RegArr[bit]`for read

Read a bit field in the array of STM32 registers associated with the `iol.RegArr` object assigned to `reg_arr_obj`:
 
    bit_field_value = reg_arr_obj[index]

* `index` is the positive integer (or zero) index of the bit field to be read from the array of STM32 registers (starting from zero).  It must be within the range of zero to the total number  **minus one** of fields in the array (i.e. `fields_per_reg` * number of registers)  defined for the `iol.RegArr` object when it was constructed.

* The return value (`bit_field_value`) will be a positive integer (or zero) within the range of the number of bits for the bit field defined by `bits_per_field` when the `iol.RegArr` object was constructed (i.e. 0-7 for a 3 bit field).

### `iol.RegArr[bit]`for write

Write to a bit field in the array of STM32 registers associated with the `iol.RegArr` object assigned to `reg_arr_obj`:
 
    reg_arr_obj[index] = bit_field_value

* `index` is the positive integer (or zero) index of the bit field to be read from the array of STM32 registers (starting from zero).  It must be within the range of zero to the total number  **minus one** of fields in the array (i.e. `fields_per_reg` * number of registers)  defined for the `iol.RegArr` object when it was constructed.

* `bit_field_value` must be a positive integer (or zero) within the range of the number of bits for the bit field defined by `bits_per_field` when the `iol.RegArr` object was constructed (i.e. 0-7 for a 3 bit field).

### `iol.RegArr.print()`

Print in human-friendly format the array of values held in the STM32 registers associated with the `iol.RegArr` object assigned to `reg_arr_obj`:
 
    reg_arr_obj.print()
    
*This method is useful for debugging problems with "bare-metal" code in which it is necessary to locate the correct bit field within an array of STM32 peripheral registers and identify its value at a hexadecimal level or an individual bit level.*

### `iol.RegArr.dump()`

Dump in human-friendly format the contents of all of the STM32 registers associated with the `iol.RegArr` object assigned to `reg_arr_obj`:
 
    reg_arr_obj.dump()
    
The output of `dump()` is an iteration of the `print()` output for each of the `iol.Reg` registers specified when constructing the `iol.RegArr` object.

# Class `iol.Mem` ⁠— low-level I/O access to a single STM32 memory location

The `iol.Mem` class is the base class for `iol.Reg` that enables any single STM32 memory location (not necessarily a peripheral register) to be manipulated in a more fluent way from Micropython.  `iol.Mem` provides most of the methods to the derived [`iol.Reg`](https://github.com/Chapmip/micropython-stm32-iol#methods-for-iolreg) class.

## Constructor for `iol.Mem`

Create a new `iol.Mem` object corresponding to an STM32 memory location and assign it to `mem_obj`:

    mem_obj = iol.Mem(addr, size=32)

* `addr` is a positive integer (or zero) corresponding to the absolute address of the STM32 memory location of interest.  The address must satisfy the alignment requirements for the value of `size` (see below) ⁠— for example, 32-bit words must be aligned to a 32-bit word boundary, or else read and write operations will fail.

* `size` is an optional integer value that specifies the size of the memory location (32, 16 or 8 bits), with a default of 32 bits.

Examples:

    mem_32 = iol.Mem(0x40020014)
    mem_16 = iol.Mem(0x4002001A, 16)

## Methods for `iol.Mem`

`iol.Mem` provides all of the methods **except** `dump()`to the `iol.Reg` class.  Please therefore refer to the [documentation on `iol.Reg`](https://github.com/Chapmip/micropython-stm32-iol#methods-for-iolreg) for details of applicable methods. 

# Gotchas!

I'm documenting here any hazards that I encounter whilst using the `iol.py` module.

## 1. Remember to use `[:]` or `read/write` methods!

The following code will not work as expected:

    pa_odr = iol.Reg("GPIOA.ODR")
    pa_odr = 0x55

It will not change the value of the GPIOA ODR register.  Instead, it will change `pa_odr` from a reference to the `iol.Reg` object to an integer with a value of 0x55.

Instead, use one of the following:

    pa_odr[:] = 0x55
    pa_odr.write(0x55)

Similarly, the following code will not work as expected:

    pa_idr = iol.Reg("GPIOA.IDR")
    value = pa_odr
    
It will not read the state of GPIOA IDR register.  Instead, it will set up `value` as another reference to the `iol.Reg` object associated with pa_idr.

Instead, use one of the following:

    value = pa_idr[:]
    value = pa_idr.read()

# References

* [STM32F405 Data Sheet](https://www.st.com/resource/en/datasheet/dm00037051.pdf)
* [STM32F405 Reference Manual](https://www.st.com/resource/en/reference_manual/dm00031020-stm32f405-415-stm32f407-417-stm32f427-437-and-stm32f429-439-advanced-arm-based-32-bit-mcus-stmicroelectronics.pdf)
* [STM32 Cortex®-M4 Programming Manual](https://www.st.com/resource/en/programming_manual/dm00046982-stm32-cortexm4-mcus-and-mpus-programming-manual-stmicroelectronics.pdf)
* [MicroPython documentation](https://docs.micropython.org/en/latest/)
* [Pyboard v1.1 documentation](https://docs.micropython.org/en/latest/pyboard/quickref.html)
* [Serial Term for Chrome OS (by Ganehag)](https://chrome.google.com/webstore/detail/serial-term/fnjkimblohniildfepjhejeppenokhie)
* [Separate repository for code examples using `iol.py`](https://github.com/Chapmip/micropython-stm32-examples)

