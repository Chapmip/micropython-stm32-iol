# Work in progress...

**This document is currently being created and so is not yet suitable for reference.**

### General description of `iol.py` module

* Low-level I/O classes to facilitate "bare-metal" access in Micropython to STM32 memory locations and device registers (for learning purposes).

* Created on a Pyboard (PYB) v1.1 (with STM32F405RGT6 microcontroller) but should be readily adaptable to other STM32 Micropython builds.

### Photos to support `iol.py` module

![Chrome OS Serial Terminal settings for Pyboard](/photos/Chrome%20OS%20Serial%20Terminal%20settings%20for%20Pyboard.png?raw=true "Chrome OS Serial Terminal settings for Pyboard")

![Using iol module to access ports directly](/photos/Using%20iol%20module%20to%20access%20ports%20directly.png?raw=true "Using iol module to access ports directly")

### References

* [STM32F405 Data Sheet](https://www.st.com/resource/en/datasheet/dm00037051.pdf)
* [STM32F405 Reference Manual](https://www.st.com/resource/en/reference_manual/dm00031020-stm32f405-415-stm32f407-417-stm32f427-437-and-stm32f429-439-advanced-arm-based-32-bit-mcus-stmicroelectronics.pdf)
* [STM32 Cortex®-M4 Programming Manual](https://www.st.com/resource/en/programming_manual/dm00046982-stm32-cortexm4-mcus-and-mpus-programming-manual-stmicroelectronics.pdf)
* [MicroPython documentation](https://docs.micropython.org/en/latest/)
* [Pyboard v1.1 documentation](https://docs.micropython.org/en/latest/pyboard/quickref.html)
* [Serial Term for Chrome OS (by Ganehag)](https://chrome.google.com/webstore/detail/serial-term/fnjkimblohniildfepjhejeppenokhie)

### Low-level I/O code

* [My `iol.py` module](/iol.py)
