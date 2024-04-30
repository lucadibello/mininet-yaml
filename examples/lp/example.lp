Maximize
        obj: min_r

Subject To
        r_A: min_r - dem_h1 <= 0
        r_B: min_r - dem_h4 <= 0
        r_C: min_r - dem_h3 <= 0
        dem_h1_h4_flow_r2_r4: dem_h1 - x_r2_r4_eth0 = 0
        dem_h1_h4_flow_r3_r4: dem_h1 - x_r3_r4_eth1 = 0
        dem_h1_h4_flow_h4_r4: dem_h1 - x_h4_r4_eth2 = 0
        dem_h1_h4_flow_r1_r3: dem_h1 - x_r1_r3_eth0 = 0
        dem_h1_h4_flow_r2_r3: dem_h1 - x_r2_r3_eth1 = 0
        dem_h1_h4_flow_r4_r3: dem_h1 - x_r4_r3_eth2 = 0
        dem_h1_h4_flow_h3_r3: dem_h1 - x_h3_r3_eth3 = 0
        dem_h1_h4_flow_r3_h3: dem_h1 - x_r3_h3_eth0 = 0
        dem_h1_h4_flow_s0_r1: dem_h1 - x_s0_r1_eth2 = 0
        dem_h1_h4_flow_r2_r1: dem_h1 - x_r2_r1_eth0 = 0
        dem_h1_h4_flow_r3_r1: dem_h1 - x_r3_r1_eth1 = 0
        dem_h1_h4_flow_h1_s0: dem_h1 - x_h1_s0_eth0 = 0
        dem_h1_h4_flow_r1_s0: dem_h1 - x_r1_s0_eth2 = 0
        dem_h1_h4_flow_h2_s0: dem_h1 - x_h2_s0_eth1 = 0
        dem_h1_h4_flow_s0_h2: dem_h1 - x_s0_h2_eth0 = 0
        dem_h1_h4_flow_r1_r2: dem_h1 - x_r1_r2_eth0 = 0
        dem_h1_h4_flow_r3_r2: dem_h1 - x_r3_r2_eth1 = 0
        dem_h1_h4_flow_r4_r2: dem_h1 - x_r4_r2_eth2 = 0
        dem_h4_h2_flow_h1_s0: dem_h4 - x_h1_s0_eth0 = 0
        dem_h4_h2_flow_r1_s0: dem_h4 - x_r1_s0_eth2 = 0
        dem_h4_h2_flow_h2_s0: dem_h4 - x_h2_s0_eth1 = 0
        dem_h4_h2_flow_s0_r1: dem_h4 - x_s0_r1_eth2 = 0
        dem_h4_h2_flow_r2_r1: dem_h4 - x_r2_r1_eth0 = 0
        dem_h4_h2_flow_r3_r1: dem_h4 - x_r3_r1_eth1 = 0
        dem_h4_h2_flow_r1_r3: dem_h4 - x_r1_r3_eth0 = 0
        dem_h4_h2_flow_r2_r3: dem_h4 - x_r2_r3_eth1 = 0
        dem_h4_h2_flow_r4_r3: dem_h4 - x_r4_r3_eth2 = 0
        dem_h4_h2_flow_h3_r3: dem_h4 - x_h3_r3_eth3 = 0
        dem_h4_h2_flow_r3_h3: dem_h4 - x_r3_h3_eth0 = 0
        dem_h4_h2_flow_r2_r4: dem_h4 - x_r2_r4_eth0 = 0
        dem_h4_h2_flow_r3_r4: dem_h4 - x_r3_r4_eth1 = 0
        dem_h4_h2_flow_h4_r4: dem_h4 - x_h4_r4_eth2 = 0
        dem_h4_h2_flow_r1_r2: dem_h4 - x_r1_r2_eth0 = 0
        dem_h4_h2_flow_r3_r2: dem_h4 - x_r3_r2_eth1 = 0
        dem_h4_h2_flow_r4_r2: dem_h4 - x_r4_r2_eth2 = 0
        dem_h4_h2_flow_s0_h1: dem_h4 - x_s0_h1_eth0 = 0
        dem_h3_h4_flow_r2_r4: dem_h3 - x_r2_r4_eth0 = 0
        dem_h3_h4_flow_r3_r4: dem_h3 - x_r3_r4_eth1 = 0
        dem_h3_h4_flow_h4_r4: dem_h3 - x_h4_r4_eth2 = 0
        dem_h3_h4_flow_r1_r3: dem_h3 - x_r1_r3_eth0 = 0
        dem_h3_h4_flow_r2_r3: dem_h3 - x_r2_r3_eth1 = 0
        dem_h3_h4_flow_r4_r3: dem_h3 - x_r4_r3_eth2 = 0
        dem_h3_h4_flow_h3_r3: dem_h3 - x_h3_r3_eth3 = 0
        dem_h3_h4_flow_s0_r1: dem_h3 - x_s0_r1_eth2 = 0
        dem_h3_h4_flow_r2_r1: dem_h3 - x_r2_r1_eth0 = 0
        dem_h3_h4_flow_r3_r1: dem_h3 - x_r3_r1_eth1 = 0
        dem_h3_h4_flow_h1_s0: dem_h3 - x_h1_s0_eth0 = 0
        dem_h3_h4_flow_r1_s0: dem_h3 - x_r1_s0_eth2 = 0
        dem_h3_h4_flow_h2_s0: dem_h3 - x_h2_s0_eth1 = 0
        dem_h3_h4_flow_s0_h2: dem_h3 - x_s0_h2_eth0 = 0
        dem_h3_h4_flow_s0_h1: dem_h3 - x_s0_h1_eth0 = 0
        dem_h3_h4_flow_r1_r2: dem_h3 - x_r1_r2_eth0 = 0
        dem_h3_h4_flow_r3_r2: dem_h3 - x_r3_r2_eth1 = 0
        dem_h3_h4_flow_r4_r2: dem_h3 - x_r4_r2_eth2 = 0

Bounds
        x_s0_r1_eth2 >= 0
        x_h4_r4_eth2 >= 0
        0 <= x_r1_r2_eth0 <= 3
        x_s0_h1_eth0 <= 0
        -3 <= x_r2_r1_eth0 <= 0
        x_h1_s0_eth0 >= 0
        0 <= x_r1_r3_eth0 <= 10
        x_s0_h2_eth0 <= 0
        -10 <= x_r3_r1_eth1 <= 0
        x_h2_s0_eth1 >= 0
        0 <= x_r2_r4_eth0 <= 10
        -10 <= x_r4_r2_eth2 <= 0
        0 <= x_r2_r3_eth1 <= 8
        -8 <= x_r3_r2_eth1 <= 0
        x_r3_h3_eth0 <= 0
        x_h3_r3_eth3 >= 0
        0 <= x_r3_r4_eth1 <= 10
        -10 <= x_r4_r3_eth2 <= 0
        x_r1_s0_eth2 <= 0
        x_r4_h4_eth0 <= 0
        0 <= dem_h1 <= 10
        0 <= dem_h4 <= 2
        0 <= dem_h3 <= 15
End