import pulp as lp
import pandas as pd
import numpy as np

t_now = 0

coeff_con = 1
coeff_time = 0
coeff_mir = 10 * 0


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
    df_solver['ID'] = df_solver.index
    df_solver.index = df_solver['estrusore']
    return(df_solver)


def best_choice(t_now, stato):
    global coeff_con, coeff_time, coeff_mir
    #  Creates a list of container
    mask_disp = stato.df_coni['stato'] == 'D'
    containers = list(stato.df_coni[mask_disp].index)

    #  Creates a dataframe of dosaggi
    df_dos = dos_list(stato.df_OP, stato.estrusori)

    #  Dictionary of the dosaggi's color
    colors_d = pd.Series.to_dict(df_dos['color'])

    #  Dictionary of the dosaggi's valcrom
    valcroms_d = pd.Series.to_dict(df_dos['valcrom'])

    #  Dictionary of the dosaggi's time of weighing
    time_d = pd.Series.to_dict(df_dos['TD'])

    #  Dictionary of the container's color
    colors_c = pd.Series.to_dict(stato.df_coni[mask_disp]['color'])

    #  Dictionary of the container's valcrom
    valcroms_c = pd.Series.to_dict(stato.df_coni[mask_disp]['color'])

    #  Dictionary of the TEr times for each extruder
    ter = stato.dict_TER
    for k in ter:
        ter[k] = ter[k] - t_now

    #  Dictionary of the TCr times for each extruder
    tcr = {}

    for e in stato.estrusori:
        mask_est_que = ((stato.df_OP['estrusore'] == e)
                        & ((stato.df_OP['stato'] == 'D')
                           | (stato.df_OP['stato'] == 'G')
                           | (stato.df_OP['stato'] == 'M')
                           | (stato.df_OP['stato'] == 'B')))
        df_est_que = stato.df_OP[mask_est_que]
        est_que_time = np.sum(df_est_que['TE'])
        tcr[e] = est_que_time

    #  Dictionary of mp with time to pick
    mp_time = pd.Series.to_dict(stato.df_giacenza['time_pick'])

    #  Dictionary of mp quantity in stock
    mp_qta = pd.Series.to_dict(stato.df_giacenza['qta'])

    #  Dictionary of mix for each dosaggio
    mix = {}
    for e in df_dos.index:
        mix[e] = {}
        for i in range(1, 16):
            codice = 'cod.i' + str(i)
            peso = 'kg.i' + str(i)
            if (df_dos.loc[e, codice] != ''
                and df_dos.loc[e, codice] != ' '
                    and df_dos.loc[e, codice] is not None):
                mix[e][df_dos.loc[e, codice]] = df_dos.loc[e, peso]
            else:
                break

    # Create the 'prob' variable to contain the problem data
    prob = lp.LpProblem("The complete sequencing Problem", lp.LpMinimize)
    #  ---------------------

    # A dictionary is created to contain the referenced Variables
    arcs = [(d, c) for c in containers for d in df_dos['estrusore']]
    variables = lp.LpVariable.dicts(
        "Couples", (df_dos['estrusore'], containers), 0, None, lp.LpInteger)
    #  ------------------

    #  Define lists with values for objective function
    color_obj = [((colors_d[d] - colors_c[c]) + (valcroms_d[d] -
                  valcroms_c[c])) * variables[d][c] for (d, c) in arcs]
    color_obj = np.multiply(color_obj, coeff_con)

    time_obj = [(ter[d] + tcr[d] - time_d[d]) * variables[d][c]
                for (d, c) in arcs]
    time_obj = np.multiply(time_obj, coeff_time)

    time_pick_obj = [(np.sum(mp_time[x] for x in mix[d]))
                     * variables[d][c] for (d, c) in arcs]
    time_pick_obj = np.multiply(time_obj, coeff_mir)

    objective = time_obj + color_obj + time_pick_obj
    #  --------------------

    # The objective function is added to 'prob' first
    prob += (lp.lpSum(objective),
             "Total delta color/time/picking ",
             )
    #  ------------------
    # The constraints are added to 'prob'
    prob += lp.lpSum([variables[d][c]
                      for d in df_dos['estrusore'] for c in containers]) == 1, "Single choice"

    for d in df_dos['estrusore']:
        for c in containers:
            mask_ext = stato.df_coni['estrusore'] == d
            df_con_ext = stato.df_coni[mask_ext]
            tot = len(df_con_ext)
            prob += ((variables[d][c] * tot <= 2),
                     "Vincolo di coni x ext{}".format(str(d + c)),
                     )

    i = 0
    for d in df_dos['estrusore']:
        for c in containers:
            i += 1
            prob += (variables[d][c] >= 0,
                     str(i),
                     )

    for d in df_dos['estrusore']:
        for c in containers:
            prob += ((variables[d][c] * colors_d[d] >= variables[d][c]
                     * colors_c[c]),
                     "Vincolo di colore{}".format(str(d + c)),
                     )

    for d in df_dos['estrusore']:
        for c in containers:
            prob += ((variables[d][c] * valcroms_d[d] >= variables[d][c]
                     * valcroms_c[c]),
                     "Vincolo di valcrom{}".format(str(d + c)),
                     )

    for d in df_dos['estrusore']:
        for c in containers:
            for m in mix[d]:
                prob += ((variables[d][c] * mix[d][m] <= variables[d][c]
                         * mp_qta[m]),
                         "Vincolo di quantità stock{}".format(str(d + c + m)),
                         )
    #  ---------------------

    # The problem is solved using PuLP's choice of Solver
    prob.solve()

    if lp.LpStatus[prob.status] == 'Optimal':
        # Optimum arc is memorized in two variables
        for v in prob.variables():
            if v.varValue == 1:
                dos = v.name[8:10]
                con = v.name[11:]
                id_dos = df_dos.loc[dos, 'ID']
    else:
        print('Infeasible')
    #  ------------------------

    return(id_dos, con)
