// Standard single-qubit gates
gate u3(theta, phi, lambda) a {
  U(theta, phi, lambda) a;
}

gate u2(phi, lambda) a {
  U(π/2, phi, lambda) a;
}

gate u1(lambda) a {
  U(0, 0, lambda) a;
}

gate cx a, b {
  CX a, b;
}

gate id a {
  U(0, 0, 0) a;
}

gate x a {
  u3(π, 0, π) a;
}

gate y a {
  u3(π, π/2, π/2) a;
}

gate z a {
  u1(π) a;
}

gate h a {
  u2(0, π) a;
}

gate s a {
  u1(π/2) a;
}

gate sdg a {
  u1(-π/2) a;
}

gate t a {
  u1(π/4) a;
}

gate tdg a {
  u1(-π/4) a;
}

gate rx(theta) a {
  u3(theta, -π/2, π/2) a;
}

gate ry(theta) a {
  u3(theta, 0, 0) a;
}

gate rz(phi) a {
  u1(phi) a;
}

gate cz a, b {
  h b;
  cx a, b;
  h b;
}

gate cy a, b {
  sdg b;
  cx a, b;
  s b;
}

gate swap a, b {
  cx a, b;
  cx b, a;
  cx a, b;
}

gate ch a, b {
  h b;
  sdg b;
  cx a, b;
  h b;
  t b;
  cx a, b;
  t b;
  h b;
  s b;
  x b;
  s a;
}

gate ccx a, b, c {
  h c;
  cx b, c;
  tdg c;
  cx a, c;
  t c;
  cx b, c;
  tdg c;
  cx a, c;
  t b;
  t c;
  h c;
  cx a, b;
  t a;
  tdg b;
  cx a, b;
}

gate cswap a, b, c {
  cx c, b;
  ccx a, b, c;
  cx c, b;
}
