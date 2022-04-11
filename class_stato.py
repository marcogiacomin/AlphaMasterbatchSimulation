import pandas as pd
import new_giacenza
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
              'tool': 1,  # 1 paletta piccola, 2 paletta grande
              'par_que': 10,  # quanti elementi mettere in coda nell'algoritmo
              'max_cicli': 1,  # massimi cicli di utilizzo di un cono
              }

data = {'df_coni': pd.read_csv(r"C:\Users\HP\Desktop\mag_coni.csv",
                               sep=';', index_col='RFID'),
        'df_giacenza': new_giacenza.df_giacenza,
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
                                        'destinazione': [],
                                        'richiesta': [],
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


# definisco la classe stato
class Stato():
    def __init__(self, parameters, variables, data):
        self.t_tool = parameters['t_tool']
        self.t_mass_v = parameters['t_mass_v']
        self.t_mass_f = parameters['t_mass_f']
        self.t_pig_v = parameters['t_pig_v']
        self.t_pig_f = parameters['t_pig_f']
        self.tool = parameters['tool']
        self.par_que = parameters['par_que']
        self.max_cicli = parameters['max_cicli']

        self.df_coni = data['df_coni']
        self.df_giacenza = data['df_giacenza']
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

a = pd.Series.to_dict(stato.df_giacenza['qta'])
