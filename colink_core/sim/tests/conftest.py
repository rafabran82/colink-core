import math

def approx(a, b, rel=1e-9, abs=1e-12):
    return math.isclose(a, b, rel_tol=rel, abs_tol=abs)

