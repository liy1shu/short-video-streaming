from scipy import optimize
import numpy as np

Z = np.array([-1])
A = np.array([[1]] * 4)

B = np.array([ -1169.18122875,  -4151.23847901, -11649.55837639, -26697.7015741 ])

x_bound = (-1000000, 4000.0)

print(A)
print(B)

res = optimize.linprog(Z, A_ub = A, b_ub = B, bounds = (x_bound))

print(res)
