import module_class_cono
import module_stats
import Solver_sequencing
import module_que_by_est

import math
import pandas as pd
import salabim as sim
from scipy import stats
from random import random

from module_class_cono import obj_coni
from class_stato import stato
from sim_queue import (obj_buffer, que_staz_dos,
                       que_staz_dos_1, que_staz_dos_2)

from datetime import datetime
start = datetime.now()


#  capienza di cassoni stazione e buffer
upperbound_s = 4
upperbound_b = 10
#  ----------------

# set distributions for service times
d_interarrival = sim.External(stats.burr, c=3.145066166877723,
                              d=0.4544712096918647,
                              loc=0.4728219512560952,
                              scale=14.372708948169587)
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

d_mir500_coni_pul = sim.Normal(
    mean=8, standard_deviation=0.8)  # go and back CT
db_mir500_coni_pul = sim.Bounded(d_mir500_coni_pul,
                                 lowerbound=5, upperbound=15)

d_mir500_coni_staz = sim.Normal(
    mean=5, standard_deviation=0.5)  # go and back CT
db_mir500_coni_staz = sim.Bounded(d_mir500_coni_staz,
                                  lowerbound=5, upperbound=15)

d_mir500_mp_mag = sim.Normal(mean=3, standard_deviation=0.3)  # only go
db_mir500_mp_mag = sim.Bounded(d_mir500_mp_mag, lowerbound=0.5, upperbound=6)

d_mir500_mp_buff = sim.Normal(mean=1, standard_deviation=0.1)  # only go
db_mir500_mp_buff = sim.Bounded(d_mir500_mp_buff, lowerbound=0.5, upperbound=2)
#  --------------------


class DosaggioGenerator(sim.Component):
    def process(self):
        yield self.hold(0.5)
        while True:
            stato.df_coni = module_class_cono.update_df_coni(obj_coni)
            if 'D' in stato.df_coni['stato'].values:
                if random() <= 0.5:
                    s = stazione1
                else:
                    s = stazione2
                Dosaggio(staz_call=s)
                yield self.hold(db_interarrival.sample())
            else:
                yield self.hold(1)


class DosaggioGeneratorAuto(sim.Component):
    def setup(self):
        self.pull = False

    def process(self):
        yield self.hold(1)
        Dosaggio(staz_call=staz_auto)
        yield self.hold(1)
        Dosaggio(staz_call=staz_auto)
        yield self.hold(5)
        while True:
            stato.df_coni = module_class_cono.update_df_coni(obj_coni)
            if self.pull and 'D' in stato.df_coni['stato'].values:
                Dosaggio(staz_call=staz_auto)
                self.pull = False
            else:
                yield self.hold(0.1)


