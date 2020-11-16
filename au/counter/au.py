#!/usr/bin/env python3

from migen import *

from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform

_io = [
    # Clk / Rst
    ("clk100", 0, Pins("N14"), IOStandard("LVCMOS33")),
    ("cpu_reset", 0, Pins("P6"), IOStandard("LVCMOS33")),

    # Leds
    ("user_led", 0, Pins("K13"), IOStandard("LVCMOS33")),
    ("user_led", 1, Pins("K12"), IOStandard("LVCMOS33")),
    ("user_led", 2, Pins("L14"), IOStandard("LVCMOS33")),
    ("user_led", 3, Pins("L13"), IOStandard("LVCMOS33")),
    ("user_led", 4, Pins("M16"), IOStandard("LVCMOS33")),
    ("user_led", 5, Pins("M14"), IOStandard("LVCMOS33")),
    ("user_led", 6, Pins("M12"), IOStandard("LVCMOS33")),
    ("user_led", 7, Pins("N16"), IOStandard("LVCMOS33")),

    # uart
    ("serial", 0,
        Subsignal("tx", Pins("P16")),
        Subsignal("rx", Pins("P15")),
        IOStandard("LVCMOS33")
    ),
]

# Platform -----------------------------------------------------------------------------------------

class Platform(XilinxPlatform):
    default_clk_name   = "clk100"
    default_clk_period = 1e9/100e6

    def __init__(self):
        XilinxPlatform.__init__(self, "xc7a35t-ftg256-1", _io, toolchain="vivado")
        self.toolchain.bitstream_commands = [
            "set_property BITSTREAM.GENERAL.COMPRESS TRUE [current_design]",
            "set_property BITSTREAM.CONFIG.CONFIGRATE 33 [current_design]",
            "set_property CONFIG_VOLTAGE 3.3 [current_design]",
            "set_property CFGBVS VCCO [current_design]",
            "set_property BITSTREAM.CONFIG.SPI_32BIT_ADDR NO [current_design]",
            "set_property BITSTREAM.CONFIG.SPI_BUSWIDTH 1 [current_design]",
            "set_property BITSTREAM.CONFIG.SPI_FALL_EDGE YES [current_design]",
        ]
        self.toolchain.additional_commands = ["write_bitstream -force -bin_file {build_name}"]

    def do_finalize(self, fragment):
        XilinxPlatform.do_finalize(self, fragment)
        self.add_period_constraint(self.lookup_request("clk100", loose=True), 1e9/100e6)

# Design -------------------------------------------------------------------------------------------

# Create our platform (fpga interface)
platform = Platform()
user_leds = Cat(*[platform.request("user_led", i) for i in range(8)])

# Create our module (fpga description)
module = Module()

# Create a counter and blink a led
counter = Signal(30)
module.comb += user_leds.eq(counter[-8:])
module.sync += counter.eq(counter + 1)

# Build --------------------------------------------------------------------------------------------

platform.build(module)