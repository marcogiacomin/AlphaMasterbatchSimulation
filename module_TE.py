'''ARGOMENTI DA PASSARE ALLA FUNZIONE
dict_stat ---> dizionario contenente tutto l'OP
dict_speed --> con keys i nomi degli estrusori e values tuple
                con dentro al primo posto la velocità in lento
                al secondo posto la velocità in rapido
                unità di misura Kg/h
dense_probability --> rappresenta la probabilità che una mescola sia densa
                        quindi che abbia la necessità di essere estrusa a
                        velocità ridotta rispetto al normale
'''

from random import randint

dense_probability = 50
dict_speed = {'E1': (27, 73),
              'E2': (34, 66),
              'E3': (41, 55),
              'E4': (36, 61),
              'E5': (44, 77),
              'E6': (44, 77),
              'E7': (44, 77),
              'E8': (25, 58),
              'E9': (25, 58),
              'FL': (100, 100),
              'M1': (100, 100), }


def calc_TE(dict_stat):
    global dict_speed

    for idx in range(len(dict_stat['statino'])):
        dense = False
        if randint(0, 100) < dense_probability:
            dense = True
        if dense:
            speed = dict_speed[dict_stat['estrusore'][idx]][0] / 60
        else:
            speed = dict_speed[dict_stat['estrusore'][idx]][1] / 60
        TE = dict_stat['kg_cono'][idx] / speed
        dict_stat['TE'].append(TE)
    return(dict_stat)
