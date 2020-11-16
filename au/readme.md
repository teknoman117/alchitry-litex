Au
====

counter
-------
displays binary counter on user leds

ddr3
-----
creates a LiteX mini-soc with a wishbone bridge such that ddr3 is accessible via wishbone-tool

ddr3-soc
---------
creates a LiteX soc using the ddr3

Notes
-----
sys_clk_freq is 83.333 MHz so that 83.333 MHz * 4 = 333.333 MHz * 2 (DDR) = 666.666 MT/s, which is the maximum supported data rate for the -1 speed grade FPGA for DDR3L (1.35 V).

The memory chip on the Au is the AS4C128M16D3LB-12BCN (a DDR3L-1600 module)

au schematic: https://cdn.shopify.com/s/files/1/2702/8766/files/alchitry_au_sch.pdf

datasheet: https://www.alliancememory.com/wp-content/uploads/pdf/ddr3/Alliance%20Memory_2G%20128Mx16%20AS4C128M16D3LB-12BCN%20v1.0%20March%202016.pdf

DDR3 module class is in my fork of litedram: https://github.com/teknoman117/litedram/commit/ca83330897475ad6ba9525864e56a0e2b044c7f8
