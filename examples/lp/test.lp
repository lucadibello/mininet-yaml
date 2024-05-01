\ try our topology

Maximize
    obj: min + x + y + z \ ?? I think this should work

Subject to
    min1: min - x <= 0
    min2: min - y <= 0
    min3: min - z <= 0

    \ find input
    flow1: 10 x - lambda_x = 0
    flow2: 2 y - lambda_y = 0
    flow3: 15 z - lambda_z = 0

    \ flow balance for real-value rate variables
    \ flow x
    flow_a_rx: rx_ba - rx_ab + rx_ca - rx_ac + lambda_x = 0
    flow_b_rx: rx_ab + rx_cb + rx_db - rx_ba - rx_bc - rx_bd = 0
    flow_c_rx: rx_ac + rx_bc + rx_dc - rx_ca - rx_cb - rx_cd = 0
    flow_d_rx: rx_bd + rx_cd - rx_db - rx_dc - lambda_x = 0
    \ flow y
    flow_a_ry: ry_ba - ry_ab + ry_ca - ry_ac - lambda_y = 0
    flow_b_ry: ry_ab + ry_cb + ry_db - ry_ba - ry_bc - ry_bd = 0
    flow_c_ry: ry_ac + ry_bc + ry_dc - ry_ca - ry_cb - ry_cd = 0
    flow_d_ry: ry_bd + ry_cd - ry_db - ry_dc + lambda_y = 0
    \ flow z
    flow_a_rz: rz_ba - rz_ab + rz_ca - rz_ac = 0
    flow_b_rz: rz_ab + rz_cb + rz_db - rz_ba - rz_bc - rz_bd = 0
    flow_c_rz: rz_ac + rz_bc + rz_dc - rz_ca - rz_cb - rz_cd + lambda_z = 0
    flow_d_rz: rz_bd + rz_cd - rz_db - rz_dc - lambda_z = 0

