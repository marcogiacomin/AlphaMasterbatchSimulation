import pandas as pd
from class_stato import stato


# definisco la classe cono
class Cono():
    def __init__(self, rfid, df_coni):
        self.rfid = rfid
        self.color = df_coni.loc[rfid, 'color']
        self.valcrom = df_coni.loc[rfid, 'valcrom']
        self.stato = df_coni.loc[rfid, 'stato']
        self.posizione = df_coni.loc[rfid, 'posizione']
        self.cicli = df_coni.loc[rfid, 'cicli']
        self.estrusore = None
        self.coda_pul = False


# funzione per aggiornare il dataframe dei coni a valle della simulazione
def update_df_coni(obj_coni):
    d = {'rfid': [], 'color': [], 'valcrom': [], 'stato': [],
         'posizione': [], 'cicli': [], 'estrusore': []}
    for cono in obj_coni:
        d['rfid'].append(cono.rfid)
        d['color'].append(cono.color)
        d['valcrom'].append(cono.valcrom)
        d['stato'].append(cono.stato)
        d['posizione'].append(cono.posizione)
        d['cicli'].append(cono.cicli)
        d['estrusore'].append(cono.estrusore)
    df_updated = pd.DataFrame.from_dict(d, orient='columns').set_index('rfid')
    return(df_updated)


# creo tutti i 24 oggetti cono
C1 = Cono(rfid='C1', df_coni=stato.df_coni)
C2 = Cono(rfid='C2', df_coni=stato.df_coni)
C3 = Cono(rfid='C3', df_coni=stato.df_coni)
C4 = Cono(rfid='C4', df_coni=stato.df_coni)
C5 = Cono(rfid='C5', df_coni=stato.df_coni)
C6 = Cono(rfid='C6', df_coni=stato.df_coni)
C7 = Cono(rfid='C7', df_coni=stato.df_coni)
C8 = Cono(rfid='C8', df_coni=stato.df_coni)
C9 = Cono(rfid='C9', df_coni=stato.df_coni)
C10 = Cono(rfid='C10', df_coni=stato.df_coni)
C11 = Cono(rfid='C11', df_coni=stato.df_coni)
C12 = Cono(rfid='C12', df_coni=stato.df_coni)
C13 = Cono(rfid='C13', df_coni=stato.df_coni)
C14 = Cono(rfid='C14', df_coni=stato.df_coni)
C15 = Cono(rfid='C15', df_coni=stato.df_coni)
C16 = Cono(rfid='C16', df_coni=stato.df_coni)
C17 = Cono(rfid='C17', df_coni=stato.df_coni)
C18 = Cono(rfid='C18', df_coni=stato.df_coni)
C19 = Cono(rfid='C19', df_coni=stato.df_coni)
C20 = Cono(rfid='C20', df_coni=stato.df_coni)
C21 = Cono(rfid='C21', df_coni=stato.df_coni)
C22 = Cono(rfid='C22', df_coni=stato.df_coni)
C23 = Cono(rfid='C23', df_coni=stato.df_coni)
C24 = Cono(rfid='C24', df_coni=stato.df_coni)

C25 = Cono(rfid='C25', df_coni=stato.df_coni)
C26 = Cono(rfid='C26', df_coni=stato.df_coni)
C27 = Cono(rfid='C27', df_coni=stato.df_coni)
C28 = Cono(rfid='C28', df_coni=stato.df_coni)
C29 = Cono(rfid='C29', df_coni=stato.df_coni)
C30 = Cono(rfid='C30', df_coni=stato.df_coni)

# lista di oggetti cono che verrà usata dal simulatore
obj_coni = [C1, C2, C3, C4, C5, C6, C7, C8, C9, C10, C11, C12,
            C13, C14, C15, C16, C17, C18, C19, C20, C21, C22,
            C23, C24] #, C25, C26, C27, C28, C29, C30]
