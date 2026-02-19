// Chunk 2 of 2 from adder.qasm
// Required variables:
//   qubit[4] b
//   qubit cout
//   bit[5] ans

include "stdgates.inc";

measure b[0:3] -> ans[0:3];
measure cout[0] -> ans[4];