\ flow balance for binary rate variables
    \ flow x
    flow_a_x: x_ba - x_ab + x_ca - x_ac = -1
    flow_b_x: x_ab + x_cb + x_db - x_ba - x_bc - x_bd = 0
    flow_c_x: x_ac + x_bc + x_dc - x_ca - x_cb - x_cd = 0
    flow_d_x: x_bd + x_cd - x_db - x_dc = 1
    \ flow y
    flow_a_y: y_ba - y_ab + y_ca - y_ac = 1
    flow_b_y: y_ab + y_cb + y_db - y_ba - y_bc - y_bd = 0
    flow_c_y: y_ac + y_bc + y_dc - y_ca - y_cb - y_cd = 0
    flow_d_y: y_bd + y_cd - y_db - y_dc = -1
    \ flow z
    flow_a_z: z_ba - z_ab + z_ca - z_ac = 0
    flow_b_z: z_ab + z_cb + z_db - z_ba - z_bc - z_bd = 0
    flow_c_z: z_ac + z_bc + z_dc - z_ca - z_cb - z_cd = -1
    flow_d_z: z_bd + z_cd - z_db - z_dc = 1

    \ mutual exclusion for binary, for incoming to same node, for each flow
    \ flow x
    in_x_a: x_ba + x_ca <= 1
    in_x_b: x_ab + x_cb + x_db <= 1
    in_x_c: x_ac + x_bc + x_dc <= 1
    in_x_d: x_bd + x_cd <= 1
    \ flow y
    in_y_a: y_ba + y_ca <= 1
    in_y_b: y_ab + y_cb + y_db <= 1
    in_y_c: y_ac + y_bc + y_dc <= 1
    in_y_d: y_bd + y_cd <= 1
    \ flow z
    in_z_a: z_ba + z_ca <= 1
    in_z_b: z_ab + z_cb + z_db <= 1
    in_z_c: z_ac + z_bc + z_dc <= 1
    in_z_d: z_bd + z_cd <= 1

    \mutual exclusion for binary, for outgoing from same node, for each flow
    \ flow x
    out_x_a: x_ab + x_ac <= 1
    out_x_b: x_ba + x_bc + x_bd <= 1
    out_x_c: x_ca + x_cb + x_cd <= 1
    out_x_d: x_db + x_dc <= 1
    \ flow y
    out_y_a: y_ab + y_ac <= 1
    out_y_b: y_ba + y_bc + y_bd <= 1
    out_y_c: y_ca + y_cb + y_cd <= 1
    out_y_d: y_db + y_dc <= 1
    \ flow y
    out_z_a: z_ab + z_ac <= 1
    out_z_b: z_ba + z_bc + z_bd <= 1
    out_z_c: z_ca + z_cb + z_cd <= 1
    out_z_d: z_db + z_dc <= 1

    \ link capacities for each link
    ab_c: rx_ab + rx_ba + ry_ab + ry_ba + rz_ab + rz_ba <= 3
    ac_c: rx_ac + rx_ca + ry_ac + ry_ca + rz_ac + rz_ca <= 10
    bc_c: rx_bc + rx_cb + ry_bc + ry_cb + rz_bc + rz_cb <= 8
    bd_c: rx_bd + rx_db + ry_bd + ry_db + rz_bd + rz_db <= 10
    cd_c: rx_cd + rx_dc + ry_cd + ry_dc + rz_cd + rz_dc <= 10

    \ control of real-value flow variables by corresponding binary indicators, for each flow, for each link
    \ flow x
    ab_cx: rx_ab - 3 x_ab <= 0
    ba_cx: rx_ba - 3 x_ba <= 0
    ac_cx: rx_ac - 10 x_ac <= 0
    ca_cx: rx_ca - 10 x_ca <= 0
    bc_cx: rx_bc - 8 x_bc <= 0
    cb_cx: rx_cb - 8 x_cb <= 0
    bd_cx: rx_bd - 10 x_bd <= 0
    db_cx: rx_db - 10 x_db <= 0
    cd_cx: rx_cd - 10 x_cd <= 0
    dc_cx: rx_dc - 10 x_dc <= 0
    \ flow y
    ab_cy: ry_ab - 3  y_ab <= 0
    ba_cy: ry_ba - 3  y_ba <= 0
    ac_cy: ry_ac - 10 y_ac <= 0
    ca_cy: ry_ca - 10 y_ca <= 0
    bc_cy: ry_bc - 8  y_bc <= 0
    cb_cy: ry_cb - 8  y_cb <= 0
    bd_cy: ry_bd - 10 y_bd <= 0
    db_cy: ry_db - 10 y_db <= 0
    cd_cy: ry_cd - 10 y_cd <= 0
    dc_cy: ry_dc - 10 y_dc <= 0
    \ flow z
    ab_cz: rz_ab - 3  z_ab <= 0
    ba_cz: rz_ba - 3  z_ba <= 0
    ac_cz: rz_ac - 10 z_ac <= 0
    ca_cz: rz_ca - 10 z_ca <= 0
    bc_cz: rz_bc - 8  z_bc <= 0
    cb_cz: rz_cb - 8  z_cb <= 0
    bd_cz: rz_bd - 10 z_bd <= 0
    db_cz: rz_db - 10 z_db <= 0
    cd_cz: rz_cd - 10 z_cd <= 0
    dc_cz: rz_dc - 10 z_dc <= 0

Bounds
    0 <= x <= 1
    0 <= lambda_x <= 10
    0 <= y <= 1
    0 <= lambda_y <= 2
    0 <= z <= 1
    0 <= lambda_z <= 15

Binary
    \ flow x
    x_ab
    x_ba
    x_ac
    x_ca
    x_bc
    x_cb
    x_bd
    x_db
    x_cd
    x_dc
    \ flow y
    y_ab
    y_ba
    y_ac
    y_ca
    y_bc
    y_cb
    y_bd
    y_db
    y_cd
    y_dc
    \ flow z
    z_ab
    z_ba
    z_ac
    z_ca
    z_bc
    z_cb
    z_bd
    z_db
    z_cd
    z_dc

End