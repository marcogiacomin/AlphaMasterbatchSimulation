import module_class_cono
import module_stats
import module_que_by_est

import pandas as pd
import salabim as sim
from scipy import stats
from random import random, randint

from module_class_cono import obj_coni
from class_stato import stato
from sim_queue import (obj_buffer, que_staz_dos_1, que_staz_dos_2)

from datetime import datetime
start = datetime.now()

# -------------
# set distributions for service times
d_interarrival = sim.External(stats.burr12, c=1.6510761870773936,
                              d=4.90409753998643,
                              loc=-0.139633281979239,
                              scale=28.18319121005929)
db_interarrival = sim.Bounded(d_interarrival, lowerbound=0, upperbound=60)

d_handlingpes = sim.External(stats.recipinvgauss, mu=982686.023539558,
                             loc=1.133299999996841,
                             scale=3.395239969140169)
db_handlingpes = sim.Bounded(d_handlingpes, lowerbound=0, upperbound=25)

d_pesatura = sim.External(stats.invweibull, c=5.9132736293702335,
                          loc=-18.072017323530094,
                          scale=28.770231959297615)
db_pesatura = sim.Bounded(d_pesatura, lowerbound=0, upperbound=50)

d_miscelatore = sim.External(stats.johnsonsu, a=-0.8549508017162559,
                             b=0.1168327288677157,
                             loc=3.433299997933217,
                             scale=8.458237254897196e-09)
db_miscelatore = sim.Bounded(d_miscelatore, lowerbound=0, upperbound=15)

d_handlingest = sim.External(stats.gennorm, beta=0.19622416287615776,
                             loc=5.15,
                             scale=6.14156557438578e-05)
db_handlingest = sim.Bounded(d_handlingest, lowerbound=0, upperbound=15)

d_extrusion = sim.External(stats.laplace, loc=40.0, scale=16.08991553254438)
db_extrusion = sim.Bounded(d_extrusion, lowerbound=5, upperbound=250)

d_pulizia = sim.Normal(180, 20)
db_pulizia = sim.Bounded(d_extrusion, lowerbound=60, upperbound=240)
#  --------------------


class DosaggioGenerator(sim.Component):
    def process(self):
        while True:
            stato.df_coni = module_class_cono.update_df_coni(obj_coni)
            if 'D' in stato.df_coni['stato'].values:
                if random() < 0.45:
                    s = stazione1
                else:
                    s = stazione2
                Dosaggio(staz_call=s)
                yield self.hold(db_interarrival.sample() * 0.8)
            else:
                yield self.hold(1)


