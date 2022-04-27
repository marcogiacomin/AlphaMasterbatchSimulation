import math
import random


def calc_TD(d, secondi_cambio_tool, mass_v, mass_f, pig_v, pig_f):
    pesi = [('kg.i' + str(n)) for n in range(1, 15)]

    t_tool = secondi_cambio_tool / 60  # conversione in minuti
    t_mass_v = mass_v / 60
    t_mass_f = mass_f / 60
    t_pig_v = pig_v / 60
    t_pig_f = pig_f / 60

    pal_pig = 1
    pal_mass = 2

    for i in range(len(d['statino'])):
        tmp_TD = 0
        for k in pesi:
            first_pesata = True
            #  se pesa meno di 2.5kg ipotizzo sia un pigmento
            if d[k][i] <= 2.5 and d[k][i] > 0:
                tmp_TD += t_tool
                tmp_TD += (math.floor(d[k][i] / (
                    pal_pig * (random.randrange(80, 100) / 100))) - 1) * t_pig_v
                tmp_TD += 2 * t_pig_f
            elif d[k][i] > 2.5 and d[k][i] > 0:  # altrimenti ipotizzo sia un massivo
                tmp_TD += t_tool
                tmp_TD += (math.floor(d[k][i] / (
                    pal_mass * (random.randrange(80, 100) / 100))) - 1) * t_mass_v
                tmp_TD += 2 * t_mass_f
        d['TD'].append(tmp_TD)
    return(d)
