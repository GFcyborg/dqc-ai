// Chunk 4 of 4 from gateteleport.qasm
// Required variables:
//   qubit[3] q
//   qubit[3] a
//   bit r


// measure out the ancilla
r = logical_meas(a);

// if we get a logical |1> then we need to apply a logical Z correction
if (r == 1) z q;