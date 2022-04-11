from pulp import *
import numpy as np


# Create the 'prob' variable to contain the problem data
prob = LpProblem("The complete sequencing Problem", LpMinimize)
#  ---------------------

# A dictionary is created to contain the referenced Variables
arcs = [(d, c) for c in containers for d in dosaggi]
variables = LpVariable.dicts(
    "Couples", (dosaggi, containers), 0, None, LpInteger)
#  ------------------

#  Define lists with values for objective function
color_obj = [((colors_d[d] - colors_c[c]) + (valcroms_d[d] -
              valcroms_c[c])) * variables[d][c] for (d, c) in arcs]
color_obj = np.multiply(color_obj, 0.25)

time_obj = [(ter[d] + tcr[d] - time_d[d]) * variables[d][c] for (d, c) in arcs]
time_obj = np.multiply(time_obj, 0.5)

time_pick_obj = [(np.sum(mp_time[x] for x in mix[d]))
                 * variables[d][c] for (d, c) in arcs]
time_pick_obj = np.multiply(time_obj, 0.25)

objective = time_obj + color_obj + time_pick_obj
#  --------------------

# The objective function is added to 'prob' first
prob += (lpSum(objective),
         "Total delta color/time/picking ",
         )
#  ------------------
# The constraints are added to 'prob'
prob += lpSum([variables[d][c]
              for d in dosaggi for c in containers]) == 1, "PercentagesSum"

i = 0
for d in dosaggi:
    for c in containers:
        i += 1
        prob += (variables[d][c] >= 0,
                 str(i),
                 )

for d in dosaggi:
    for c in containers:
        prob += (variables[d][c] * colors_d[d] >= variables[d][c] * colors_c[c],
                 "Vincolo di colore{}".format(str(d + c)),
                 )

for d in dosaggi:
    for c in containers:
        prob += (variables[d][c] * valcroms_d[d] >= variables[d][c] * valcroms_c[c],
                 "Vincolo di valcrom{}".format(str(d + c)),
                 )

for d in dosaggi:
    for c in containers:
        for m in mix[d]:
            prob += (variables[d][c] * mix[d][m] <= variables[d][c] * mp_qta[m],
                     "Vincolo di quantità stock{}".format(str(d + c + m)),
                     )
#  ---------------------

# The problem is solved using PuLP's choice of Solver
prob.solve()

# Each of the variables is printed with it's resolved optimum value
for v in prob.variables():
    if v.varValue == 1:
        dos = v.name[8:10]
        con = v.name[11:]
#  ------------------------
