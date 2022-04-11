from pulp import *
import pandas as pd
import numpy as np
from class_stato import stato


def dos_list(df, estrusori):
    df_solver = pd.DataFrame()
    df_OP = df.sort_values(['estrusore', 'data', 'ordine']).copy()
    # riempie il dizionario con il primo cono in stato ORDINATO
    for est in estrusori:
        mask = (df_OP['estrusore'] == est) & (
            df_OP['stato'] == 'O')
        df_tmp = df_OP[mask]
        if len(df_tmp) > 0:
            df_solver = pd.concat(
                [df_solver, pd.DataFrame([df_tmp.iloc[0, ]])], axis=0)
    df_solver.index = [df_solver['estrusore']]
    return(df_solver)


#  Creates a list of container
containers = list(stato.df_coni.index)

#  Creates a list of dosaggi
dosaggi = ['D' + str(n) for n in range(1, 9)]

df_dos = dos_list(stato.df_OP, stato.estrusori)

#  Dictionary of the dosaggi's color
colors_d = pd.Series.to_dict(stato.df_dos['color'])

#  Dictionary of the dosaggi's valcrom
valcroms_d = pd.Series.to_dict(stato.df_dos['valcrom'])

#  Dictionary of the dosaggi's time of weighing
time_d = pd.Series.to_dict(stato.df_dos['TD'])

#  Dictionary of the container's color
colors_c = pd.Series.to_dict(stato.df_coni['color'])

#  Dictionary of the container's valcrom
valcroms_c = pd.Series.to_dict(stato.df_coni['color'])

#  Dictionary of the TEr times for each extruder
ter = {'D1': 15, 'D2': 200, 'D3': 0, 'D4': 0,
       'D5': 95, 'D6': 20, 'D7': 30, 'D8': 17, 'D9': 0}

#  Dictionary of the TCr times for each extruder
tcr = {'D1': 150, 'D2': 2, 'D3': 80, 'D4': 0,
       'D5': 105, 'D6': 10, 'D7': 300, 'D8': 1, 'D9': 400}

#  Dictionary of mp with time to pick
mp_time = pd.Series.to_dict(stato.df_giacenza['time_pick'])

#  Dictionary of mp quantity in stock
mp_qta = pd.Series.to_dict(stato.df_giacenza['qta'])

#  Dictionary of mix for each dosaggio
mix = {'D1': {'A': 10, 'B': 100}, 'D2': {'C': 50, 'A': 100, 'D': 2000, 'E': 20},
       'D3': {'F': 80, 'G': 500},
       'D4': {'M': 400000000, 'N': 15, 'O': 30},
       'D5': {'I': 50, 'L': 20, 'H': 20},
       'D6': {'O': 10, 'A': 40, 'D': 80, 'E': 10},
       'D7': {'F': 80, 'G': 100},
       'D8': {'I': 84, 'C': 7400},
       'D9': {'L': 200, 'I': 40, 'D': 10}}

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
#  ------------------------
#  ------------------------
