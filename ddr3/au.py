#!/usr/bin/env python3

from migen import *

from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform

from litex.soc.integration.soc_core import *
from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *

from litex.soc.cores.clock import *
from litex.soc.cores.uart import UARTWishboneBridge
from litex.soc.cores import dna

from litedram.modules import AS4C128M16
from litedram.phy import s7ddrphy

from ios import Led

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

    # ddr3
    ("ddram", 0,
        Subsignal("a", Pins(
            "F12 G16 G15 E16 H11 G12 H16",
            "H12 J16 H13 E12 H14 F13 J15"),
            IOStandard("SSTL135")),
        Subsignal("ba",    Pins("E13 F15 E15"), IOStandard("SSTL135")),
        Subsignal("ras_n", Pins("D11"),  IOStandard("SSTL135")),
        Subsignal("cas_n", Pins("D14"),  IOStandard("SSTL135")),
        Subsignal("we_n",  Pins("E11"),  IOStandard("SSTL135")),
        Subsignal("dm", Pins("A14 C9"), IOStandard("SSTL135")),
        Subsignal("dq", Pins(
            "A13 B16 B14 C11 C13 C16 C12 C14",
            "D8  B11 C8  B10 A12 A8  B12 A9"),
            IOStandard("SSTL135"),
            Misc("IN_TERM=UNTUNED_SPLIT_50")),
        Subsignal("dqs_p",
            Pins("B15 B9"),
            IOStandard("DIFF_SSTL135"),
            Misc("IN_TERM=UNTUNED_SPLIT_50")),
        Subsignal("dqs_n",
            Pins("A15 A10"),
            IOStandard("DIFF_SSTL135"),
            Misc("IN_TERM=UNTUNED_SPLIT_50")),
        Subsignal("clk_p", Pins("G14"), IOStandard("DIFF_SSTL135")),
        Subsignal("clk_n", Pins("F14"), IOStandard("DIFF_SSTL135")),
        Subsignal("cke",   Pins("D15"), IOStandard("SSTL135")),
        Subsignal("odt",   Pins("G11"), IOStandard("SSTL135")),
        Subsignal("cs_n",  Pins("D16"), IOStandard("SSTL135")),
        Subsignal("reset_n", Pins("D13"), IOStandard("SSTL135")),
        Misc("SLEW=FAST"),
    ),
]

# Platform -----------------------------------------------------------------------------------------

class Platform(XilinxPlatform):
    default_clk_name   = "clk100"
    default_clk_period = 1e9/100e6

    def __init__(self):
        XilinxPlatform.__init__(self, "xc7a35t-ftg256-1", _io, toolchain="vivado")
        self.add_platform_command("set_property INTERNAL_VREF  0.675 [get_iobanks 15]")
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

# CRG ----------------------------------------------------------------------------------------------

class _CRG(Module):
    def __init__(self, platform, sys_clk_freq):
        self.clock_domains.cd_sys       = ClockDomain()
        self.clock_domains.cd_sys4x     = ClockDomain(reset_less=True)
        self.clock_domains.cd_sys4x_dqs = ClockDomain(reset_less=True)
        self.clock_domains.cd_clk200    = ClockDomain()

        self.submodules.pll = pll = S7PLL(speedgrade=-1)
        self.comb += pll.reset.eq(~platform.request("cpu_reset"))
        pll.register_clkin(platform.request("clk100"), 100e6)
        pll.create_clkout(self.cd_sys,       sys_clk_freq)
        pll.create_clkout(self.cd_sys4x,     4*sys_clk_freq)
        pll.create_clkout(self.cd_sys4x_dqs, 4*sys_clk_freq, phase=90)
        pll.create_clkout(self.cd_clk200,    200e6)

        self.submodules.idelayctrl = S7IDELAYCTRL(self.cd_clk200)

# SoC ----------------------------------------------------------------------------------------------

class BaseSoC(SoCMini):
    def __init__(self, sys_clk_freq=int(83333333), **kwargs):
        platform = Platform()

        # SoCMini
        SoCMini.__init__(self, platform, sys_clk_freq, csr_data_width=32,
            ident="Alchitry Au Mini Soc", ident_version=True)

        self.submodules.crg = _CRG(platform, sys_clk_freq)
        self.submodules.ddrphy = s7ddrphy.A7DDRPHY(platform.request("ddram"),
            memtype      = "DDR3",
            nphases      = 4,
            sys_clk_freq = sys_clk_freq)
        self.add_csr("ddrphy")
        self.add_sdram("sdram",
            phy                     = self.ddrphy,
            module                  = AS4C128M16(sys_clk_freq, "1:4"),
            origin                  = self.mem_map["main_ram"],
            size                    = kwargs.get("max_sdram_size", 0x10000000),
            l2_cache_size           = kwargs.get("l2_size", 8192),
            l2_cache_min_data_width = kwargs.get("min_l2_data_width", 128),
            l2_cache_reverse        = True
        )

        # No CPU, use Serial to control Wishbone bus
        self.submodules.serial_bridge = UARTWishboneBridge(platform.request("serial"), sys_clk_freq)
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
builder.build(build_name="ddr3")
