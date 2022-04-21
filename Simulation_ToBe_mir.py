import module_class_cono
import module_stats
import module_que_by_est

import math
import pandas as pd
import salabim as sim
from scipy import stats

from module_class_cono import obj_coni
from class_stato import stato
from sim_queue import (obj_buffer, que_staz_dos)

from datetime import datetime

#  intertempi tra due sezioni del magazzino
t_carico = 0.5
t_scarico = 0.3
t_manovra = 1
t_depall = 1
#  ------------------

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

d_mir100_sl = sim.Normal(
    mean=3, standard_deviation=0.4)  # go and back CT
db_mir100_sl = sim.Bounded(d_mir500_coni_pul,
                           lowerbound=2, upperbound=8)
#  --------------------


class DosaggioGeneratorAuto(sim.Component):
    def process(self):
        Dosaggio(staz_call=staz_auto)
        yield self.hold(5)
        while True:
            stato.df_coni = module_class_cono.update_df_coni(obj_coni)
            if 'D' in stato.df_coni['stato'].values:
                Dosaggio(staz_call=staz_auto)
                yield self.wait((dos_done, True, 1))
            else:
                yield self.standby()


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
        self.materie_prime = {}
        self.cono = None

        for i in [('cod.i' + str(n), 'kg.i' + str(n)) for n in range(1, 16)]:
            x = best_dosaggio.loc[i[0]]
            if x != '':
                self.materie_prime[x] = best_dosaggio.loc[i[1]]
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

    #  Heuristc version of setup dosaggio
    def setup(self, staz_call):
        global stato
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
            print('Setting up ', env.now(), self.ID)

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

    def start_mission(self, mp):
        global n_mission500_mp, n_mission100_sl
        if mp in stato.df_stock_mp.index:
            n_mission500_mp += 1
            Mission500_mp(mission='picking', dosaggio=self)
        elif mp in stato.df_stock_sl.index:
            n_mission100_sl += 1
            Mission100_sl(dosaggio=self)
        return()

    def process(self):
        global stato
        stato.df_OP.loc[self.ID, 'stato'] = 'C'
        self.richiesta_cono = env.now()

        stato.elements += 1
        Mission500_coni(cono=self.cono, mission='staz_auto dosaggio',
                        dosaggio=self)
        yield self.passivate()

        self.enter(self.staz_call.que)
        self.cono.posizione = 'Que ' + str(self.staz_call.n)
        stato.df_OP.loc[[self.ID], 'stato'] = 'D'

        for x in self.materie_prime:
            self.start_mission(mp=x)

        if self.staz_call.ispassive():
            self.staz_call.activate()
        yield self.passivate()
        dos_done.trigger(max=1)
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
                yield self.standby()
        self.release()
        '''print('miscelato ', env.now(),
              self.estrusore, self.cono.rfid)'''
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
                yield self.standby()
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
                yield self.standby()
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


class Staz_auto(sim.Component):
    def setup(self, n, delay=0):
        self.n = n
        self.que = que_staz_dos
        self.retry_call = False

