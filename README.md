# The `iol.py` module

**Note: This document is currently being created and so is not yet suitable for reference.**

## Quick summary

* Low-level I/O classes to facilitate "bare-metal" access in Micropython to STM32 memory locations and peripheral registers (for learning purposes)

* Created on a Pyboard (PYB) v1.1 (with STM32F405RGT6 microcontroller) but should be readily adaptable to other STM32 Micropython builds

## History

I created the `iol.py` module when I wanted to experiment with "bare metal" access to STM32 peripheral registers on a Pyboard v1.1.  I had obtained the Udemy course [*"Embedded Systems Bare-Metal Programming Ground Up™ (STM32)"*](https://www.udemy.com/course/embedded-systems-bare-metal-programming/) but was unable to use the examples directly as I didn't have a Windows PC on which to run the required Keil uVision environment.  I therefore chose to create classes to simulate "bare metal" access in Micropython rather than C.

I wasn't sure whether the Micropython system footprint would get in the way of "bare metal" accesses to peripheral registers, but I didn't find this generally to be the case.  In most cases, I have been able to work around issues of contention by reading carefully the Micropython documentation and avoiding a few on-chip peripheral functions that are dedicated to Micropython.

Inevitably, code written in Micropython will run considerably slower than C code.  I only found this to be a problem, though, during one experiment with the SPI bus, in which Micropython code is unable to keep up with the high speed of the bus (up to 21 MHz).  Even in this case, I was able to work around this limitation by re-writing the critical section of code using inline assembler code.

My code examples inspired by the Udemy course can be found in my separate repository [here](https://github.com/Chapmip/micropython-stm32-examples).

## Getting started

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

##  Classes and methods in `iol.py`

The source code for `iol.py` can be viewed and downloaded [`here`](/iol.py).  The following text describes further the classes and associated methods exposed by the module.

### Class `iol.Reg` ⁠— low-level I/O access to a single STM32 peripheral register:

The `iol.Reg` class enables a single STM32 peripheral register to be manipulated in a more fluent way from Micropython.

#### Constructor for `iol.Reg`

Create a new `iol.Reg` object corresponding to an STM32 register and assign it to `reg_obj`:

    reg_obj = iol.Reg(label, size=32)

* `label` is a string of the form `"<base>.<register>"`, where `<base>` is the name of an STM32 peripheral block (e.g. "GPIOA") and `<register>` is the name of an individual register within that block (e.g. "ODR").

* `size` is an optional integer value that specifies the size of the register (32, 16 or 8 bits), overriding the inference built in to the module (usually 32 bits).  Use this feature with caution, as some STM32 registers can only be accessed in larger sizes (check the STM32 data sheet and reference manuals for specifics — see references later).

Examples:

    pa_odr = iol.Reg("GPIOA.ODR")
    t2_psc = iol.Reg("TIM2.PSC", 16)

Notes:

The STM32 `<base>` and `<register>` values are derived from the Micropython `stm` module, which is included in compatible builds.  A completes list of these values can be obtained by invoking the module-level method `iol.list_names()`.

The `iol.py` module also handles a few special cases in which the `stm` manual falls short (for example, the common registers for ADC1,2,3 which are not defined in the `stm` module but can be accessed using the `label` strings "ADC.CSR", "ADC.CCR" and "ADC.CDR").

#### Methods for `iol.Reg`

Read the current value held in the STM32 register associated with the `iol.Reg` object assigned to `reg_obj`.
 
    value = reg_obj.read(*, size=None)
    
* `size` is an optional integer value (not valid as a positional parameter ⁠— must be assigned explictly by name) that specifies the bit width of the read operation (32, 16 or 8 bits), overriding the inference built in to the module (usually 32 bits).  Refer to the warning in the constructor section about overriding the default read size.

Note that the alternative terser syntax `value = reg_obj[:]` can also be used for this operation.

Write a value to the STM32 register associated with the `iol.Reg` object assigned to `reg_obj`.
 
    reg_obj.write(value, *, size=None)

* `value` is the positive integer (or zero) value to be written into the STM32 register.  It must be within the range of the bit width defined by the explicit `size` parameter (see below) if included, and the bit width defined for the `iol.Reg` object when it was constructed.
    
* `size` is an optional integer value (not valid as a positional parameter ⁠— must be assigned explictly by name) that specifies the bit width of the read operation (32, 16 or 8 bits), overriding the inference built in to the module (usually 32 bits).  Refer to the warning in the constructor section about overriding the default read size.

It may also be possible to use the alternative terser syntax `reg_obj[:] = value` for this operation.  Note, however, that the latter option causes a read operation to be made to the STM32 register before the write is carried out.  If there is a risk that this may cause unwanted side-effects, then the `reg_obj.write()` method (which only leads to a write operation) is a safer option.

### More to be added here...

## References

* [STM32F405 Data Sheet](https://www.st.com/resource/en/datasheet/dm00037051.pdf)
* [STM32F405 Reference Manual](https://www.st.com/resource/en/reference_manual/dm00031020-stm32f405-415-stm32f407-417-stm32f427-437-and-stm32f429-439-advanced-arm-based-32-bit-mcus-stmicroelectronics.pdf)
* [STM32 Cortex®-M4 Programming Manual](https://www.st.com/resource/en/programming_manual/dm00046982-stm32-cortexm4-mcus-and-mpus-programming-manual-stmicroelectronics.pdf)
* [MicroPython documentation](https://docs.micropython.org/en/latest/)
* [Pyboard v1.1 documentation](https://docs.micropython.org/en/latest/pyboard/quickref.html)
* [Serial Term for Chrome OS (by Ganehag)](https://chrome.google.com/webstore/detail/serial-term/fnjkimblohniildfepjhejeppenokhie)
* [Separate repository for code examples using `iol.py`](https://github.com/Chapmip/micropython-stm32-examples)

