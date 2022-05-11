import pandas as pd
from random import shuffle
import ETL_all_OPs


# PATH DEI FILE DA IMPORTARE
path_folder_statini = "C:/Users/HP/Desktop/statini/*"
path_folder_progprod = "C:/Users/HP/Desktop/OP/*"
df_coni = pd.read_csv(r"C:\Users\HP\Desktop\mag_coni.csv",
                      sep=';', index_col='RFID')

# --------------------------------------------------
# Creo i dizionari per l'oggetto stato

# questo dizionario contiene e i parametri di funzionamento della simulazione
parameters = {'t_tool': 15,  # tempo robot cambio tool in secondi
              't_mass_v': 17,
              't_mass_f': 25,
              't_pig_v': 17,
              't_pig_f': 25,  # tempi robot per una palettata in secondi
              'kg_mass': 3,  # capacità paletta massivi
              'kg_pig': 3, #  capacità paletta pigmento
              'max_cicli': 15,  # massimi cicli di utilizzo di un cono
              }

data = {'df_coni': pd.read_csv(r"C:\Users\HP\Desktop\mag_coni.csv",
                               sep=';', index_col='RFID'),
        'df_stock_mp': None,
        'df_stock_sl': None,
        'df_OP': ETL_all_OPs.func_OP(path_folder_statini, path_folder_progprod,
                                     parameters['t_tool'],
                                     mass_v=parameters['t_mass_v'],
                                     mass_f=parameters['t_mass_f'],
                                     pig_v=parameters['t_pig_v'],
                                     pig_f=parameters['t_pig_f']), }

variables = {'elements': 0,  # entità presenti nel sistema all'istante t
             'estrusori': ['E1', 'E2', 'E3',
                           'E4', 'E5', 'E6',
                           'E7', 'E8', 'E9'],
             'dict_TER': {'E1': 0, 'E2': 0, 'E3': 0,
                          'E4': 0, 'E5': 0, 'E6': 0,
                          'E7': 0, 'E8': 0, 'E9': 0},

             # dizionario per verificare la correttezza
             # delle assegnazioni cono/estrusore
             'check': {'E1': [], 'E2': [], 'E3': [],
                       'E4': [], 'E5': [], 'E6': [],
                       'E7': [], 'E8': [], 'E9': []},

             # dizionari di appoggio per l'acquisizione delle statistiche
             'dict_throughput': {'time': [0], 'tot': [0], 'staz.dosaggio': [0],
                                 'E1': [0], 'E2': [0], 'E3': [0],
                                 'E4': [0], 'E5': [0], 'E6': [0],
                                 'E7': [0], 'E8': [0], 'E9': [0], },
             'dict_timestamp_dosaggi': {'ID': [], 'estrusore': [], 'RFID': [],
                                        'stazione': [],
                                        'kg_cono': [],
                                        'richiesta_cono': [],
                                        'inizio_dosatura': [],
                                        'fine_dosatura': [],
                                        't_dosaggio': [],
                                        'inizio_miscelazione': [],
                                        'fine_miscelazione': [],
                                        'ingresso_handlingest': [],
                                        'fine_handlingest': [],
                                        'ingresso_buffer': [],
                                        'inizio_estrusione': [],
                                        'fine_estrusione': [],
                                        't_tot': []},

             'dict_timestamp_picking': {'veicolo': [],
                                        'n_mission': [],
                                        'codice': [],
                                        'richiesta': [],
                                        'disponibilità': [],
                                        'partenza': [],
                                        'scarico': [], },

             'dict_elements': {'time': [], 'elements': []},

             'dict_timestamp_pulizie': {'cono': [],
                                        'cono_cicli': [],
                                        'richiesta_cono': [],
                                        'inizio_pulizia': [],
                                        'fine_pulizia': [],
                                        'scarico_cono': [],
                                        't_tot': []},

             'dict_timestamp_mir500': {'veicolo': [],
                                       'n_mission': [],
                                       'mission': [],
                                       'cono': [],
                                       'richiesta': [],
                                       'partenza': [],
                                       'scarico': [],
                                       't_tot': [], }
             }
# --------------------------------------------------

# in questa sezione creo la giacenza
cod_col = ['cod.i' + str(x) for x in range(1, 16)]
codici = []
for col in cod_col:
    codici.extend(data['df_OP'][col])
    
codes = list(set(codici))
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
df_mp['statonext'] = False

sections = 14
containers_in_section = len(df_mp) / sections

#  definizione della posizione in magazzino
for section in range(0, 14):
    for idx in df_mp.index:
        if (df_mp.loc[idx, 'posizione'] <= (section * containers_in_section)
                and df_mp.loc[idx, 'posizione'] >= ((section - 1) * containers_in_section)):
            if section <= 6:
                df_mp.loc[idx, 'sezione'] = section
            else:
                df_mp.loc[idx, 'sezione'] = section - 6
        elif df_mp.loc[idx, 'posizione'] > section * containers_in_section:
            break
for idx in df_mp.index:
    if df_mp.loc[idx, 'sezione'] is None:
        df_mp.loc[idx, 'sezione'] = 6


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
'''df_sl.iloc[1, 2] = 'S'
df_sl.iloc[1, 3] = 5
df_sl.iloc[2, 2] = 'S'
df_sl.iloc[2, 3] = 5'''



def pareto_allocation(df_mp):
    df_pareto = pd.read_csv('C:/Users/HP/Desktop/df_pareto_OP.csv', index_col='codice')
    df = df_mp.copy()
    df.sort_index(inplace=True)
    df_pareto.sort_index(inplace=True)
    df['sezione'] = df_pareto['posizione']
    df.fillna(1, inplace=True)
   
    return(df)


# definisco la classe stato
class Stato():
    def __init__(self, parameters, variables, data):
        self.t_tool = parameters['t_tool']
        self.t_mass_v = parameters['t_mass_v']
        self.t_mass_f = parameters['t_mass_f']
        self.t_pig_v = parameters['t_pig_v']
        self.t_pig_f = parameters['t_pig_f']
        self.kg_mass = parameters['kg_mass']
        self.kg_pig = parameters['kg_pig']
        self.max_cicli = parameters['max_cicli']

        self.df_coni = data['df_coni']
        #self.df_stock_mp = df_mp
        self.df_stock_mp = pareto_allocation(df_mp)
        self.df_stock_sl = df_sl
        self.df_OP = data['df_OP']

        self.elements = variables['elements']
        self.estrusori = variables['estrusori']
        self.dict_TER = variables['dict_TER']
        self.check = variables['check']
        self.dict_throughput = variables['dict_throughput']
        self.dict_timestamp_dosaggi = variables['dict_timestamp_dosaggi']
        self.dict_timestamp_picking = variables['dict_timestamp_picking']
        self.dict_elements = variables['dict_elements']
        self.dict_timestamp_pulizie = variables['dict_timestamp_pulizie']
        self.dict_timestamp_mir500 = variables['dict_timestamp_mir500']


# creo l'oggetto stato
stato = Stato(parameters, variables, data)