#  qui devo inserire il discorso della pesata random
    def weigh(self):
        global stato
        t = 0
        condition = False
        for mp in self.dosaggio.materie_prime:
            if mp in stato.df_stock_mp.index:
                condition = (stato.df_stock_mp.loc[mp, 'zona'] == 'S'
                             and stato.df_stock_mp.loc[mp, 'stato'] == 'D')
            else:
                condition = (stato.df_stock_sl.loc[mp, 'zona'] == 'S'
                             and stato.df_stock_sl.loc[mp, 'stato'] == 'D')

            if condition:
                if self.dosaggio.materie_prime[mp] <= 2.5:
                    t += stato.t_tool/60
                    t += ((math.floor(self.dosaggio.materie_prime[mp] / 1) - 1)
                          * stato.t_pig_v/60)
                    t += 2 * (stato.t_pig_f / 60)
                    return(t, mp)
                else:
                    if stato.tool != 2:
                        t += stato.t_tool/60
                        stato.tool = 2
                    t += ((math.floor(self.dosaggio.materie_prime[mp] / 2) - 1)
                          * stato.t_mass_v/60)
                    t += 2 * (stato.t_mass_f/60)
                    return(t, mp)
        return(None)

    def process(self):
        global stato
        while True:
            while len(que_staz_dos) == 0:
                yield self.passivate()
            self.dosaggio = que_staz_dos.pop()

            self.dosaggio.cono.posizione = 'DOS ' + self.n
            self.dosaggio.inizio_dosatura = env.now()

            #  dosa le cose una per volta
            wait = True
            while wait:
                tupla = self.weigh()
                if tupla is not None:
                    t_pes = tupla[0]
                    mp = tupla[1]

                    if mp in stato.df_stock_mp.index:
                        stato.df_stock_mp.loc[mp, 'stato'] = 'WIP'
                    else:
                        stato.df_stock_sl.loc[mp, 'stato'] = 'WIP'

                    #  rimuove dalla giacenza i kg di mp usata
                    if mp in stato.df_stock_mp.index:
                        stato.df_stock_mp.loc[mp,
                                              'qta'] -= self.dosaggio.materie_prime[mp]

                    yield self.hold(t_pes)
                    del self.dosaggio.materie_prime[mp]
                    print('finito', mp)
                    if mp in stato.df_stock_mp.index:
                        stato.df_stock_mp.loc[mp, 'stato'] = 'D'
                    else:
                        stato.df_stock_sl.loc[mp, 'stato'] = 'D'

                    if len(self.dosaggio.materie_prime) == 0:
                        wait = False
                else:
                    yield self.standby()
            #  --------------------
            self.dosaggio.fine_dosatura = env.now()
            print('Dosato {} '.format(self.dosaggio.ID), env.now(),
                  self.dosaggio.cono.rfid)
            stato.dict_throughput = module_stats.kg_cum(stato.dict_throughput,
                                                        env.now(),
                                                        self.dosaggio.kg,
                                                        'staz.dosaggio')
            self.dosaggio.activate()


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
            self.cono.posizione = 'HANDLING PULIZIA'
            yield self.hold(db_mir500_coni_pul.sample())
            #  yield self.hold(0)
            self.scarico = env.now()
            self.release()
            self.pulizia.activate()
        elif self.mission == 'staz_auto dosaggio':
            self.cono.posizione = 'HANDLING DOSAGGIO'
            #  yield self.hold(db_mir500_coni_staz.sample())
            yield self.hold(0)
            self.scarico = env.now()
            self.release()
            self.dosaggio.activate()
        stato.dict_timestamp_mir500 = module_stats.aggiorna_timestamp_mir500(self,
                                                                             stato.dict_timestamp_mir500)
        yield self.passivate()


