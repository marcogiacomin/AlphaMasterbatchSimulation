import pandas as pd


def func_calc_que(par_que, estrusori, dict_TER, t, df_OP):
    df_pre_seq = df_OP.sort_values(['estrusore', 'data', 'ordine']).copy()
    len_que = 1
    for _ in range(par_que):
        # dizionario per calcolare la coda (tmp)
        dict_calc = {
            'ID': [],
            'estrusore': [],
            'statino': [],
            'codice': [],
            'ass_cono': [],
            'n_cono': [],
            'coni': [],
            'kg_cono': [],
            'TD': [],
            'TE': [],
            'color': [],
            'valcrom': [],
            'ordine': [],
            'stato': [],
            'ord_dos': [],
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
                    # non riempie la key 'TU'
                    if key != 'TU':
                        dict_calc[key].append(dict_tmp[key])

        # calcola TU ed estrae ID del più urgente
        for i in range(len(dict_calc['ID'])):
            # calcola TU facendo riferimento al tempo ETA per l'estrusore
            tu_tmp = (
                dict_TER[dict_calc['estrusore'][i]] - t - dict_calc['TD'][i])

            # prende il tempo di tutti i coni in coda sull'estrusore
            mask = (((df_pre_seq['stato'] == 'C')
                    | (df_pre_seq['stato'] == 'D')
                    | (df_pre_seq['stato'] == 'M')
                    | (df_pre_seq['stato'] == 'B'))
                    & (df_pre_seq['estrusore'] == dict_calc['estrusore'][i]))
            # somma a TU il tempo TE dei coni in coda
            tu_tmp = tu_tmp + df_pre_seq[mask]['TE'].sum()

            dict_calc['TU'].append(tu_tmp)

        # trova la posizione in lista del TU minimo
        i_min = dict_calc['TU'].index(min(dict_calc['TU']))
        most_urgent_id = dict_calc['ID'][i_min]  # estra ID del TU minimo

        # modifica nel df originale il TU dell'ID mandato in coda
        df_pre_seq.loc[most_urgent_id, 'TU'] = tu_tmp

        # modifica nel df originale lo stato dell'ID mandato in coda
        df_pre_seq.loc[most_urgent_id, 'stato'] = 'C'

        # assegnazione ordine dell'ID mandato in coda
        df_pre_seq.loc[most_urgent_id, 'ord_dos'] = len_que
        len_que = len_que + 1

    # dataframe con la coda valida in questo istante di tempo
    df_seq = df_pre_seq[df_pre_seq['stato'] == 'C'].sort_values('ord_dos')

    # elimina dalla coda i coni di ordine maggiore per ogni estrusore
    # serve per fa rimanere invariata la coda sull'estrusore
    for est in estrusori:
        mask_est = (df_seq['estrusore'] == est)
        ord_min = df_seq[mask_est]['ordine'].min()
        mask_drop = (df_seq['estrusore'] == est) & (
            df_seq['ordine'] > ord_min)
        df_seq = df_seq.drop(df_seq[mask_drop].index)
    return (df_seq)
