import pandas as pd

import glob
import os
from random import shuffle, randrange

#  importazione statini
path_folder_statini = "C:/Users/HP/Desktop/statini/*"

dict_stat = {
    'estrusore': [],
    'statino': [],
    'codice': [],
    'coni': [],
    'kg_cono': [],
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

# rimepimento dizionario
# importazione statini uno alla volta
for filename in glob.glob(path_folder_statini):
    with open(os.path.join(os.getcwd(), filename), 'r') as f:
        stat_str = f.read()
        list_str = stat_str.split(';')
        idx = 0
        for k in dict_stat.keys():
            dict_stat[k].append(list_str[idx].strip())
            idx += 1

all_code = []
for i in [('cod.i' + str(n)) for n in range(1, 16)]:
    all_code.extend(dict_stat[i])

codes = list(set(all_code))
mp_list = []
sl_list = []

for c in codes:
    if c == '':
        pass
    elif c[0] == '5':
        sl_list.append(c)
    else:
        mp_list.append(c)

#  shuffle of mp to simulate a random allocation of codes
shuffle(mp_list)

dict_mp = dict.fromkeys(mp_list)
dict_sl = dict.fromkeys(sl_list)
#  ------------------------

#  creazione bulk storage materie prime
df_mp = pd.DataFrame.from_dict(dict_mp, orient='index', columns=['posizione'])

df_mp['posizione'] = range(0, len(df_mp))
df_mp['sezione'] = None
df_mp['qta'] = 500
df_mp['zona'] = 'M'
df_mp['stato'] = None

i = 0
for mp in df_mp.index:
    df_mp.loc[mp, 'zona'] = 'S'
    df_mp.loc[mp, 'stato'] = 5
    i += 1
    if i == 4:
        break

#  creazione magrob per semilavorati
df_sl = pd.DataFrame.from_dict(dict_sl, orient='index', columns=['posizione'])
df_sl['posizione'] = range(0, len(df_sl))
df_sl['qta'] = 100
df_sl['zona'] = 'M'
df_sl['stato'] = None
df_sl.iloc[0, 2] = 'S'
df_sl.iloc[0, 3] = 5

# questo funzione assegna un numero random alla sezione
# di magazzino in cui si trova il prodotto
def random_section(df, colonna, start, end):
    for i in df_mp.index:
        s = randrange(start, end + 1)
        df.loc[i, colonna] = s
    return(df)

# questa funzione prende in input il df con pareto
# assegna la sezione in funzione del numero di movimentazioni
# che quella materia prima subirà
def pareto_allocation(df_mp):
    df_pareto = pd.read_csv('C:/Users/HP/Desktop/df_pareto_OP.csv',
                            index_col='codice')
    df = df_mp.copy()
    df.sort_index(inplace=True)
    df_pareto.sort_index(inplace=True)
    df['sezione'] = df_pareto['posizione']
    df.fillna(1, inplace=True)
    return(df)
# ----------------------