class Mission500_mp(sim.Component):
    def setup(self, mission, codice=None, dosaggio=None):
        global stato, n_mission500_mp
        self.veicolo = 'MIR500 MP'
        self.n_mission = n_mission500_mp
        self.cod_pick = codice
        self.mission = mission
        if self.mission == 'picking':
            self.dosaggio = dosaggio
            self.richiesta = env.now()
            self.partenza = 0
            self.scarico = 0

    def process(self):
        global stato, n_mission500_mp

        #  seize resource
        yield self.request(mir500_mp)

        if self.mission == 'picking':

            #  seleziona il codice da prelevare
            for c in self.dosaggio.materie_prime:
                if c in stato.df_stock_mp.index:
                    if (stato.df_stock_mp.loc[c, 'stato'] is None
                            and stato.df_stock_mp.loc[c, 'zona'] == 'M'):
                        self.cod_pick = c
                        stato.df_stock_mp.loc[c, 'stato'] = 'R'
                        break
            if self.cod_pick == None:
                self.release()
                yield self.passivate()
            #  --------------

            #  seleziona il codice da portare via dalla staz_auto
            remove_cod = None
            go = False
            while not go:
                #  individua i codici presenti nella staz_auto
                mask_station = (stato.df_stock_mp['zona'] == 'S')
                cod_staz = list(stato.df_stock_mp[mask_station].index)
                if len(cod_staz) != 0:
                    for c in cod_staz:
                        if (c not in self.dosaggio.materie_prime
                                and stato.df_stock_mp.loc[c, 'zona'] == 'S'
                                and c not in staz_auto.dosaggio.materie_prime.keys()):
                            remove_cod = c
                            go = True
                            stato.df_stock_mp.loc[remove_cod, 'zona'] = 'H'
                            stato.df_stock_mp.loc[remove_cod, 'stato'] = 'H'
                            break
                    if not go:
                        yield self.standby()
                else:
                    yield self.standby()
            #  ------------

            #  inizia con la missione
            self.partenza = env.now()
            print(self.n_mission, self.dosaggio.ID, self.cod_pick, remove_cod)
            print(self.dosaggio.materie_prime.keys())
            print('alla stazione manca', staz_auto.dosaggio.materie_prime.keys())
            if stato.df_stock_mp.loc[remove_cod, 'qta'] >= 90:
                t = (stato.df_stock_mp.loc[remove_cod, 'sezione'] * t_carico
                     + t_manovra
                     + stato.df_stock_mp.loc[remove_cod, 'sezione']
                     * t_scarico)
                dt = sim.Normal(mean=t, standard_deviation=t/10)  # only go
                dtb = sim.Bounded(dt, lowerbound=t/2, upperbound=2*t)
                yield self.hold(dtb.sample())
                #  yield self.hold(0)
                stato.df_stock_mp.loc[remove_cod, 'zona'] = 'M'
                stato.df_stock_mp.loc[remove_cod, 'stato'] = None
            else:
                stato.df_stock_mp.loc[remove_cod, 'zona'] = 'DEPALL'
                stato.df_stock_mp.loc[remove_cod, 'stato'] = 'DEPALL'
                t = (t_manovra + t_depall)
                dt = sim.Normal(mean=t, standard_deviation=t/10)  # only go
                dtb = sim.Bounded(dt, lowerbound=t/2, upperbound=2*t)
                yield self.hold(dtb.sample())
                #  yield self.hold(0)
                while depallettizzatore.requesters().length() >= 1:
                    yield self.standby()
                Depallettizzazione(mp=remove_cod)

            stato.df_stock_mp.loc[self.cod_pick, 'zona'] = 'H'
            t = (stato.df_stock_mp.loc[self.cod_pick, 'sezione'] * t_scarico
                 + t_manovra
                 + stato.df_stock_mp.loc[self.cod_pick, 'sezione'] * t_scarico)
            dt = sim.Normal(mean=t, standard_deviation=t/10)  # only go
            dtb = sim.Bounded(dt, lowerbound=t/2, upperbound=2*t)
            yield self.hold(dtb.sample())
            #  yield self.hold(0)

            stato.df_stock_mp.loc[self.cod_pick, 'stato'] = 'D'
            stato.df_stock_mp.loc[self.cod_pick, 'zona'] = 'S'
            self.scarico = env.now()
            stato.dict_timestamp_picking = module_stats.aggiorna_timestamp_picking(
                self, stato.dict_timestamp_picking)

        elif self.mission == 'recupero_depall':
            t = (t_depall + t_manovra
                 + stato.df_stock_mp.loc[self.cod_pick, 'sezione'] * t_carico
                 + stato.df_stock_mp.loc[self.cod_pick, 'sezione'] * t_scarico)
            dt = sim.Normal(mean=t, standard_deviation=t/10)  # only go
            dtb = sim.Bounded(dt, lowerbound=t/2, upperbound=2*t)
            #  yield self.hold(dtb.sample())
            yield self.hold(0)
            stato.df_stock_mp.loc[self.cod_pick, 'zona'] = 'M'
            stato.df_stock_mp.loc[self.cod_pick, 'stato'] = None

        self.release()
        yield self.passivate()


