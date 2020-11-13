DDR3 test
=========

notes
-----

The part works via MiG in Vivado, but not in LiteX yet. This is an attempt to use LiteX to run the DDR3

vivado settings (picture): https://photos.app.goo.gl/qJ9LKPQcdtpj1TLN7

vivado xdc files from MiG are in the vivado folder

sys_clk_freq is 83.333 MHz so that 83.333 MHz * 4 = 333.333 MHz * 2 (DDR) = 666.666 MT/s, which is the maximum supported data rate for the -1 speed grade FPGA for DDR3L (1.35 V).

The memory chip on the Au is the AS4C128M16D3LB-12BCN (a DDR3L-1600 module)

au schematic: https://cdn.shopify.com/s/files/1/2702/8766/files/alchitry_au_sch.pdf

datasheet: https://www.alliancememory.com/wp-content/uploads/pdf/ddr3/Alliance%20Memory_2G%20128Mx16%20AS4C128M16D3LB-12BCN%20v1.0%20March%202016.pdf

DDR3 module class is in my fork of litedram: https://github.com/teknoman117/litedram/commit/42c30dd2ab13a4af515a0890c779a39fd8760d9a
