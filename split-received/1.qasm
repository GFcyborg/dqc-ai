// Chunk 1 of 2 from adder.qasm
// Required variables:
//   qubit[4] a
//   qubit[4] b
//   uint[4] a_in
//   uint[4] b_in

// set input states
for uint i in [0: 3] {
  if(bool(a_in[i])) x a[i];
  if(bool(b_in[i])) x b[i];
}