class Dosaggio(sim.Component):
    def parameters(self, best_dosaggio):
        self.ID = best_dosaggio.loc['ID']
        self.statino = best_dosaggio.loc['statino']
        self.estrusore = best_dosaggio.loc['estrusore']
        self.kg = best_dosaggio.loc['kg_cono']
        self.TD = best_dosaggio.loc['TD']
        self.TE = best_dosaggio.loc['TE']
        self.color = best_dosaggio.loc['color']
        self.valcrom = best_dosaggio.loc['valcrom']
        self.materie_prime = []
        self.peso_mp = []
        self.cono = None

        for i in [('cod.i' + str(n)) for n in range(1, 16)]:
            x = best_dosaggio.loc[i]
            if x != '':
                self.materie_prime.append(x)
            else:
                break

        for i in [('kg.i' + str(n)) for n in range(1, 16)]:
            x = best_dosaggio.loc[i]
            if x != '':
                self.peso_mp.append(x)
            else:
                break

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

    #  Operations research version of setup
    '''def setup(self, staz_call):
        global stato, obj_coni
        t = env.now()

        self.staz_call = staz_call

        dos_con = Solver_sequencing.best_choice(t, stato)
        id_dos = dos_con[0]
        container = dos_con[1]

        best_dosaggio = stato.df_OP.loc[id_dos, :]
        self.parameters(best_dosaggio)
        stato.df_OP.loc[[self.ID], 'stato'] = 'C'
        print('Setting up {} '.format(self.staz_call.n),
              env.now(), self.estrusore, self.ID)

        for c in obj_coni:
            if c.rfid == container:
                self.cono = c
        self.cono.stato = 'A'
        self.cono.estrusore = self.estrusore
        self.cono.color = self.color
        self.cono.valcrom = self.valcrom'''

    #  Heuristc version of setup dosaggio
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

        if self.staz_call.n in ['S1', 'S2']:
            yield self.request(handlingpes)
            self.cono.posizione = 'GUA_PES'
            stato.elements += 1
            stato.dict_elements['time'].append(env.now()/60)
            stato.dict_elements['elements'].append(stato.elements)
            yield self.hold(db_handlingpes.sample())
            self.release()

        elif self.staz_call.n == 'SA':
            stato.elements += 1
            Mission500_coni(cono=self.cono, mission='staz_auto dosaggio',
                            dosaggio=self)
            yield self.passivate()

        self.enter(self.staz_call.que)
        self.cono.posizione = 'Que ' + self.staz_call.n
        stato.df_OP.loc[[self.ID], 'stato'] = 'D'
        if self.staz_call.ispassive():
            self.staz_call.activate()
        yield self.passivate()
        #  ------------------

        #  ingresso nel miscelatore
        self.cono.posizione = 'MISC_request'
        yield self.request(miscelatore)
        self.inizio_miscelazione = env.now()
        self.cono.posizione = 'MISC'
        stato.df_OP.loc[[self.ID], 'stato'] = 'M'
        yield self.hold(db_miscelatore.sample())
        self.fine_miscelazione = env.now()

        if self.estrusore not in ['E5', 'E9']:
            while handlingest.claimers().length() != 0:
                yield self.hold(0.1)
        self.release()
        print('miscelato ', env.now(),
              self.estrusore, self.cono.rfid)
        #  --------------------

        #  ingresso handlingest e arrivo sul buffer se non Leistritz
        if self.estrusore not in ['E5', 'E9']:
            self.cono.posizione = 'GUA_EST_request'
            yield self.request(handlingest)
            stato.df_OP.loc[[self.ID], 'stato'] = 'G'
            self.cono.posizione = 'GUA_EST'
            self.ingresso_handlingest = env.now()
            yield self.hold(db_handlingest.sample())
            i = stato.estrusori.index(self.estrusore)
            while len(obj_buffer[i]) >= 2:
                yield self.hold(1)
            self.ingresso_buffer = env.now()
            self.enter(obj_buffer[i])
            self.cono.posizione = 'BUFF ' + self.estrusore
            stato.df_OP.loc[[self.ID], 'stato'] = 'B'
            self.release()
            self.fine_handlingest = env.now()
        else:
            self.cono.posizione = 'attesa sul mir'
            i = stato.estrusori.index(self.estrusore)
            #  qui deve chiamare il mir500 che prende il cono pieno
            #  lo carica e lo porta fino all'estrusore
            #  se il buffer è pieno la sosta viene fatta fare a bordo del mir
            #  in futuro valutare dove è meglio far fare la sosta
            #  in funzione dell'ottimizzazione di TC
            while len(obj_buffer[i]) >= 2:
                yield self.hold(0.1)
            self.ingresso_buffer = env.now()
            self.enter(obj_buffer[i])
            self.cono.posizione = 'BUFF' + self.estrusore
            stato.df_OP.loc[[self.ID], 'stato'] = 'B'
        #  -------------------

        # ingresso nell'estrusore
        if obj_est[i].ispassive():
            obj_est[i].activate()
        yield self.passivate()
        #  --------------------

        #  fine processo dosaggio
        self.end_process()
        stato.df_OP.loc[[self.ID], 'stato'] = 'T'
        yield self.passivate()
        #  --------------------


