import glob
import os
import numpy as np
import pandas as pd
from random import randint
from datetime import datetime

import module_TE
import module_TD

path_folder_statini = "C:/Users/HP/Desktop/statini/*"
op_folder = "C:/Users/HP/Desktop/OP/*"


def func_OP(path_folder_statini, op_folder, secondi_cambio_tool,
            mass_v, mass_f, pig_v, pig_f):
    # Dichiarazione dizionario per memorizzazione statini
    dict_stat = {
        'estrusore': [],
        'statino': [],
        'codice': [],
        'n_cono': 1,
        'coni': [],
        'kg_cono': [],
        'TD': [],
        'TE': [],
        'color': [],
        'valcrom': [],
        'ord_dos': None,
        'stato': 'O',
        'cod.i1': [], 'fp.i1': [], 'dex.i1': [], 'kg.i1': [],
        'cod.i2': [], 'fp.i2': [], 'dex.i2': [], 'kg.i2': [],
        'cod.i3': [], 'fp.i3': [], 'dex.i3': [], 'kg.i3': [],
        'cod.i4': [], 'fp.i4': [], 'dex.i4': [], 'kg.i4': [],
        'cod.i5': [], 'fp.i5': [], 'dex.i5': [], 'kg.i5': [],
        'cod.i6': [], 'fp.i6': [], 'dex.i6': [], 'kg.i6': [],
        'cod.i7': [], 'fp.i7': [], 'dex.i7': [], 'kg.i7': [],
        'cod.i8': [], 'fp.i8': [], 'dex.i8': [], 'kg.i8': [],
        'cod.i9': [], 'fp.i9': [], 'dex.i9': [], 'kg.i9': [],
        'cod.i10': [], 'fp.i10': [], 'dex.i10': [], 'kg.i10': [],
        'cod.i11': [], 'fp.i11': [], 'dex.i11': [], 'kg.i11': [],
        'cod.i12': [], 'fp.i12': [], 'dex.i12': [], 'kg.i12': [],
        'cod.i13': [], 'fp.i13': [], 'dex.i13': [], 'kg.i13': [],
        'cod.i14': [], 'fp.i14': [], 'dex.i14': [], 'kg.i14': [],
        'cod.i15': [], 'fp.i15': [], 'dex.i15': [], 'kg.i15': [],
    }

    # queste chiavi non devono essere riempite con le info da statino
    # chiavi del dizionario non comprese nello statino
    key_out_stat = ['n_cono', 'TD', 'TE', 'color',
                    'valcrom', 'stato', 'ord_dos']

    # rimepimento dizionario
    # importazione statini uno alla volta
    for filename in glob.glob(path_folder_statini):
        with open(os.path.join(os.getcwd(), filename), 'r') as f:
            stat_str = f.read()
            list_str = stat_str.split(';')
            idx = 0
            for k in dict_stat.keys():
                if k not in key_out_stat:
                    dict_stat[k].append(list_str[idx].strip())
                    idx += 1

    # Conversione tipi
    for x in range(len(dict_stat['kg_cono'])):
        dict_stat['kg_cono'][x] = int(
            dict_stat['kg_cono'][x].replace(',', '')) / 100
        dict_stat['coni'][x] = int(dict_stat['coni'][x])

    fasi = ['01', '02', '03', '04']
    fase = 'fp.i'
    peso = 'kg.i'
    for ingrediente in range(1, 16):
        key_fase = fase + str(ingrediente)
        key_peso = peso + str(ingrediente)

        for x in range(len(dict_stat[key_fase])):
            if dict_stat[key_fase][x] not in fasi:
                dict_stat[key_fase][x] = 0
            else:
                dict_stat[key_fase][x] = int(dict_stat[key_fase][x])

        for x in range(len(dict_stat[key_peso])):
            dict_stat[key_peso][x] = int(
                dict_stat[key_peso][x].replace(',', '')) / 1000000

    #  -----------------------------------------
    # dizionario per memorizzare OP di Vignolini
    dict_op = {}

    key = 0
    for filename in glob.glob(op_folder):
        op = open(filename)
        date = datetime.strptime(str(filename[-14:]), '%Y%m%d%H%M%S')
        for line in op:
            list_line = line.split(';')
            dict_op[key] = []
            dict_op[key].append(list_line[2])
            dict_op[key].append(list_line[0])
            dict_op[key].append(list_line[1])
            dict_op[key].append(date.strftime('%Y/%m/%d %H:%M:%S'))
            key += 1
    #  ----------------------------------------

    # Crea le colonne da riempire dopo, devono avere lunghezza uniforme
    # altrimenti darà errore quando si va fare il df
    for x in dict_stat['statino']:
        dict_stat['color'].append(None)
        dict_stat['valcrom'].append(None)
    #  -----------------------------------------

    #  funzione calcolo TD in base ai parametri passati in simulazione
    dict_stat = module_TD.calc_TD(dict_stat, secondi_cambio_tool,
                                  mass_v, mass_f, pig_v, pig_f)
    #  funzione calcolo TE in base ai parametri passati in simulazione
    dict_stat = module_TE.calc_TE(dict_stat)

    # crea due df
    df_stat = pd.DataFrame.from_dict(dict_stat)

    #  --------------------------------------
    # converte l'OP in dataframe
    df_op = pd.DataFrame.from_dict(dict_op, orient='index',
                                   columns=['statino', 'estrusore',
                                            'ordine', 'data'])
    df_op['data'] = pd.to_datetime(
        df_op['data'], format='%Y/%m/%d %H:%M:%S')  # .dt.strftime('%Y/%m/%d')

    # riempie la colonna color e valcrom
    for est in set(dict_stat['estrusore']):
        color = randint(0, 50)
        valcrom = randint(0, 120)
        for i in df_stat.index:
            if df_stat.loc[i, 'estrusore'] == est:
                df_stat.loc[i, 'color'] = color
                df_stat.loc[i, 'valcrom'] = valcrom

    # unisce i df sulla base dello statino e dell'estrusore
    df_stat = df_stat.merge(df_op, on=['estrusore', 'statino']).sort_values(
        by=['estrusore', 'data', 'ordine', ], ascending=True)
    df_stat.drop_duplicates(subset='statino', inplace=True, keep='first')

    df_stat = df_stat.loc[df_stat.index.repeat(
        df_stat.coni)].reset_index(drop=True)

    for i in df_stat.index:
        if i != 0:
            if df_stat.loc[i, 'coni'] > 1 and df_stat.loc[i, 'statino'] == df_stat.loc[i - 1, 'statino']:
                df_stat.loc[i, 'n_cono'] = df_stat.loc[i - 1, 'n_cono'] + 1
        else:
            continue

    df_stat.index = (df_stat['n_cono'].astype(str)
                     + '-'
                     + df_stat['coni'].astype(str)
                     + df_stat['estrusore']
                     + df_stat['statino'])

    df_stat['ID'] = df_stat.index

    #  -----------------------------------------
    #  rimuovo statini relativi ad estrusori che non sono di nostro interesse
    mask_drop = np.asarray(
        df_stat[~df_stat['estrusore'].isin(['E' + str(n) for n in range(1, 10)])].index)
    df_stat.drop(mask_drop, inplace=True)

    return(df_stat)
