\ Maximize minimum throughput ratio for each maximum transmission rate r1, r2, r3
\ The ratio is defined as r*i (which is the maximum transmission rate archieved by the demand i) / r_i (which is the maximum transmission rate defined a priori)
Maximize
obj: min

Subject To:
 min1: min - r1 
 min2: min - r2
 min3: min - r3

Bounds:
0 <= r1 <= 1
0 <= r2 <= 1
0 <= r3 <= 1
0 <= min <= 1

End