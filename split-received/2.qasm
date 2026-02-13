// Chunk 2 of 2 from adder.qasm
// Required variables:
//   gate majority
//   gate unmaj
//   qubit cin
//   qubit[4] a
//   qubit[4] b
//   qubit cout
//   bit[5] ans

// add a to b, storing result in b
majority cin[0], b[0], a[0];
for uint i in [0: 2] { majority a[i], b[i + 1], a[i + 1]; }
cx a[3], cout[0];
for uint i in [2: -1: 0] { unmaj a[i],b[i+1],a[i+1]; }
unmaj cin[0], b[0], a[0];
measure b[0:3] -> ans[0:3];
measure cout[0] -> ans[4];