Maximize
        obj: min_r

Subject To
        \ Set min_r as the minimum of all effectiveness ratios
        x_min: min_r - ratio_x <= 0
        y_min: min_r - ratio_y <= 0
        z_min: min_r - ratio_z <= 0

        \ Define how the ratio is computed for each flow
        x_flow: 10 x - ratio_x = 0
        y_flow: 2 y - ratio_y = 0
        z_flow: 15 z - ratio_z = 0

        \ Define default routes for source and destination of flow x
        x_src: x_h1_s0_eth0 = 1
        x_dst: x_r4_h4_eth0 = 1

        \ Define default routes for source and destination of flow y
        y_src: y_h4_r4_eth2 = 1
        y_dst: y_s0_h2_eth0 = 1

        \ Define default routes for source and destination of flow z
        z_src: z_h3_r3_eth3 = 1
        z_dst: z_r4_h4_eth0 = 1

        \ Provide mutual exclusion on INPUT routes on all elements of flow x
        x_in_r1: x_s0_r1_eth2 + x_r2_r1_eth0 + x_r3_r1_eth1 <= 1
        x_in_r2: x_r3_r2_eth1 + x_r1_r2_eth0 + x_r4_r2_eth2 <= 1
        x_in_r3: x_r2_r3_eth1 + x_h3_r3_eth3 + x_r4_r3_eth2 + x_r1_r3_eth0 <= 1
        x_in_r4: x_r3_r4_eth1 + x_h4_r4_eth2 + x_r2_r4_eth0 <= 1

        \ Provide mutual exclusion on OUTPUT routes on all elements of flow x
        x_out_r1: x_r1_s0_eth2 + x_r1_r2_eth0 + x_r1_r3_eth0 <= 1
        x_out_r2: x_r2_r1_eth0 + x_r2_r4_eth0 + x_r2_r3_eth1 <= 1
        x_out_r3: x_r3_r1_eth1 + x_r3_r2_eth1 + x_r3_h3_eth0 + x_r3_r4_eth1 <= 1
        x_out_r4: x_r4_r2_eth2 + x_r4_r3_eth2 + x_r4_h4_eth0 <= 1

        \ Provide mutual exclusion on INPUT routes on all elements of flow y
        y_in_r1: y_s0_r1_eth2 + y_r2_r1_eth0 + y_r3_r1_eth1 <= 1
        y_in_r2: y_r3_r2_eth1 + y_r1_r2_eth0 + y_r4_r2_eth2 <= 1
        y_in_r3: y_r2_r3_eth1 + y_h3_r3_eth3 + y_r4_r3_eth2 + y_r1_r3_eth0 <= 1
        y_in_r4: y_r3_r4_eth1 + y_h4_r4_eth2 + y_r2_r4_eth0 <= 1

        \ Provide mutual exclusion on OUTPUT routes on all elements of flow y
        y_out_r1: y_r1_s0_eth2 + y_r1_r2_eth0 + y_r1_r3_eth0 <= 1
        y_out_r2: y_r2_r1_eth0 + y_r2_r4_eth0 + y_r2_r3_eth1 <= 1
        y_out_r3: y_r3_r1_eth1 + y_r3_r2_eth1 + y_r3_h3_eth0 + y_r3_r4_eth1 <= 1
        y_out_r4: y_r4_r2_eth2 + y_r4_r3_eth2 + y_r4_h4_eth0 <= 1

        \ Provide mutual exclusion on INPUT routes on all elements of flow z
        z_in_r1: z_s0_r1_eth2 + z_r2_r1_eth0 + z_r3_r1_eth1 <= 1
        z_in_r2: z_r3_r2_eth1 + z_r1_r2_eth0 + z_r4_r2_eth2 <= 1
        z_in_r3: z_r2_r3_eth1 + z_h3_r3_eth3 + z_r4_r3_eth2 + z_r1_r3_eth0 <= 1
        z_in_r4: z_r3_r4_eth1 + z_h4_r4_eth2 + z_r2_r4_eth0 <= 1

        \ Provide mutual exclusion on OUTPUT routes on all elements of flow z
        z_out_r1: z_r1_s0_eth2 + z_r1_r2_eth0 + z_r1_r3_eth0 <= 1
        z_out_r2: z_r2_r1_eth0 + z_r2_r4_eth0 + z_r2_r3_eth1 <= 1
        z_out_r3: z_r3_r1_eth1 + z_r3_r2_eth1 + z_r3_h3_eth0 + z_r3_r4_eth1 <= 1
        z_out_r4: z_r4_r2_eth2 + z_r4_r3_eth2 + z_r4_h4_eth0 <= 1


Bounds
        0 <= ratio_x <= 10
        0 <= ratio_y <= 2
        0 <= ratio_z <= 15
Binary
        y_r3_r1_eth1
        z_s0_h2_eth0
        z_h4_r4_eth2
        x_r4_r2_eth2
        z_r4_r3_eth2
        x_h2_s0_eth1
        y_h2_s0_eth1
        z_r1_s0_eth2
        x_s0_r1_eth2
        x_r4_r3_eth2
        z_r2_r3_eth1
        y_r1_s0_eth2
        y_s0_h1_eth0
        y_r4_r3_eth2
        x_r3_r2_eth1
        z_s0_r1_eth2
        y_r1_r3_eth0
        x_r3_h3_eth0
        y_h1_s0_eth0
        x_s0_h2_eth0
        z_r2_r1_eth0
        x_s0_h1_eth0
        x_h4_r4_eth2
        x_r4_h4_eth0
        y_r3_h3_eth0
        x_h3_r3_eth3
        y_h3_r3_eth3
        y_r3_r2_eth1
        y_r3_r4_eth1
        z_r2_r4_eth0
        y_r4_r2_eth2
        z_r4_r2_eth2
        y_r2_r1_eth0
        z_s0_h1_eth0
        z_h2_s0_eth1
        y_r2_r3_eth1
        y_r4_h4_eth0
        x_r2_r1_eth0
        z_r3_r4_eth1
        z_r1_r3_eth0
        z_r4_h4_eth0
        x_r1_r3_eth0
        x_r1_r2_eth0
        x_r3_r4_eth1
        x_r2_r3_eth1
        z_r3_r2_eth1
        y_s0_r1_eth2
        z_h1_s0_eth0
        z_h3_r3_eth3
        z_r3_h3_eth0
        x_h1_s0_eth0
        y_h4_r4_eth2
        y_s0_h2_eth0
        x_r1_s0_eth2
        y_r2_r4_eth0
        z_r1_r2_eth0
        z_r3_r1_eth1
        x_r3_r1_eth1
        x_r2_r4_eth0
        y_r1_r2_eth0
End