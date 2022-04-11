#  from class_stato import stato
import pandas as pd


def func_calc_que(estrusori, dict_TER, t, df_OP):
    df_pre_seq = df_OP.sort_values(['estrusore', 'data', 'ordine']).copy()
    # dizionario per calcolare la coda (tmp)
    dict_calc = {
        'ID': [],
        'estrusore': [],
        'statino': [],
        'codice': [],
        'n_cono': [],
        'coni': [],
        'kg_cono': [],
        'TD': [],
        'TE': [],
        'color': [],
        'valcrom': [],
        'ordine': [],
        'stato': [],
        'TU': [],
        'data': [],
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

    # riempie il dizionario con il primo cono in stato ORDINATO
    for est in estrusori:
        mask = (df_pre_seq['estrusore'] == est) & (
            df_pre_seq['stato'] == 'O')
        df_tmp = df_pre_seq[mask]
        if len(df_tmp) > 0:
            dict_tmp = pd.Series.to_dict(df_tmp.iloc[0, ])
            for key in dict_tmp:
                # non riempie le key che non sono nel nuovo diz
                if key not in ['TU', 'ord_dos', 'ass_cono']:
                    dict_calc[key].append(dict_tmp[key])

    # calcola TU ed estrae ID del più urgente
    for i in range(len(dict_calc['ID'])):
        # calcola TU facendo riferimento al tempo ETA per l'estrusore
        estrusore = dict_calc['estrusore'][i]
        tu_tmp = (dict_TER[estrusore] - t - dict_calc['TD'][i])

        # prende il tempo di tutti i coni in coda sull'estrusore
        mask = (((df_pre_seq['stato'] == 'C')
                | (df_pre_seq['stato'] == 'D')
                | (df_pre_seq['stato'] == 'M')
                | (df_pre_seq['stato'] == 'B'))
                & (df_pre_seq['estrusore'] == dict_calc['estrusore'][i]))
        # somma a TU il tempo TE dei coni in coda
        tu_tmp = tu_tmp + df_pre_seq[mask]['TE'].sum()

        dict_calc['TU'].append(tu_tmp)

    df_seq = pd.DataFrame.from_dict(
        dict_calc, orient='columns').sort_values('TU')
    return (df_seq)


'''df_coda = func_calc_que(
    stato.estrusori,
    stato.dict_TER, 10,
    stato.df_OP)'''