class Stazione(sim.Component):
    def setup(self, n):
        self.n = n
        if n == 'S1':
            self.que = que_staz_dos_1
        elif n == 'S2':
            self.que = que_staz_dos_2

    def process(self):
        global stato, dict_picking
        while True:
            if len(self.que) == 0:
                yield self.passivate()
            self.dosaggio = self.que.pop()
            self.dosaggio.cono.posizione = 'DOS ' + self.n
            self.dosaggio.inizio_dosatura = env.now()
            yield self.hold(db_pesatura.sample())
            self.dosaggio.fine_dosatura = env.now()
            print('Dosato {} '.format(self.n), env.now(), str(
                self.dosaggio.estrusore), self.dosaggio.cono.rfid)

            stato.dict_throughput = module_stats.kg_cum(stato.dict_throughput,
                                                        env.now(),
                                                        self.dosaggio.kg,
                                                        'staz.dosaggio')
            # attiva solo se la coda del miscelatore è vuota
            while miscelatore.claimers().length() >= 2:
                yield self.hold(0.1)
            self.dosaggio.activate()


class Staz_auto(sim.Component):
    def setup(self, n, delay=0):
        self.n = n
        self.que = que_staz_dos
        self.retry_call = False

    def picking_list(self):
        global stato
        dict_picking = {}
        idx = 0
        for mp in self.dosaggio.materie_prime:
            #  l'if c'è per prevenire il fatto
            #  che potrebbero esserci codici nuovi
            if mp in stato.df_giacenza.index:
                if dict_picking.get(mp) is None:
                    dict_picking[mp] = []
                    dict_picking[mp].append(self.dosaggio.peso_mp[idx])
                    dict_picking[mp].append(
                        stato.df_giacenza.loc[mp, 'posizione'])
                    if stato.df_giacenza.loc[mp, 'posizione'] == 'S':
                        dict_picking[mp].append('D')
                    else:
                        dict_picking[mp].append('O')
                    idx += 1
                else:
                    dict_picking[mp][0] += self.dosaggio.peso_mp[idx]
                    idx += 1
        return(dict_picking)

    def start_mission(self):
        global dict_picking, n_mission500_mp
        for mp in dict_picking:
            if dict_picking[mp][1] != 'S' and dict_picking[mp][2] == 'O':
                dict_picking[mp][2] = 'R'  # mette stato "richiesto"
                n_mission500_mp += 1
                Mission500_mp(codice=mp)
                break
        return()

#  qui devo inserire il discorso della pesata random
    def weigh_and_pull(self):
        global stato, dict_picking
        t = 0
        for mp, car in dict_picking.items():
            if car[1] == 'S' and car[2] == 'D':
                self.start_mission()
                if car[0] <= 2.5:
                    t += stato.t_tool/60
                    t += ((math.floor(car[0] / 1) - 1)
                          * stato.t_pig_v/60)
                    t += 2 * (stato.t_pig_f / 60)
                    break
                else:
                    if stato.tool != 2:
                        t += stato.t_tool/60
                        stato.tool = 2
                    t += ((math.floor(car[0] / 2) - 1)
                          * stato.t_mass_v/60)
                    t += 2 * (stato.t_mass_f/60)
                    break
        return(t, mp)

    def process(self):
        global stato, dict_picking
        while True:
            while len(que_staz_dos) == 0:
                yield self.passivate()
            self.dosaggio = que_staz_dos.pop()
            self.dosaggio.cono.posizione = 'DOS ' + self.n
            #  crea la picking list
            dict_picking = self.picking_list()
            self.dosaggio.inizio_dosatura = env.now()
            self.start_mission()

            #  dosa le cose una per volta
            #  chiama la missione per MIR
            wait = True
            while wait:
                tupla = self.weigh_and_pull()
                t_pes = tupla[0]
                mp = tupla[1]
                if t_pes != 0:
                    dict_picking[mp][2] = 'WIP'
                    yield self.hold(t_pes)
                    del dict_picking[mp]
                    if len(dict_picking) == 0:
                        wait = False
                else:
                    yield self.hold(0.1)
            #  --------------------
            self.dosaggio.fine_dosatura = env.now()
            print('Dosato {} '.format(self.n), env.now(), str(
                self.dosaggio.estrusore), self.dosaggio.cono.rfid)
            stato.dict_throughput = module_stats.kg_cum(stato.dict_throughput,
                                                        env.now(),
                                                        self.dosaggio.kg,
                                                        'staz.dosaggio')
            self.dosaggio.activate()
            generator_auto.pull = True


