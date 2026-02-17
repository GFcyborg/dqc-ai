// Chunk 3 of 4 from gateteleport.qasm
// Required variables:
//   qubit[3] q
//   qubit[3] a


// prep magic state
rz(pi/4) a;

// entangle two logical registers
cx q, a;