class Dosaggio(sim.Component):
    def parameters(self, best_dosaggio):
        self.ID = best_dosaggio.loc['ID']
        self.statino = best_dosaggio.loc['statino']
        self.estrusore = best_dosaggio.loc['estrusore']
        self.kg = best_dosaggio.loc['kg_cono']
        self.color = best_dosaggio.loc['color']
        self.valcrom = best_dosaggio.loc['valcrom']
        self.cono = None

        self.richiesta_cono = 0
        self.inizio_dosatura = 0
        self.fine_dosatura = 0
        self.inizio_miscelazione = 0
        self.fine_miscelazione = 0
        self.ingresso_handlingest = 0
        self.fine_handlingest = 0
        self.ingresso_buffer = 0
        self.inizio_estrusione = 0
        self.fine_estrusione = 0

    def end_process(self):
        global stato
        self.cono.cicli += 1
        self.cono.posizione = 'MAG'
        self.cono.stato = 'D'

        stato.dict_throughput = module_stats.kg_cum(stato.dict_throughput,
                                                    env.now(),
                                                    self.kg,
                                                    self.estrusore)
        stato.dict_timestamp_dosaggi = module_stats.aggiorna_timestamp_dosaggi(
            self, stato.dict_timestamp_dosaggi)
        stato.elements -= 1
        stato.dict_elements['time'].append(env.now()/60)
        stato.dict_elements['elements'].append(stato.elements)
        return()

    def setup(self, staz_call):
        global stato, error, df_coda_fail, df_coda_LC_fail, best_dosaggio_fail
        t = env.now()

        self.staz_call = staz_call

        df_coda = module_que_by_est.func_calc_que(
            stato.estrusori,
            stato.dict_TER, t,
            stato.df_OP)

        cono_found = False
        idx_que = 0

        while not cono_found:
            best_dosaggio = df_coda.iloc[idx_que, :]

            self.parameters(best_dosaggio)
            print('Setting up ', env.now(), self.estrusore)

            for cono in obj_coni:
                if cono.estrusore == self.estrusore and cono.stato == 'D':
                    cono_found = True
                    self.cono = cono
                    cono.stato = 'A'
                    cono.estrusore = self.estrusore
                    cono.color = self.color
                    cono.valcrom = self.valcrom
                    break

            if not cono_found:
                for cono in obj_coni:
                    if (cono.valcrom <= self.valcrom
                        and cono.color <= self.color
                            and cono.stato == 'D'):
                        cono_found = True
                        self.cono = cono
                        cono.stato = 'A'
                        cono.estrusore = self.estrusore
                        cono.color = self.color
                        cono.valcrom = self.valcrom
                        break

            if not cono_found:
                idx_que += 1
                print('Cono non trovato, skip to', idx_que)

    def process(self):
        global stato
        self.richiesta_cono = env.now()
        yield self.request(handlingpes)
        self.cono.posizione = 'GUA_PRE'
        stato.elements += 1
        stato.dict_elements['time'].append(env.now()/60)
        stato.dict_elements['elements'].append(stato.elements)
        yield self.hold(db_handlingpes.sample())
        self.release()
        self.enter(self.staz_call.que)
        if self.staz_call.ispassive():
            self.staz_call.activate()
        self.cono.posizione = 'DOS'
        stato.df_OP.loc[[self.ID], 'stato'] = 'D'
        yield self.passivate()

        #  -------------------------
        #  ingresso nel miscelatore
        yield self.request(miscelatore)
        self.inizio_miscelazione = env.now()
        self.cono.posizione = 'MISC'
        stato.df_OP.loc[[self.ID], 'stato'] = 'M'
        yield self.hold(db_miscelatore.sample())

        if self.estrusore not in ['E5', 'E9']:
            while handlingest.claimers().length() != 0:
                yield self.hold(1)
        self.release()
        self.fine_miscelazione = env.now()
        print('miscelato ', env.now(),
              self.estrusore, self.cono.rfid)

        #  ---------------------------
        #  ingresso handlingest e arrivo sul buffer se non Leistritz
        if self.estrusore not in ['E5', 'E9']:
            yield self.request(handlingest)
            stato.df_OP.loc[[self.ID], 'stato'] = 'G'
            self.cono.posizione = 'GUA'
            self.ingresso_handlingest = env.now()
            yield self.hold(db_handlingest.sample()*0.8)
            i = stato.estrusori.index(self.estrusore)
            while len(obj_buffer[i]) >= 2:
                yield self.hold(1)
            self.ingresso_buffer = env.now()
            self.enter(obj_buffer[i])
            self.cono.posizione = 'BUFF'
            stato.df_OP.loc[[self.ID], 'stato'] = 'B'
            self.release()
            self.fine_handlingest = env.now()
        else:
            i = stato.estrusori.index(self.estrusore)
            while len(obj_buffer[i]) >= 2:
                yield self.hold(1)
            self.ingresso_buffer = env.now()
            self.enter(obj_buffer[i])
            self.cono.posizione = 'BUFF'
            stato.df_OP.loc[[self.ID], 'stato'] = 'B'

        #  --------------------
        # ingresso nell'estrusore
        if obj_est[i].ispassive():
            obj_est[i].activate()
        yield self.passivate()

        #  --------------------------------
        #  fine processo
        self.end_process()
        stato.df_OP.loc[[self.ID], 'stato'] = 'T'
        yield self.passivate()


class Stazione(sim.Component):
    def setup(self, n, delay=0):
        self.n = n
        self.delay = delay
        if n == 'S1':
            self.que = que_staz_dos_1
        elif n == 'S2':
            self.que = que_staz_dos_2

    def process(self):
        global stato, dict_picking
        yield self.hold(self.delay)
        while True:
            if len(self.que) == 0:
                yield self.passivate()
            self.dosaggio = self.que.pop()
            self.dosaggio.inizio_dosatura = env.now()
            yield self.hold(db_pesatura.sample()*0.78)
            self.dosaggio.fine_dosatura = env.now()
            print('Dosato ', env.now(), str(
                self.dosaggio.estrusore), self.dosaggio.cono.rfid)

            stato.dict_throughput = module_stats.kg_cum(stato.dict_throughput,
                                                        env.now(),
                                                        self.dosaggio.kg,
                                                        'staz.dosaggio')
            # attiva solo se la coda del miscelatore è vuota
            while miscelatore.claimers().length() >= 2:
                yield self.hold(1)
            self.dosaggio.activate()


class Estrusore(sim.Component):
    def setup(self, n):
        self.n = n

    def process(self):
        global stato
        for est in stato.estrusori:
            if self.n == est:
                i = stato.estrusori.index(est)
                while True:
                    while len(obj_buffer[i]) == 0:
                        yield self.passivate()
                    self.dosaggio = obj_buffer[i].pop()
                    stato.df_OP.loc[[self.dosaggio.ID], 'stato'] = 'E'
                    self.dosaggio.inizio_estrusione = env.now()
                    self.dosaggio.cono.posizione = est
                    extrusion_time = db_extrusion.sample()
                    stato.dict_TER[self.n] = extrusion_time + env.now()
                    yield self.hold(extrusion_time*0.75)
                    if random() < 0.04: # probabilità di guasto
                        yield self.hold(randint(200, 350)) # tempo di manutenzione
                    self.dosaggio.fine_estrusione = env.now()
                    print('estruso ', env.now(), str(
                        self.n), self.dosaggio.cono.rfid)
                    stato.check[self.n].append(self.dosaggio.estrusore)
                    self.dosaggio.activate()
                break


