from matplotlib import pyplot as plt
import seaborn as sns
import numpy as np
sns.set()


def aggiorna_timestamp_dosaggi(self, dict_timestamp_dosaggi):
    dict_timestamp_dosaggi['ID'].append(self.ID)
    dict_timestamp_dosaggi['estrusore'].append(self.estrusore)
    dict_timestamp_dosaggi['RFID'].append(self.cono.rfid)
    dict_timestamp_dosaggi['stazione'].append(self.staz_call.n)
    dict_timestamp_dosaggi['kg_cono'].append(self.kg)
    dict_timestamp_dosaggi['richiesta_cono'].append(
        np.round(self.richiesta_cono, 2))
    dict_timestamp_dosaggi['inizio_dosatura'].append(
        np.round(self.inizio_dosatura, 2))
    dict_timestamp_dosaggi['fine_dosatura'].append(
        np.round(self.fine_dosatura, 2))
    dict_timestamp_dosaggi['t_dosaggio'].append(self.fine_dosatura
                                                - self.inizio_dosatura)
    dict_timestamp_dosaggi['inizio_miscelazione'].append(np.round(
        self.inizio_miscelazione, 2))
    dict_timestamp_dosaggi['fine_miscelazione'].append(
        np.round(self.fine_miscelazione, 2))
    dict_timestamp_dosaggi['ingresso_handlingest'].append(np.round(
        self.ingresso_handlingest, 2))
    dict_timestamp_dosaggi['fine_handlingest'].append(
        np.round(self.fine_handlingest, 2))
    dict_timestamp_dosaggi['ingresso_buffer'].append(
        np.round(self.ingresso_buffer, 2))
    dict_timestamp_dosaggi['inizio_estrusione'].append(
        np.round(self.inizio_estrusione, 2))
    dict_timestamp_dosaggi['fine_estrusione'].append(
        np.round(self.fine_estrusione, 2))
    dict_timestamp_dosaggi['t_tot'].append(self.fine_estrusione
                                           - self.richiesta_cono)
    return(dict_timestamp_dosaggi)


def aggiorna_timestamp_picking(self, dict_timestamp_picking):
    dict_timestamp_picking['veicolo'].append(self.veicolo)
    dict_timestamp_picking['n_mission'].append(self.n_mission)
    dict_timestamp_picking['codice'].append(self.cod_pick)
    dict_timestamp_picking['richiesta'].append(
        np.round(self.richiesta, 2))
    dict_timestamp_picking['partenza'].append(np.round(self.partenza, 2))
    dict_timestamp_picking['scarico'].append(np.round(self.scarico, 2))
    return(dict_timestamp_picking)


def aggiorna_timestamp_mir500(self, dict_timestamp_mir500):
    dict_timestamp_mir500['veicolo'].append(self.veicolo)
    dict_timestamp_mir500['n_mission'].append(self.n_mission)
    if self.mission == 'stazione dosaggio':
        dict_timestamp_mir500['mission'].append(self.dosaggio.ID)
    else:
        dict_timestamp_mir500['mission'].append(self.mission)
    dict_timestamp_mir500['cono'].append(self.cono.rfid)
    dict_timestamp_mir500['richiesta'].append(np.round(self.richiesta, 2))
    dict_timestamp_mir500['partenza'].append(np.round(self.partenza, 2))
    dict_timestamp_mir500['scarico'].append(np.round(self.scarico, 2))
    dict_timestamp_mir500['t_tot'].append(np.round(
        (self.scarico - self.richiesta), 2))

    return(dict_timestamp_mir500)


def aggiorna_timestamp_pulizie(self, dict_timestamp_pulizie):
    dict_timestamp_pulizie['cono'].append(self.cono)
    dict_timestamp_pulizie['cono_cicli'].append(self.cono_cicli)
    dict_timestamp_pulizie['richiesta_cono'].append(
        np.round(self.richiesta_cono, 2))
    dict_timestamp_pulizie['inizio_pulizia'].append(
        np.round(self.inizio_pulizia, 2))
    dict_timestamp_pulizie['fine_pulizia'].append(
        np.round(self.fine_pulizia, 2))
    dict_timestamp_pulizie['scarico_cono'].append(
        np.round(self.scarico_cono, 2))
    dict_timestamp_pulizie['t_tot'].append(
        np.round(self.scarico_cono - self.richiesta_cono, 2))
    return(dict_timestamp_pulizie)


def kg_cum(dict_t, now, kg, est):
    ore = now / 60
    dict_t['time'].append(ore)
    if est == 'staz.dosaggio':
        dict_t['tot'].append((dict_t['tot'][-1]))
    else:
        dict_t['tot'].append((kg + dict_t['tot'][-1]))
    dict_t[est].append((kg + dict_t[est][-1]))
    for e in ['staz.dosaggio', 'E1', 'E2', 'E3', 'E4',
              'E5', 'E6', 'E7', 'E8', 'E9']:
        if e != est:
            dict_t[e].append(dict_t[e][-1])
    return(dict_t)


def plot_throughput(dict_t):
    for k in dict_t.keys():
        if k != 'time':
            for i in range(len(dict_t[k])):
                if i != 0:
                    if dict_t['time'][i] != 0:
                        dict_t[k][i] = dict_t[k][i] / dict_t['time'][i]

    plt.figure(figsize=(16, 9), dpi=300)
    for k in dict_t.keys():
        if k != 'time':
            plt.plot(dict_t['time'], dict_t[k], label=k)
    plt.ylabel('Throughput')
    plt.xlabel('Tempo [h]')
    plt.legend()
    return()


def plot_quetot(dict_elements):
    plt.figure(figsize=(16, 9), dpi=300)
    plt.plot(dict_elements['time'], dict_elements['elements'])
    m = np.mean(dict_elements['elements'])
    mean_array = [m for x in range(len(dict_elements['time']))]
    plt.plot(dict_elements['time'], mean_array)
    plt.ylim(0, 30)
    plt.ylabel('Elementi nel sistema')
    plt.xlabel('Tempo [h]')
