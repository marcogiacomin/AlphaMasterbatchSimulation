import pandas as pd

import glob
import os


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

dict_giacenza = dict.fromkeys(codes)


df_giacenza = pd.DataFrame.from_dict(dict_giacenza, orient='index',
                                     columns=['posizione'])

df_giacenza.drop(index=df_giacenza.index[0],
                 axis=0,
                 inplace=True)

df_giacenza['posizione'] = range(0, len(df_giacenza))
df_giacenza['qta'] = 500
df_giacenza['time_pick'] = 4

#  definizione del tempo di picking in funzione della posizione in magazzino
for i in df_giacenza.index:
    if df_giacenza.loc[i, 'posizione'] <= 103 and df_giacenza.loc[i, 'posizione'] > 13:
        df_giacenza.loc[i, 'time_pick'] = 3
    elif df_giacenza.loc[i, 'posizione'] <= 13 and df_giacenza.loc[i, 'posizione'] > 3:
        df_giacenza.loc[i, 'time_pick'] = 1
    elif df_giacenza.loc[i, 'posizione'] < 4:
        df_giacenza.loc[i, 'time_pick'] = 0