class PuliziaGenerator(sim.Component):
    def setup(self):
        self.pul_running = False

    def process(self):
        while True:
            if not self.pul_running:
                Pulizia()
            yield self.hold(1)


class Pulizia(sim.Component):
    def setup(self):
        self.cono = None
        self.cono_cicli = None
        self.richiesta_cono = None
        self.inzio_pulizia = None
        self.fine_pulizia = None
        self.scarico_cono = None

    def process(self):
        global stato, pulizia_generator
        tmp_coni = sorted(obj_coni, key=lambda x: x.cicli, reverse=True)
        for cono in tmp_coni:
            if (cono.cicli >= stato.max_cicli
                    and cono.stato == 'D'):
                pulizia_generator.pul_running = True
                self.cono = cono.rfid
                yield self.request(stazione_pulizia)
                self.richiesta_cono = env.now()
                self.cono_cicli = cono.cicli
                cono.stato = 'P'

                cono.posizione = 'PUL'
                self.inizio_pulizia = env.now()
                yield self.hold(db_pulizia.sample())
                self.fine_pulizia = env.now()
                cono.color = 0
                cono.valcrom = 0
                cono.cicli = 0
                cono.estrusore = None

                self.scarico_cono = env.now()
                pulizia_generator.pul_running = False
                print('Pulito cono', cono.rfid, env.now())
                cono.stato = 'D'
                cono.posizione = 'MAG'
                cono.coda_pul = False
                stato.dict_timestamp_pulizie =\
                    module_stats.aggiorna_timestamp_pulizie(
                        self, stato.dict_timestamp_pulizie)
                break
        self.passivate()


# MAIN
# --------------------------------------------------
h_sim = 150  # totale di ore che si vogliono simulare

env = sim.Environment()

DosaggioGenerator()

handlingpes = sim.Resource('Gualchierani_pre_pes')

stazione1 = Stazione(n='S1')
stazione2 = Stazione(n='S2', delay=5)

miscelatore = sim.Resource('Miscelatore', capacity=2)

handlingest = sim.Resource('Gualchierani_pre_est')

E1 = Estrusore(n='E1')
E2 = Estrusore(n='E2')
E3 = Estrusore(n='E3')
E4 = Estrusore(n='E4')
E5 = Estrusore(n='E5')
E6 = Estrusore(n='E6')
E7 = Estrusore(n='E7')
E8 = Estrusore(n='E8')
E9 = Estrusore(n='E9')
obj_est = [E1, E2, E3, E4, E5, E6, E7, E8, E9]

pulizia_generator = PuliziaGenerator()

stazione_pulizia = sim.Resource('Stazione di pulizia coni')

env.run(till=(60 * h_sim))
# -------------------------------------------

# verifica correttezza estrusori
for key in stato.check:
    stato.check[key] = set(stato.check[key])

# aggiornamento df coni
stato.df_coni = module_class_cono.update_df_coni(obj_coni)

# creazione Dataframe con tutti i timestamp dosaggi
df_timestamp_dosaggi = pd.DataFrame.from_dict(
    stato.dict_timestamp_dosaggi).sort_values(['estrusore', 'inizio_dosatura'])

# creazione Dataframe con tutti i timestamp pulizie
df_timestamp_pulizie = pd.DataFrame.from_dict(
    stato.dict_timestamp_pulizie).sort_values('richiesta_cono')

module_stats.plot_throughput(stato.dict_throughput)

print('TEMPO DI RUN ', datetime.now() - start)

module_stats.plot_quetot(stato.dict_elements)

df_timestamp_dosaggi.to_csv(r'C:/Users/HP/Desktop/df_tc_sim.csv')


sat1 = E1.status.print_histogram(values=True, as_str=True)
sat2 = E2.status.print_histogram(values=True, as_str=True)
sat3 = E3.status.print_histogram(values=True, as_str=True)
sat4 = E4.status.print_histogram(values=True, as_str=True)
sat5 = E5.status.print_histogram(values=True, as_str=True)
sat6 = E6.status.print_histogram(values=True, as_str=True)
sat7 = E7.status.print_histogram(values=True, as_str=True)
sat8 = E8.status.print_histogram(values=True, as_str=True)
sat9 = E9.status.print_histogram(values=True, as_str=True)
staz1 = stazione1.status.print_histogram(values=True, as_str=True)
staz2 = stazione2.status.print_histogram(values=True, as_str=True)
sat_misc = miscelatore.occupancy.mean()

tot_buff = 0
for b in obj_buffer:
    tot_buff += len(b)

tot_ques = len(handlingest.claimers()
               + miscelatore.claimers()
               + handlingest.requesters()
               + miscelatore.requesters())

a_coni_h = (len(df_timestamp_dosaggi) + tot_buff + tot_ques) / h_sim

mask = stato.df_OP['stato'] == 'T'
dft = stato.df_OP[mask]
codici = []

for col in ['cod.i' + str(n) for n in range(1, 16)]:
    codici.extend(dft[col].tolist())

for c in codici:
    if c == '' or c[0] == '5':
        codici.remove(c)
    