class Mission500_coni(sim.Component):
    def setup(self, cono, mission, dosaggio=None, pulizia=None):
        global n_mission500_coni
        self.veicolo = 'MIR500 Coni'
        self.n_mission = n_mission500_coni
        self.mission = mission
        self.cono = cono
        self.dosaggio = dosaggio
        self.pulizia = pulizia

        self.richiesta = env.now()
        self.partenza = 0
        self.scarico = 0

    def process(self):
        global n_mission500_coni
        yield self.request(mir500_coni)
        n_mission500_coni += 1
        self.partenza = env.now()
        if self.mission == 'stazione pulizia':
            self.cono.posizione = 'HANDLING'
            #  yield self.hold(db_mir500_coni_pul.sample())
            yield self.hold(0)
            self.scarico = env.now()
            self.release()
            self.pulizia.activate()
        if self.mission == 'staz_auto dosaggio':
            self.cono.posizione = 'HANDLING'
            #  yield self.hold(db_mir500_coni_staz.sample())
            yield self.hold(0)
            self.scarico = env.now()
            self.release()
            self.dosaggio.activate()
        stato.dict_timestamp_mir500 =\
            module_stats.aggiorna_timestamp_mir500(self,
                                                   stato.dict_timestamp_mir500)
        yield self.passivate()


class Mission500_mp(sim.Component):
    def setup(self, codice):
        global dict_picking, n_mission500_mp
        self.veicolo = 'MIR500 MP'
        self.n_mission = n_mission500_mp
        self.cod_pick = codice
        self.peso = dict_picking[codice][0]
        self.dest = dict_picking[codice][1]

        self.richiesta = env.now()
        self.partenza = 0
        self.scarico = 0

    def process(self):
        global stato, dict_picking, n_mission500_mp

        #  seize resource
        yield self.request(mir500_mp)
        #  individua i codici che si possono togliere dalla staz_auto
        mask_station = ((stato.df_giacenza['posizione'] == 'S'))
        cod_staz = list(stato.df_giacenza[mask_station].index)
        #  ------------

        #  seleziona il codice da portare via dalla staz_auto
        remove_cod = None

        n_cod_staz = len(stato.df_giacenza[mask_station])

        if n_cod_staz >= upperbound_s:
            go = False
            while not go:
                for c in cod_staz:
                    if c not in dict_picking.keys():
                        remove_cod = c
                        go = True
                        stato.df_giacenza.loc[remove_cod,
                                              'posizione'] = 'Handling'
                        break
                    else:
                        yield self.hold(0.1)

        #  inizia con la missione
        dict_picking[self.cod_pick][1] = 'H'
        self.partenza = env.now()

        #  individua se il buffer non è pieno
        mask_buff = ((stato.df_giacenza['posizione'] == 'B'))
        n_cod_buff = len(stato.df_giacenza[mask_buff])

        if n_cod_staz < upperbound_s:
            yield self.hold(db_mir500_mp_mag.sample())

        elif self.dest == 'M' and n_cod_buff < upperbound_b:
            #  yield self.hold(db_mir500_mp_mag.sample())
            yield self.hold(0)
            if remove_cod is not None:
                stato.df_giacenza.loc[remove_cod, 'posizione'] = 'B'
            # yield self.hold(db_mir500_mp_buff.sample())
            yield self.hold(0)

        elif self.dest == 'B':
            #  yield self.hold(db_mir500_mp_buff.sample())
            yield self.hold(0)
            if remove_cod is not None:
                stato.df_giacenza.loc[remove_cod, 'posizione'] = 'B'
            #  yield self.hold(db_mir500_mp_buff.sample())
            yield self.hold(0)

        elif self.dest == 'M' and n_cod_buff >= upperbound_b:
            #  yield self.hold(db_mir500_mp_mag.sample())
            yield self.hold(0)
            if remove_cod is not None:
                stato.df_giacenza.loc[remove_cod, 'posizione'] = 'M'
            #  yield self.hold(db_mir500_mp_mag.sample())
            yield self.hold(0)

        dict_picking[self.cod_pick][1] = 'S'
        dict_picking[self.cod_pick][2] = 'D'
        stato.df_giacenza.loc[self.cod_pick, 'posizione'] = 'S'
        self.release()
        self.scarico = env.now()
        stato.dict_timestamp_picking = module_stats.aggiorna_timestamp_picking(
            self, stato.dict_timestamp_picking)
        yield self.passivate()


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
                    yield self.hold(extrusion_time)
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
                Mission500_coni(cono=cono, pulizia=self,
                                mission='stazione pulizia')
                yield self.passivate()
                cono.posizione = 'PUL'
                self.inizio_pulizia = env.now()
                #  yield self.hold(db_pulizia.sample())
                yield self.hold(0)
                self.fine_pulizia = env.now()
                cono.color = 0
                cono.valcrom = 0
                cono.cicli = 0
                cono.estrusore = None
                Mission500_coni(cono=cono, pulizia=self,
                                mission='stazione pulizia')
                pulizia_generator.pul_running = False
                yield self.passivate()
                self.scarico_cono = env.now()
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
h_sim = 24  # totale di ore che si vogliono simulare
n_mission500_mp = 0
n_mission500_coni = 0

