#!/usr/bin/env python3

from migen import *

from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform

_io = [
    # Clk / Rst
    ("clk50", 0, Pins("P56"), IOStandard("LVTTL")),
    ("cpu_reset", 0, Pins("P38"), IOStandard("LVTTL")),

    # Leds
    ("user_led", 0, Pins("P134"), IOStandard("LVTTL")),
    ("user_led", 1, Pins("P133"), IOStandard("LVTTL")),
    ("user_led", 2, Pins("P132"), IOStandard("LVTTL")),
    ("user_led", 3, Pins("P131"), IOStandard("LVTTL")),
    ("user_led", 4, Pins("P127"), IOStandard("LVTTL")),
    ("user_led", 5, Pins("P126"), IOStandard("LVTTL")),
    ("user_led", 6, Pins("P124"), IOStandard("LVTTL")),
    ("user_led", 7, Pins("P123"), IOStandard("LVTTL")),

    # uart
    ("serial", 0,
        Subsignal("tx", Pins("P59")),
        Subsignal("rx", Pins("P55")),
        IOStandard("LVTTL")
    ),

    # avr signals
    ("tx_busy", 0, Pins("P39"), IOStandard("LVTTL"))
]

# Platform -----------------------------------------------------------------------------------------

class Platform(XilinxPlatform):
    default_clk_name   = "clk50"
    default_clk_period = 1e9/50e6

    def __init__(self):
        XilinxPlatform.__init__(self, "xc6slx9-2-tqg144", _io)
        self.toolchain.additional_commands = ["write_bitstream -force -bin_file {build_name}"]

    def do_finalize(self, fragment):
        XilinxPlatform.do_finalize(self, fragment)
        self.add_period_constraint(self.lookup_request("clk50", loose=True), 1e9/50e6)

# Design -------------------------------------------------------------------------------------------

# Create our platform (fpga interface)
platform = Platform()
user_leds = Cat(*[platform.request("user_led", i) for i in range(8)])

# Create our module (fpga description)
module = Module()

# Create a counter and blink a led
counter = Signal(29)
module.comb += user_leds.eq(counter[-8:])
module.sync += counter.eq(counter + 1)

# Build --------------------------------------------------------------------------------------------

platform.build(module)