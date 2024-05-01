Maximize
	obj: min_r + x + y + z

Subject To
	\ Set min_r as the minimum of all effectiveness ratios
	x_min: min_r - x <= 0
	y_min: min_r - y <= 0
	z_min: min_r - z <= 0

	\ Define how the ratio is computed for each flow
	x_flow: 10 x - lambda_x = 0
	y_flow: 2 y - lambda_y = 0
	z_flow: 15 z - lambda_z = 0

	\ Provide mutual exclusion on INPUT routes on all elements of flow x
	x_in_r1: x_r2_r1_eth0 + x_r3_r1_eth1 <= 1
	x_in_r2: x_r1_r2_eth0 + x_r4_r2_eth2 + x_r3_r2_eth1 <= 1
	x_in_r3: x_r4_r3_eth2 + x_r1_r3_eth0 + x_r2_r3_eth1 <= 1
	x_in_r4: x_r2_r4_eth0 + x_r3_r4_eth1 <= 1

	\ Provide mutual exclusion on OUTPUT routes on all elements of flow x
	x_out_r1: x_r1_r2_eth0 + x_r1_r3_eth0 <= 1
	x_out_r2: x_r2_r1_eth0 + x_r2_r4_eth0 + x_r2_r3_eth1 <= 1
	x_out_r3: x_r3_r1_eth1 + x_r3_r2_eth1 + x_r3_r4_eth1 <= 1
	x_out_r4: x_r4_r2_eth2 + x_r4_r3_eth2 <= 1

	\ Provide mutual exclusion on INPUT routes on all elements of flow y
	y_in_r1: y_r2_r1_eth0 + y_r3_r1_eth1 <= 1
	y_in_r2: y_r1_r2_eth0 + y_r4_r2_eth2 + y_r3_r2_eth1 <= 1
	y_in_r3: y_r4_r3_eth2 + y_r1_r3_eth0 + y_r2_r3_eth1 <= 1
	y_in_r4: y_r2_r4_eth0 + y_r3_r4_eth1 <= 1

	\ Provide mutual exclusion on OUTPUT routes on all elements of flow y
	y_out_r1: y_r1_r2_eth0 + y_r1_r3_eth0 <= 1
	y_out_r2: y_r2_r1_eth0 + y_r2_r4_eth0 + y_r2_r3_eth1 <= 1
	y_out_r3: y_r3_r1_eth1 + y_r3_r2_eth1 + y_r3_r4_eth1 <= 1
	y_out_r4: y_r4_r2_eth2 + y_r4_r3_eth2 <= 1

	\ Provide mutual exclusion on INPUT routes on all elements of flow z
	z_in_r1: z_r2_r1_eth0 + z_r3_r1_eth1 <= 1
	z_in_r2: z_r1_r2_eth0 + z_r4_r2_eth2 + z_r3_r2_eth1 <= 1
	z_in_r3: z_r4_r3_eth2 + z_r1_r3_eth0 + z_r2_r3_eth1 <= 1
	z_in_r4: z_r2_r4_eth0 + z_r3_r4_eth1 <= 1

	\ Provide mutual exclusion on OUTPUT routes on all elements of flow z
	z_out_r1: z_r1_r2_eth0 + z_r1_r3_eth0 <= 1
	z_out_r2: z_r2_r1_eth0 + z_r2_r4_eth0 + z_r2_r3_eth1 <= 1
	z_out_r3: z_r3_r1_eth1 + z_r3_r2_eth1 + z_r3_r4_eth1 <= 1
	z_out_r4: z_r4_r2_eth2 + z_r4_r3_eth2 <= 1

	\ Provide mutual exclusion on INPUT and OUTPUT routes on all elements of flow x
	x_in_out_r1: x_r2_r1_eth0 + x_r3_r1_eth1 - x_r1_r2_eth0 - x_r1_r3_eth0 = -1
	x_in_out_r2: x_r1_r2_eth0 + x_r4_r2_eth2 + x_r3_r2_eth1 - x_r2_r1_eth0 - x_r2_r4_eth0 - x_r2_r3_eth1 = 0
	x_in_out_r3: x_r4_r3_eth2 + x_r1_r3_eth0 + x_r2_r3_eth1 - x_r3_r1_eth1 - x_r3_r2_eth1 - x_r3_r4_eth1 = 0
	x_in_out_r4: x_r2_r4_eth0 + x_r3_r4_eth1 - x_r4_r2_eth2 - x_r4_r3_eth2 = 1

	\ Provide mutual exclusion on INPUT and OUTPUT routes on all elements of flow y
	y_in_out_r1: y_r2_r1_eth0 + y_r3_r1_eth1 - y_r1_r2_eth0 - y_r1_r3_eth0 = 1
	y_in_out_r2: y_r1_r2_eth0 + y_r4_r2_eth2 + y_r3_r2_eth1 - y_r2_r1_eth0 - y_r2_r4_eth0 - y_r2_r3_eth1 = 0
	y_in_out_r3: y_r4_r3_eth2 + y_r1_r3_eth0 + y_r2_r3_eth1 - y_r3_r1_eth1 - y_r3_r2_eth1 - y_r3_r4_eth1 = 0
	y_in_out_r4: y_r2_r4_eth0 + y_r3_r4_eth1 - y_r4_r2_eth2 - y_r4_r3_eth2 = -1

	\ Provide mutual exclusion on INPUT and OUTPUT routes on all elements of flow z
	z_in_out_r1: z_r2_r1_eth0 + z_r3_r1_eth1 - z_r1_r2_eth0 - z_r1_r3_eth0 = 0
	z_in_out_r2: z_r1_r2_eth0 + z_r4_r2_eth2 + z_r3_r2_eth1 - z_r2_r1_eth0 - z_r2_r4_eth0 - z_r2_r3_eth1 = 0
	z_in_out_r3: z_r4_r3_eth2 + z_r1_r3_eth0 + z_r2_r3_eth1 - z_r3_r1_eth1 - z_r3_r2_eth1 - z_r3_r4_eth1 = -1
	z_in_out_r4: z_r2_r4_eth0 + z_r3_r4_eth1 - z_r4_r2_eth2 - z_r4_r3_eth2 = 1

	\ Define the maximum capacity of each element for flow x
	x_capacity_r1: x_cap_r2_r1_eth0 + x_cap_r3_r1_eth1 - x_cap_r1_r2_eth0 - x_cap_r1_r3_eth0 + lambda_x = 0
	x_capacity_r2: x_cap_r1_r2_eth0 + x_cap_r4_r2_eth2 + x_cap_r3_r2_eth1 - x_cap_r2_r1_eth0 - x_cap_r2_r4_eth0 - x_cap_r2_r3_eth1 = 0
	x_capacity_r3: x_cap_r4_r3_eth2 + x_cap_r1_r3_eth0 + x_cap_r2_r3_eth1 - x_cap_r3_r1_eth1 - x_cap_r3_r2_eth1 - x_cap_r3_r4_eth1 = 0
	x_capacity_r4: x_cap_r2_r4_eth0 + x_cap_r3_r4_eth1 - x_cap_r4_r2_eth2 - x_cap_r4_r3_eth2 - lambda_x = 0

	\ Define the maximum capacity of each element for flow y
	y_capacity_r1: y_cap_r2_r1_eth0 + y_cap_r3_r1_eth1 - y_cap_r1_r2_eth0 - y_cap_r1_r3_eth0 - lambda_y = 0
	y_capacity_r2: y_cap_r1_r2_eth0 + y_cap_r4_r2_eth2 + y_cap_r3_r2_eth1 - y_cap_r2_r1_eth0 - y_cap_r2_r4_eth0 - y_cap_r2_r3_eth1 = 0
	y_capacity_r3: y_cap_r4_r3_eth2 + y_cap_r1_r3_eth0 + y_cap_r2_r3_eth1 - y_cap_r3_r1_eth1 - y_cap_r3_r2_eth1 - y_cap_r3_r4_eth1 = 0
	y_capacity_r4: y_cap_r2_r4_eth0 + y_cap_r3_r4_eth1 - y_cap_r4_r2_eth2 - y_cap_r4_r3_eth2 + lambda_y = 0

	\ Define the maximum capacity of each element for flow z
	z_capacity_r1: z_cap_r2_r1_eth0 + z_cap_r3_r1_eth1 - z_cap_r1_r2_eth0 - z_cap_r1_r3_eth0 = 0
	z_capacity_r2: z_cap_r1_r2_eth0 + z_cap_r4_r2_eth2 + z_cap_r3_r2_eth1 - z_cap_r2_r1_eth0 - z_cap_r2_r4_eth0 - z_cap_r2_r3_eth1 = 0
	z_capacity_r3: z_cap_r4_r3_eth2 + z_cap_r1_r3_eth0 + z_cap_r2_r3_eth1 - z_cap_r3_r1_eth1 - z_cap_r3_r2_eth1 - z_cap_r3_r4_eth1 + lambda_z = 0
	z_capacity_r4: z_cap_r2_r4_eth0 + z_cap_r3_r4_eth1 - z_cap_r4_r2_eth2 - z_cap_r4_r3_eth2 - lambda_z = 0

	\ Define overall capacities of each edge in the network for all flows
	capacity_r3_r4_eth1: x_cap_r4_r3_eth2 + y_cap_r4_r3_eth2 + z_cap_r4_r3_eth2 + x_cap_r3_r4_eth1 + y_cap_r3_r4_eth1 + z_cap_r3_r4_eth1 <= 10
	capacity_r2_r1_eth0: x_cap_r1_r2_eth0 + y_cap_r1_r2_eth0 + z_cap_r1_r2_eth0 + x_cap_r2_r1_eth0 + y_cap_r2_r1_eth0 + z_cap_r2_r1_eth0 <= 3
	capacity_r3_r1_eth1: x_cap_r1_r3_eth0 + y_cap_r1_r3_eth0 + z_cap_r1_r3_eth0 + x_cap_r3_r1_eth1 + y_cap_r3_r1_eth1 + z_cap_r3_r1_eth1 <= 10
	capacity_r4_r2_eth2: x_cap_r2_r4_eth0 + y_cap_r2_r4_eth0 + z_cap_r2_r4_eth0 + x_cap_r4_r2_eth2 + y_cap_r4_r2_eth2 + z_cap_r4_r2_eth2 <= 10
	capacity_r3_r2_eth1: x_cap_r2_r3_eth1 + y_cap_r2_r3_eth1 + z_cap_r2_r3_eth1 + x_cap_r3_r2_eth1 + y_cap_r3_r2_eth1 + z_cap_r3_r2_eth1 <= 8

	\ Define the flow on each route of flow x
	x_capacity_r4_r3_eth2: x_cap_r4_r3_eth2 - 10 x_r4_r3_eth2 <= 0
	x_capacity_r1_r2_eth0: x_cap_r1_r2_eth0 - 3 x_r1_r2_eth0 <= 0
	x_capacity_r2_r1_eth0: x_cap_r2_r1_eth0 - 3 x_r2_r1_eth0 <= 0
	x_capacity_r1_r3_eth0: x_cap_r1_r3_eth0 - 10 x_r1_r3_eth0 <= 0
	x_capacity_r3_r1_eth1: x_cap_r3_r1_eth1 - 10 x_r3_r1_eth1 <= 0
	x_capacity_r2_r4_eth0: x_cap_r2_r4_eth0 - 10 x_r2_r4_eth0 <= 0
	x_capacity_r4_r2_eth2: x_cap_r4_r2_eth2 - 10 x_r4_r2_eth2 <= 0
	x_capacity_r2_r3_eth1: x_cap_r2_r3_eth1 - 8 x_r2_r3_eth1 <= 0
	x_capacity_r3_r2_eth1: x_cap_r3_r2_eth1 - 8 x_r3_r2_eth1 <= 0
	x_capacity_r3_r4_eth1: x_cap_r3_r4_eth1 - 10 x_r3_r4_eth1 <= 0

	\ Define the flow on each route of flow y
	y_capacity_r4_r3_eth2: y_cap_r4_r3_eth2 - 10 y_r4_r3_eth2 <= 0
	y_capacity_r1_r2_eth0: y_cap_r1_r2_eth0 - 3 y_r1_r2_eth0 <= 0
	y_capacity_r2_r1_eth0: y_cap_r2_r1_eth0 - 3 y_r2_r1_eth0 <= 0
	y_capacity_r1_r3_eth0: y_cap_r1_r3_eth0 - 10 y_r1_r3_eth0 <= 0
	y_capacity_r3_r1_eth1: y_cap_r3_r1_eth1 - 10 y_r3_r1_eth1 <= 0
	y_capacity_r2_r4_eth0: y_cap_r2_r4_eth0 - 10 y_r2_r4_eth0 <= 0
	y_capacity_r4_r2_eth2: y_cap_r4_r2_eth2 - 10 y_r4_r2_eth2 <= 0
	y_capacity_r2_r3_eth1: y_cap_r2_r3_eth1 - 8 y_r2_r3_eth1 <= 0
	y_capacity_r3_r2_eth1: y_cap_r3_r2_eth1 - 8 y_r3_r2_eth1 <= 0
	y_capacity_r3_r4_eth1: y_cap_r3_r4_eth1 - 10 y_r3_r4_eth1 <= 0

	\ Define the flow on each route of flow z
	z_capacity_r4_r3_eth2: z_cap_r4_r3_eth2 - 10 z_r4_r3_eth2 <= 0
	z_capacity_r1_r2_eth0: z_cap_r1_r2_eth0 - 3 z_r1_r2_eth0 <= 0
	z_capacity_r2_r1_eth0: z_cap_r2_r1_eth0 - 3 z_r2_r1_eth0 <= 0
	z_capacity_r1_r3_eth0: z_cap_r1_r3_eth0 - 10 z_r1_r3_eth0 <= 0
	z_capacity_r3_r1_eth1: z_cap_r3_r1_eth1 - 10 z_r3_r1_eth1 <= 0
	z_capacity_r2_r4_eth0: z_cap_r2_r4_eth0 - 10 z_r2_r4_eth0 <= 0
	z_capacity_r4_r2_eth2: z_cap_r4_r2_eth2 - 10 z_r4_r2_eth2 <= 0
	z_capacity_r2_r3_eth1: z_cap_r2_r3_eth1 - 8 z_r2_r3_eth1 <= 0
	z_capacity_r3_r2_eth1: z_cap_r3_r2_eth1 - 8 z_r3_r2_eth1 <= 0
	z_capacity_r3_r4_eth1: z_cap_r3_r4_eth1 - 10 z_r3_r4_eth1 <= 0


Bounds
	0 <= x <= 1
	0 <= lambda_x <= 10
	0 <= y <= 1
	0 <= lambda_y <= 2
	0 <= z <= 1
	0 <= lambda_z <= 15
Binary
	z_r2_r3_eth1
	x_r1_r3_eth0
	x_r2_r1_eth0
	x_r3_r1_eth1
	y_r1_r3_eth0
	y_r1_r2_eth0
	y_r4_r2_eth2
	z_r3_r4_eth1
	z_r2_r1_eth0
	y_r2_r1_eth0
	x_r2_r3_eth1
	z_r3_r1_eth1
	x_r3_r4_eth1
	x_r3_r2_eth1
	x_r4_r2_eth2
	z_r2_r4_eth0
	x_r1_r2_eth0
	z_r4_r2_eth2
	z_r4_r3_eth2
	y_r2_r3_eth1
	z_r1_r2_eth0
	y_r2_r4_eth0
	z_r1_r3_eth0
	z_r3_r2_eth1
	x_r2_r4_eth0
	y_r3_r4_eth1
	y_r3_r2_eth1
	y_r4_r3_eth2
	x_r4_r3_eth2
	y_r3_r1_eth1
End