env = sim.Environment()


#  DosaggioGenerator()
generator_auto = DosaggioGeneratorAuto()

mir500_mp = sim.Resource('MIR500 MP', capacity=100)
mir500_coni = sim.Resource('MIR500 Coni', capacity=100)

handlingpes = sim.Resource('Gualchierani_pre_pes')

staz_auto = Staz_auto(n='SA')
stazione1 = Stazione(n='S1')
stazione2 = Stazione(n='S2')

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

# creazione Dataframe con tutti i timestamp picking
df_timestamp_picking = pd.DataFrame.from_dict(
    stato.dict_timestamp_picking).sort_values('richiesta')

# creazione Dataframe con tutti i timestamp pulizie
df_timestamp_pulizie = pd.DataFrame.from_dict(
    stato.dict_timestamp_pulizie).sort_values('richiesta_cono')

# creazione Dataframe con tutti i timestamp picking
df_timestamp_mir500 = pd.DataFrame.from_dict(
    stato.dict_timestamp_mir500).sort_values('n_mission')

module_stats.plot_throughput(stato.dict_throughput)

print('TEMPO DI RUN ', datetime.now() - start)

module_stats.plot_quetot(stato.dict_elements)

tot_buff = 0
for b in obj_buffer:
    tot_buff += len(b)

tot_ques = len(handlingest.claimers()
               + miscelatore.claimers()
               + handlingest.requesters()
               + miscelatore.requesters())

a_coni_h = (len(df_timestamp_dosaggi) + tot_buff + tot_ques) / h_sim

# STATISTICHE SULLA SATURAZIONE DEI SERVER
sat_hand_1 = handlingpes.occupancy.mean()
sat_misc = miscelatore.occupancy.mean()
sat_hand_2 = handlingest.occupancy.mean()
sat_staz_1 = stazione1.status.print_histogram(values=True, as_str=True)
sat_staz_2 = stazione2.status.print_histogram(values=True, as_str=True)
sat_staz_aut = staz_auto.status.print_histogram(values=True, as_str=True)

sat1 = E1.status.print_histogram(values=True, as_str=True)
sat2 = E2.status.print_histogram(values=True, as_str=True)
sat3 = E3.status.print_histogram(values=True, as_str=True)
sat4 = E4.status.print_histogram(values=True, as_str=True)
sat5 = E5.status.print_histogram(values=True, as_str=True)
sat6 = E6.status.print_histogram(values=True, as_str=True)
sat7 = E7.status.print_histogram(values=True, as_str=True)
sat8 = E8.status.print_histogram(values=True, as_str=True)
sat9 = E9.status.print_histogram(values=True, as_str=True)

#  que_staz_dos.print_statistics()
#  que_staz_dos.print_statistics()