class Mission100_sl(sim.Component):
    def setup(self, dosaggio):
        self.veicolo = 'MIR100 SL'
        self.n_mission = n_mission100_sl
        self.cod_pick = None
        self.dosaggio = dosaggio

        self.richiesta = env.now()
        self.partenza = 0
        self.scarico = 0

    def process(self):
        global stato, n_mission100_sl

        #  seize resource
        yield self.request(mir100_sl)

        #  seleziona il codice da prelevare
        for c in self.dosaggio.materie_prime:
            if c in stato.df_stock_sl.index:
                if (stato.df_stock_sl.loc[c, 'zona'] == 'M'
                        and stato.df_stock_sl.loc[c, 'stato'] is None):
                    self.cod_pick = c
                    stato.df_stock_sl.loc[c, 'stato'] = 'R'
                    break
        #  --------------

        #  seleziona il codice da portare via dalla staz_auto
        remove_cod = None
        go = False
        while not go:
            #  individua i codici presenti nella staz_auto
            mask_station = (stato.df_stock_sl['zona'] == 'S')
            cod_staz = list(stato.df_stock_sl[mask_station].index)
            for c in cod_staz:
                if (c not in self.dosaggio.materie_prime
                        and stato.df_stock_sl.loc[c, 'zona'] == 'S'
                        and c not in staz_auto.dosaggio.materie_prime.keys()):
                    remove_cod = c
                    go = True
                    stato.df_stock_sl.loc[remove_cod, 'zona'] = 'H'
                    stato.df_stock_sl.loc[remove_cod, 'stato'] = 'H'
                    break
                else:
                    yield self.standby()
        #  ------------

        #  inizia con la missione
        self.partenza = env.now()
        yield self.hold(db_mir100_sl.sample())
        #  yield self.hold(0)
        stato.df_stock_sl.loc[remove_cod, 'zona'] = 'M'
        stato.df_stock_sl.loc[remove_cod, 'stato'] = None
        yield self.hold(db_mir100_sl.sample())
        #  yield self.hold(0)

        stato.df_stock_sl.loc[self.cod_pick, 'stato'] = 'D'
        stato.df_stock_sl.loc[self.cod_pick, 'zona'] = 'S'
        self.scarico = env.now()
        stato.dict_timestamp_picking = module_stats.aggiorna_timestamp_picking(
            self, stato.dict_timestamp_picking)

        self.release()
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
                    '''print('estruso ', env.now(), str(
                        self.n), self.dosaggio.cono.rfid)'''
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
            #  qui potrei provare a mettere una condizione di
            #  wait until per vedere se miglioro ancora le prestazioni


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
                stato.dict_timestamp_pulizie = module_stats.aggiorna_timestamp_pulizie(
                    self, stato.dict_timestamp_pulizie)
                break
        self.passivate()


class Depallettizzazione(sim.Component):
    def setup(self, mp):
        self.code = mp

    def process(self):
        global stato
        yield self.request(depallettizzatore)
        yield self.hold(0)
        stato.df_stock_mp.loc[self.code, 'qta'] = 500
        Mission500_mp(codice=self.code, mission='recupero_depall')
        self.release()
        self.passivate()


# MAIN
# --------------------------------------------------
h_sim = 100  # totale di ore che si vogliono simulare
n_mission500_mp = 0
n_mission100_sl = 0
n_mission500_coni = 0

start = datetime.now()
print('PARTENZA ', start)

env = sim.Environment()

#  states
dos_done = sim.State('dos_done')
#  ------------

DosaggioGeneratorAuto()

#  massimo numero di mir500 MP è 4
#  perchè avendo 4 cassoni in stazione il 5° mir che partirebbe non troverebbe
#  nessun cassone da rimuovere dalla stazione
#  quindi rimarrebbe per tempo infinito nel ciclo while standby() a riga 562
mir500_mp = sim.Resource('MIR500 MP', capacity=4)
mir100_sl = sim.Resource('MIR100 SL', capacity=1)
mir500_coni = sim.Resource('MIR500 Coni', capacity=1)

staz_auto = Staz_auto(n='SA')

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
depallettizzatore = sim.Resource('Stazione di depallettizzazione')

env.run(till=(60 * h_sim))

print('TEMPO DI RUN ', datetime.now() - start)
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
sat_misc = miscelatore.occupancy.mean()
sat_hand_2 = handlingest.occupancy.mean()
sat_staz_aut = staz_auto.status.print_histogram(values=True, as_str=True)
sat_mir500_mp = mir500_mp.occupancy.mean()
sat_mir100_sl = mir100_sl.occupancy.mean()
sat_mir500_coni = mir500_coni.occupancy.mean()

sat1 = E1.status.print_histogram(values=True, as_str=True)
sat2 = E2.status.print_histogram(values=True, as_str=True)
sat3 = E3.status.print_histogram(values=True, as_str=True)
sat4 = E4.status.print_histogram(values=True, as_str=True)
sat5 = E5.status.print_histogram(values=True, as_str=True)
sat6 = E6.status.print_histogram(values=True, as_str=True)
sat7 = E7.status.print_histogram(values=True, as_str=True)
sat8 = E8.status.print_histogram(values=True, as_str=True)
sat9 = E9.status.print_histogram(values=True, as_str=True)


print(len(mir500_mp.claimers()))
#  que_staz_dos.print_statistics()

#  que_staz_dos.print_statistics()

#  que_staz_dos.print_statistics()
#  que_staz_dos.print_statistics()
#  que_staz_dos.print_statistics()
#  que_staz_dos.print_statistics()
#  que_staz_dos.print_statistics()
#  que_staz_dos.print_statistics()
