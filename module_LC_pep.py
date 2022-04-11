import numpy as np
import pandas as pd

'''
questa funzione riempie la colonna LC del df_coda
calcola il livello di comunanza di ogni cono in coda
in relazione alla fotografia attuale del buffer e dei cassoni in stazione
'''


def func_LC(df_coda, df_giacenza):
    codici = [('cod.i' + str(n)) for n in range(1, 16)]

    df_coda['LC'] = 0

    df_buff = df_giacenza[df_giacenza['posizione'] == 'B']
    df_staz = df_giacenza[df_giacenza['posizione'] == 'S']

    for c in df_coda.index:
        n_ric = 0
        ing_ric = []
        LC = 0
        for i in codici:
            if (df_coda.loc[c, i] != 0
                and df_coda.loc[c, i] is not None
                    and df_coda.loc[c, i] != ''
                    and len(df_coda.loc[c, i]) > 2):
                n_ric += 1
                ing_ric.append(df_coda.loc[c, i])
        len_ric = len(set(ing_ric))
        sum_list = list(set(ing_ric)) + list(df_buff.index)
        tmp_buff = len(sum_list) - len(set(sum_list))
        sum_list = list(set(ing_ric)) + list(df_staz.index)
        tmp_staz = len(sum_list) - len(set(sum_list))
        # peso relativo tra buffer e stazione messo a caso per ora
        LC = np.round(((tmp_buff / len_ric) * 0.25 +
                      (tmp_staz / len_ric) * 0.75) * 100, 2)
        df_coda.loc[c, 'LC'] = LC
        df_coda.sort_values('TU', inplace=True)

    return(df_coda)


'''
questa funzione restituisce il miglior cono da dosare
prende come input la coda e la riordina tenendo conto del LC
verifica che il riordino non causi una violazione dei vincoli di tempo.
Se la coda è formata da tutti coni assegnati allo stesso estrusore prende
direttamente il primo senza entrare nell'algoritmo
'''


def func_best_dosaggio(df_coda, dict_TER, t):
    # se entra nel loop con una coda con un solo elemento da errore
    if len(df_coda['estrusore'].unique()) > 1:
        df_tmp1 = df_coda.copy().sort_values(
            ['LC', 'ord_dos'], ascending=[False, True])
        df_tmp2 = df_coda.copy()
        bol = True

        if len(df_tmp1['TU'].unique()) == 1:
            best = pd.DataFrame(df_tmp1.iloc[0, :]).T
        else:

            # calcola il miglior cono data la coda attuale
            while bol and len(df_tmp1) > 0:
                df_tmp2.drop([df_tmp1.iloc[0, :]['ID']],
                             axis='index', inplace=True)
                df_tmp2 = pd.concat(
                    [pd.DataFrame(df_tmp1.iloc[0, :]).T, df_tmp2])

                list_TU = list(df_tmp2['TU'])
                list_TD = list(df_tmp2['TD'])

                for i in range(len(list_TU)):
                    # verifica violazione vincolo temporale
                    est_i = df_tmp2.iloc[i, 0]
                    int_ETA = dict_TER[est_i] - t
                    if list_TU[i] < int_ETA + sum(list_TD[: i]):
                        bol = False
                if bol:
                    best = pd.DataFrame(df_tmp1.iloc[0, :]).T
                    bol = False
                else:
                    df_tmp1.drop([df_tmp1.iloc[0, :]['ID']],
                                 axis='index', inplace=True)
                    bol = True

            # se non ha trovato niente tiene al primo posto il cono soddisfa TU
            if len(df_tmp1) == 0:
                best = pd.DataFrame(df_coda.iloc[0, :]).T
    else:
        best = pd.DataFrame(df_coda.iloc[0, :]).T

    # elimina dalla coda il cono estratto
    df_coda.drop(best['ID'][0], axis='index', inplace=True)
    return(best)
