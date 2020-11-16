#!/usr/bin/env python3

from migen import *

from litex.build.io import DDROutput
from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform

from litex.soc.integration.soc_core import *
from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *

from litex.soc.cores.clock import S6PLL
from litex.soc.cores.uart import UARTWishboneBridge
from litex.soc.cores import dna

from litedram.modules import MT48LC32M8
from litedram.phy import HalfRateGENSDRPHY, GENSDRPHY

from ios import Led

import os
import argparse

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
    ("tx_busy", 0, Pins("P39"), IOStandard("LVTTL")),
    ("cclk", 0, Pins("P70"), IOStandard("LVTTL")),

    # sdram (HDMI shield)
    ("sdram_clock", 0, Pins("P29"), IOStandard("LVTTL"), Misc("SLEW=FAST")),
    ("sdram", 0,
        Subsignal("a", Pins("P101 P102 P104 P105 P5 P6 P7 P8 P9 P10 P88 P27 P26")),
        Subsignal("dq", Pins("P75 P78 P79 P80 P34 P35 P40 P41")),
        Subsignal("ba", Pins("P85 P87")),
        Subsignal("dm", Pins("P74")),
        Subsignal("ras_n", Pins("P83")),
        Subsignal("cas_n", Pins("P82")),
        Subsignal("we_n", Pins("P81")),
        Subsignal("cs_n", Pins("P84")),
        Subsignal("cke", Pins("P30")),
        IOStandard("LVTTL"),
        Misc("SLEW = FAST")
    ),
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

# CRG ----------------------------------------------------------------------------------------------

class _CRG(Module):
    def __init__(self, platform, sys_clk_freq):
        self.clock_domains.cd_sys      = ClockDomain()
        self.clock_domains.cd_sys_ps   = ClockDomain(reset_less=True)
        #self.clock_domains.cd_sys2x    = ClockDomain()
        #self.clock_domains.cd_sys2x_ps = ClockDomain(reset_less=True)

        # PLL
        self.submodules.pll = pll = S6PLL(speedgrade=-2)
        self.comb += pll.reset.eq(~platform.request("cpu_reset") | ~platform.request("cclk"))
        pll.register_clkin(platform.request("clk50"), 50e6)
        pll.create_clkout(self.cd_sys,      sys_clk_freq)
        pll.create_clkout(self.cd_sys_ps,   sys_clk_freq, phase=90)
        #pll.create_clkout(self.cd_sys2x,    2*sys_clk_freq)
        #pll.create_clkout(self.cd_sys2x_ps, 2*sys_clk_freq, phase=90)

        # SDRAM clock
        self.specials += DDROutput(1, 0, platform.request("sdram_clock"), ClockSignal("sys_ps"))
        #self.specials += DDROutput(1, 0, platform.request("sdram_clock"), ClockSignal("sys2x_ps"))

# SoC ----------------------------------------------------------------------------------------------

class BaseSoC(SoCMini):
    def __init__(self, sys_clk_freq=int(66666666), **kwargs):
        platform = Platform()

        SoCMini.__init__(self, platform, sys_clk_freq,
            csr_data_width=32,
            ident="Mojo V3 SoC",
            ident_version=True)

        self.submodules.crg = _CRG(platform, sys_clk_freq)

        # SDR SDRAM --------------------------------------------------------------------------------
        self.submodules.sdrphy = GENSDRPHY(platform.request("sdram"))
        #self.submodules.sdrphy = HalfRateGENSDRPHY(platform.request("sdram"))
        self.add_sdram("sdram",
            phy                     = self.sdrphy,
            module                  = MT48LC32M8(sys_clk_freq, "1:1"),
            #module                  = MT48LC32M8(sys_clk_freq, "1:2"),
            origin                  = self.mem_map["main_ram"],
            size                    = kwargs.get("max_sdram_size", 0x2000000),
            l2_cache_size           = kwargs.get("l2_size", 8192),
            l2_cache_min_data_width = kwargs.get("min_l2_data_width", 128),
            l2_cache_reverse        = True
        )

        # No CPU, use Serial to control Wishbone bus
        self.submodules.serial_bridge = UARTWishboneBridge(platform.request("serial"), sys_clk_freq, baudrate=500000)
        self.add_wb_master(self.serial_bridge.wishbone)

        # FPGA identification
        self.submodules.dna = dna.DNA()
        self.add_csr("dna")

        # Led
        user_leds = Cat(*[platform.request("user_led", i) for i in range(8)])
        self.submodules.leds = Led(user_leds)
        self.add_csr("leds")

soc = BaseSoC()

# Build --------------------------------------------------------------------------------------------

builder = Builder(soc, output_dir="build", csr_csv="test/csr.csv")
builder.build(build_name="mojov3")
