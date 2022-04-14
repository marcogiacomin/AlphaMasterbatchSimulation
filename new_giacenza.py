import pandas as pd

import glob
import os

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

dict_mp = dict.fromkeys(mp_list)
dict_sl = dict.fromkeys(sl_list)
#  ------------------------

#  creazione bulk storage materie prime
df_mp = pd.DataFrame.from_dict(dict_mp, orient='index', columns=['posizione'])

df_mp.drop(index=df_mp.index[0], axis=0, inplace=True)

df_mp['posizione'] = range(0, len(df_mp))
df_mp['time_pick'] = None
df_mp['qta'] = 500
df_mp['zona'] = 'M'

sections = 10
containers_in_section = len(df_mp) / sections
dict_times = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5,
              6: 1, 7: 2, 8: 3, 9: 4, 10: 5}

#  definizione del tempo di picking in funzione della posizione in magazzino
for section, time in dict_times.items():
    for idx in df_mp.index:
        if (df_mp.loc[idx, 'posizione'] <= (section * containers_in_section)
                and df_mp.loc[idx, 'posizione'] >= ((section - 1) * containers_in_section)):
            df_mp.loc[idx, 'time_pick'] = time
        elif df_mp.loc[idx, 'posizione'] > section * containers_in_section:
            break

i = 0
for mp in df_mp.index:
    df_mp.loc[mp, 'time_pick'] = 0
    i += 1
    if i == 4:
        break

#  creazione magrob per semilavorati
df_sl = pd.DataFrame.from_dict(dict_sl, orient='index', columns=['posizione'])
df_sl['posizione'] = range(0, len(df_sl))
df_sl['qta'] = 100
df_sl['zona'] = 'M'
df_sl.iloc[0, 2] = 'S'
# ----------------------
