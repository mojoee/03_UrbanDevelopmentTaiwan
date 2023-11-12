import gurobipy as gp
from gurobipy import GRB
import copy
import numpy as np


n = 14000
m = 200
# random integer matrix
np.random.seed(1)
A = np.random.randint(0, 100, size=(n, m), dtype=np.int8)
B = copy.deepcopy(A)

# create permutation matrix P
P_hat = np.eye(m)
np.random.shuffle(P_hat)




# permutate columns of B
import random
B = B @ P_hat

# add small random elta to B
delta = np.random.randint(0, 3, size=(n, m))
B = B + delta

# check if A and B have the same column sum
assert np.sum(A, axis=0).all() == np.sum(B, axis=0).all()

with gp.Env(empty=True) as env:
    env.setParam("OutputFlag", 0)
    env.start()
    with gp.Model(env=env) as model:

        P = model.addMVar((m, m), vtype=GRB.BINARY)

        obj = ((A @ P) * B).sum()
        model.setObjective(obj, GRB.MAXIMIZE)

        model.addConstrs(P[:,i].sum() == 1 for i in range(m))
        model.addConstrs(P[i,:].sum() == 1 for i in range(m))

        model.optimize()

        P = np.array([[P[i, j].x for j in range(m)] for i in range(m)])
        print(P)
        print(np.sum(P, axis=0))

        print("obj: ", model.objVal)

        # check if P is a permutation matrix
        assert np.sum(P, axis=0).all() == 1
        assert np.sum(P, axis=1).all() == 1
        assert np.sum(P) == m

        assert np.allclose(P, P_hat)
