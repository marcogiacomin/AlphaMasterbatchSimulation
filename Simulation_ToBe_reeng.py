import module_class_cono
import module_stats_reeng
import module_que_by_est

import pandas as pd
import salabim as sim
from scipy import stats
from random import random, randrange
import math

from module_class_cono import obj_coni
from class_stato import stato
from sim_queue import (obj_buffer, que_staz_dos,
                       que_staz_dos_1, que_staz_dos_2)

from datetime import datetime
start = datetime.now()

#  intertempi tra due sezioni del magazzino
t_carico = 8/60 # da carico viaggia piano
t_scarico = 4/60 # da scarico va più forte, v_max 1 metro al secondo
t_corridoio = 90/60 #  frenata, manovra, percorrenza, accelerazione
t_zero = 60/60 # carico pallet, accelerazione e percorrenza
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
class OrologioSim(sim.Component):
    def process(self):
        while True:
            orologio.trigger(max=1)
            yield self.hold(0.01)


class DosaggioGeneratorAuto(sim.Component):
    def process(self):
        Dosaggio(staz_call=staz_auto)
        yield self.wait((picking_list_refreshed, 1, True))
        while True:
            stato.df_coni = module_class_cono.update_df_coni(obj_coni)
            if ('D' in stato.df_coni['stato'].values
                and len(fleet_manager_forklift.picking_list) < 4):
                Dosaggio(staz_call=staz_auto)
                yield self.wait((picking_list_refreshed, 1, True))
            else:
                yield self.wait((orologio, 1, True))
                
class DosaggioGeneratorAutoNoPicking(sim.Component):
    def process(self):
        Dosaggio(staz_call=staz_auto)
        yield self.hold(4)
        while True:
            stato.df_coni = module_class_cono.update_df_coni(obj_coni)
            if ('D' in stato.df_coni['stato'].values):
                Dosaggio(staz_call=staz_auto)
                yield self.wait((call_dos, 1, True))
            else:
                yield self.wait((orologio, 1, True))
                

class DosaggioGenerator(sim.Component):
    def process(self):
        yield self.hold(8)
        while True:
            stato.df_coni = module_class_cono.update_df_coni(obj_coni)
            if 'D' in stato.df_coni['stato'].values:
                if random() < 0.5:
                    s = stazione1
                else:
                    s = stazione2
                Dosaggio(staz_call=s)
                yield self.hold(db_interarrival.sample())
            else:
                yield self.wait((orologio, 1, True))


class FleetManagerMIR(sim.Component):
    def setup(self):
        self.picking_list = []
        
    def process(self):
        global stato, mir100_list
        while True:
            if len(self.picking_list) != 0:
                code = self.picking_list.pop(0)
                departed = False
                t_richiesta = env.now()
                while not departed:
                    if stato.df_stock_sl.loc[code, 'zona'] == 'M':
                        for mir100 in mir100_list:
                            if mir100.ispassive():
                                mir100.richiesta = t_richiesta
                                mir100.disponibilità = env.now()
                                mask_station = stato.df_stock_sl['zona'] == 'S'
                                cod_staz = list(stato.df_stock_sl[mask_station].index)
                                for remove in cod_staz:
                                    if stato.df_stock_sl.loc[remove, 'stato'] == 5:
                                        mir100.remove_code = remove
                                        mir100.pick_code = code
                                        stato.df_stock_sl.loc[remove, 'zona'] = 'H'
                                        stato.df_stock_sl.loc[code, 'zona'] = 'H'
                                        stato.df_stock_sl.loc[code, 'stato'] = 2
                                        mir100.activate()
                                        departed = True
                                        break
                                break
                        yield self.wait((orologio, 1, True))
                    elif (stato.df_stock_sl.loc[code, 'zona'] == 'S'
                          and stato.df_stock_sl.loc[code, 'stato'] == 5
                          and code in staz_auto.dosaggio.materie_prime.keys()):
                        stato.df_stock_sl.loc[code, 'stato'] = 3
                        stato.df_stock_sl.loc[code, 'zona'] = 'S'
                        departed = True
                    else:
                        yield self.wait((orologio, 1, True))
            else:
                yield self.wait((orologio, 1, True))

class FleetManagerForklift(sim.Component):
    def setup(self):
        self.picking_list = []
    
    def count_overlap(self):
        global stato
        total = 0
        mask_station = stato.df_stock_mp['zona'] == 'S'
        cod_staz = list(stato.df_stock_mp[mask_station].index)
        for c in cod_staz:
            if (stato.df_stock_mp.loc[c, 'stato'] == 3
                and c not in staz_auto.dosaggio.materie_prime.keys()):
                total += 1
        return(total)
        
    def process(self):
        global stato, fl_list
        # a = 0
        # b = 0
        while True:
            if len(self.picking_list) != 0:
                code = self.picking_list.pop(0)
                departed = False
                t_richiesta = env.now()
                while not departed:
                    if stato.df_stock_mp.loc[code, 'zona'] == 'M':
                        for forklift in fl_list:
                            if forklift.ispassive(): # non trova forklift liberi
                                forklift.richiesta = t_richiesta
                                forklift.disponibilità = env.now()
                                mask_station = stato.df_stock_mp['zona'] == 'S'
                                cod_staz = list(stato.df_stock_mp[mask_station].index)
                                for remove in cod_staz: #  non trova codici da rimuovere
                                    if (stato.df_stock_mp.loc[remove, 'stato'] == 5
                                        and remove not in staz_auto.dosaggio.materie_prime.keys()): 
                                        forklift.remove_code = remove
                                        forklift.pick_code = code
                                        stato.df_stock_mp.loc[remove, 'zona'] = 'H'
                                        stato.df_stock_mp.loc[code, 'zona'] = 'H'
                                        stato.df_stock_mp.loc[code, 'stato'] = 2
                                        forklift.activate()
                                        departed = True
                                        break
                                break
                        if not departed:
                            mask_station = stato.df_stock_mp['zona'] == 'S'
                            cod_staz = list(stato.df_stock_mp[mask_station].index)
                            for c in cod_staz:
                                if (stato.df_stock_mp.loc[code, 'zona'] == 'S'
                                      and stato.df_stock_mp.loc[code, 'stato'] == 5
                                      and code in staz_auto.dosaggio.materie_prime.keys()):
                                    stato.df_stock_mp.loc[code, 'stato'] = 3
                            yield self.wait((orologio, 1, True))
                    elif (stato.df_stock_mp.loc[code, 'zona'] == 'S'
                          and stato.df_stock_mp.loc[code, 'stato'] == 5
                          and code in staz_auto.dosaggio.materie_prime.keys()):
                        stato.df_stock_mp.loc[code, 'stato'] = 3
                        departed = True
                    elif (stato.df_stock_mp.loc[code, 'zona'] == 'S'
                          and stato.df_stock_mp.loc[code, 'stato'] == 4
                          and self.count_overlap() <= 3):
                        staz_auto.save_list.append(code)
                        departed = True
                    elif (stato.df_stock_mp.loc[code, 'zona'] == 'S'
                          and stato.df_stock_mp.loc[code, 'stato'] == 3
                          and self.count_overlap() <= 3):
                        staz_auto.save_list.append(code)
                        stato.df_stock_mp.loc[code, 'statonext'] = True
                        departed = True
                    elif (stato.df_stock_mp.loc[code, 'zona'] == 'H'
                          and stato.df_stock_mp.loc[code, 'stato'] == 2
                          and self.count_overlap() <= 3):
                        staz_auto.save_list.append(code)
                        stato.df_stock_mp.loc[code, 'statonext'] = True
                        departed = True
                    else:
                        #print('a', a)
                        #a += 1
                        yield self.wait((orologio, 1, True))
            else:
                #print('b', b)
                #b += 1
                yield self.wait((orologio, 1, True))

#  comandi per il debug in caso andasse in blocco
'''
fleet_manager_forklift.picking_list
staz_auto.save_list
staz_auto.saved
staz_auto.dosaggio.materie_prime
staz_auto.dosaggio.ID
que_staz_dos[0].materie_prime
'''

class Forklift(sim.Component):
    def setup(self, n):
        self.n = n
        self.remove_code = None
        self.pick_code = None
        
        self.n_mission = 0
        self.richiesta = 0
        self.disponibilità = 0
        self.partenza = 0
        self.scarico = 0

    def process(self):
        global stato, t_carico, t_scarico, t_zero, t_manovra, n_mission_forklift
        while True:
            self.richiesta = None
            self.disponibilità = None
            self.partenza = None
            self.scarico = None
            
            while self.pick_code is None:
                yield self.passivate()
            
            n_mission_forklift += 1
            self.n_mission = n_mission_forklift
            self.partenza = env.now()
            #  inizia con la missione
            t = (t_zero
                 + stato.df_stock_mp.loc[self.remove_code, 'sezione'] * t_carico
                 + t_corridoio
                 + stato.df_stock_mp.loc[self.remove_code, 'sezione'] * t_scarico)
            dt = sim.Normal(mean=t, standard_deviation=t/10)  # only go
            dtb = sim.Bounded(dt, lowerbound=t/2, upperbound=2*t)
            #yield self.hold(dtb.sample())
            yield self.hold(0)
            stato.df_stock_mp.loc[self.remove_code, 'zona'] = 'M'
            stato.df_stock_mp.loc[self.remove_code, 'stato'] = None
        
            stato.df_stock_mp.loc[self.pick_code, 'zona'] = 'H'
            
            #  primo approccio alla simulazione di ciclo combinato su uno
            #  o su due corridoi
            if (stato.df_stock_mp.loc[self.pick_code, 'sezione']
                == stato.df_stock_mp.loc[self.remove_code, 'sezione']):
                t = t_corridoio / 3
            else:
                t = stato.df_stock_mp.loc[self.pick_code, 'sezione'] * t_scarico
                t += t_corridoio
            
            t = (stato.df_stock_mp.loc[self.pick_code, 'sezione'] * t_carico
                 + t_zero)
            dt = sim.Normal(mean=t, standard_deviation=t/10)  # only go
            dtb = sim.Bounded(dt, lowerbound=t/2, upperbound=2*t)
            #yield self.hold(dtb.sample())
            yield self.hold(0)
            self.scarico = env.now()

            stato.df_stock_mp.loc[self.pick_code, 'stato'] = 3
            stato.df_stock_mp.loc[self.pick_code, 'zona'] = 'S'
            
            stato.dict_timestamp_picking = module_stats_reeng.aggiorna_timestamp_picking(
                self, stato.dict_timestamp_picking)
            
            self.pick_code = None


class Mir100(sim.Component):
    def setup(self, n):
        self.n = n
        self.remove_code = None
        self.pick_code = None
        
        self.n_mission = 0
        self.richiesta = 0
        self.disponibilità = 0
        self.partenza = 0
        self.scarico = 0
    
    def process(self):
        global stato, n_mission100
        while True:
            while self.pick_code is None:
                yield self.passivate()
                
            #  inizia con la missione
            n_mission100 += 1
            self.n_mission = n_mission100
            self.partenza = env.now()
            stato.df_stock_sl.loc[self.remove_code, 'stato'] = 6
            yield self.hold(db_mir100_sl.sample())
            #yield self.hold(0)
            stato.df_stock_sl.loc[self.remove_code, 'zona'] = 'M'
            stato.df_stock_sl.loc[self.remove_code, 'stato'] = None
            yield self.hold(db_mir100_sl.sample())
            #yield self.hold(0)
            self.scarico = env.now()
    
            stato.df_stock_sl.loc[self.pick_code, 'stato'] = 3
            stato.df_stock_sl.loc[self.pick_code, 'zona'] = 'S'
            
            stato.dict_timestamp_picking = module_stats_reeng.aggiorna_timestamp_picking(
                self, stato.dict_timestamp_picking)
            
            self.pick_code = None


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

        stato.dict_throughput = module_stats_reeng.kg_cum(stato.dict_throughput,
                                                    env.now(),
                                                    self.kg,
                                                    self.estrusore)
        stato.dict_timestamp_dosaggi = module_stats_reeng.aggiorna_timestamp_dosaggi(
            self, stato.dict_timestamp_dosaggi)
        stato.elements -= 1
        stato.dict_elements['time'].append(env.now()/60)
        stato.dict_elements['elements'].append(stato.elements)
        return()

    def setup(self, staz_call):
        global stato, df_coda_fail, df_coda_LC_fail, best_dosaggio_fail
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
            stato.df_OP.loc[[self.ID], 'stato'] = 'C'
            
            Mission500_coni(cono=self.cono, mission='staz_auto dosaggio',
                            dosaggio=self)
            yield self.passivate()

        self.enter(self.staz_call.que)
        self.cono.posizione = 'DOS'
        stato.df_OP.loc[[self.ID], 'stato'] = 'D'
        
        #  in caso di utilizzo mir e forklift
        if self.staz_call.n == 'SA':
            for c in self.materie_prime.keys():
                if c in stato.df_stock_mp.index:
                    fleet_manager_forklift.picking_list.append(c)
                else:
                    fleet_manager_mir.picking_list.append(c)
            picking_list_refreshed.trigger(max=1)
            
        if self.staz_call.ispassive():
            self.staz_call.activate()
        yield self.passivate()
        #  ------------------

        #  ingresso nel miscelatore
        yield self.request(miscelatore)
        self.inizio_miscelazione = env.now()
        self.cono.posizione = 'MISC'
        stato.df_OP.loc[[self.ID], 'stato'] = 'M'
        yield self.hold(db_miscelatore.sample())

        if self.estrusore not in ['E5', 'E9']:
            while handlingest.claimers().length() != 0:
                yield self.wait((orologio, 1, True))
        self.release()
        self.fine_miscelazione = env.now()
        print('miscelato ', env.now(),
              self.estrusore, self.cono.rfid)
        #  --------------------

        #  ingresso handlingest e arrivo sul buffer se non Leistritz
        if self.estrusore not in ['E5', 'E9']:
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
            self.cono.posizione = 'BUFF'
            stato.df_OP.loc[[self.ID], 'stato'] = 'B'
            self.release()
            self.fine_handlingest = env.now()
        else:
            i = stato.estrusori.index(self.estrusore)
            while len(obj_buffer[i]) >= 2:
                yield self.standby()
            self.ingresso_buffer = env.now()
            self.enter(obj_buffer[i])
            self.cono.posizione = 'BUFF'
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
            self.dosaggio.inizio_dosatura = env.now()
            yield self.hold(db_pesatura.sample())
            self.dosaggio.fine_dosatura = env.now()
            print('Dosato ', env.now(), str(
                self.dosaggio.estrusore), self.dosaggio.cono.rfid)

            stato.dict_throughput = module_stats_reeng.kg_cum(stato.dict_throughput,
                                                        env.now(),
                                                        self.dosaggio.kg,
                                                        'staz.dosaggio')
            # attiva solo se la coda del miscelatore è vuota
            while miscelatore.claimers().length() >= 2:
                yield self.wait((orologio, 1, True))
            self.dosaggio.activate()


class Staz_auto(sim.Component):
    def setup(self, n):
        self.n = n
        self.que = que_staz_dos
        self.dosaggio = None
        self.save_list = []
        self.saved = []

    def weigh(self):
        global stato
        t = 0
        condition = False
        
        if len(self.save_list) != 0:
            for mp in self.save_list:
                if mp in self.dosaggio.materie_prime:
                    if (mp in stato.df_stock_mp.index
                        and not stato.df_stock_mp.loc[mp, 'statonext']):
                        condition = (stato.df_stock_mp.loc[mp, 'zona'] == 'S'
                                     and stato.df_stock_mp.loc[mp, 'stato'] == 3)
                    elif mp in stato.df_stock_sl.index:
                        condition = (stato.df_stock_sl.loc[mp, 'zona'] == 'S'
                                     and stato.df_stock_sl.loc[mp, 'stato'] == 3)
                    if condition:
                        self.save_list.remove(mp)
                        if self.dosaggio.materie_prime[mp] <= stato.kg_mass:
                            t += stato.t_tool/60
                            t += ((math.floor(self.dosaggio.materie_prime[mp]
                                              / (stato.kg_pig * (randrange(80, 100) / 100)) - 1)
                                  * stato.t_pig_v / 60))
                            t += 2 * (stato.t_pig_f / 60)
                            return(t, mp)
                        else:
                            t += stato.t_tool/60
                            t += ((math.floor(self.dosaggio.materie_prime[mp]
                                              / (stato.kg_mass * (randrange(80, 100) / 100)) - 1)
                                  * stato.t_mass_v / 60))
                            t += 2 * (stato.t_mass_f / 60)
                            return(t, mp)
        
        for mp in self.dosaggio.materie_prime:
            if mp in stato.df_stock_mp.index:
                condition = (stato.df_stock_mp.loc[mp, 'zona'] == 'S'
                             and stato.df_stock_mp.loc[mp, 'stato'] == 3)
            elif mp in stato.df_stock_sl.index:
                condition = (stato.df_stock_sl.loc[mp, 'zona'] == 'S'
                             and stato.df_stock_sl.loc[mp, 'stato'] == 3)

            if condition:
                if self.dosaggio.materie_prime[mp] <= 2.5:
                    t += stato.t_tool/60
                    t += ((math.floor(self.dosaggio.materie_prime[mp]
                                      / (1 * (randrange(80, 100) / 100)) - 1)
                          * stato.t_pig_v/60))
                    t += 2 * (stato.t_pig_f / 60)
                    return(t, mp)
                else:
                    t += stato.t_tool/60
                    t += ((math.floor(self.dosaggio.materie_prime[mp]
                                      / (3 * (randrange(80, 100) / 100)) - 1)
                          * stato.t_mass_v/60))
                    t += 2 * (stato.t_mass_f/60)
                    return(t, mp)
        return(None)

    def process(self):
        global stato
        while True:
            while len(que_staz_dos) == 0:
                yield self.passivate()
            self.dosaggio = que_staz_dos.pop()
            
            #  in caso di NON utilizzo mir e forklift
            '''for c in self.dosaggio.materie_prime.keys():
                if c in stato.df_stock_mp.index:
                    stato.df_stock_mp.loc[c, 'zona'] = 'S'
                    stato.df_stock_mp.loc[c, 'stato'] = 3
                else:
                    stato.df_stock_sl.loc[c, 'zona'] = 'S'
                    stato.df_stock_sl.loc[c, 'stato'] = 3'''

            stato.df_stock_mp['statonext'] = False
            self.saved.clear()

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
                        stato.df_stock_mp.loc[mp, 'stato'] = 4
                    else:
                        stato.df_stock_sl.loc[mp, 'stato'] = 4

                    yield self.hold(t_pes)
                    
                    #  rimuove dalla giacenza i kg di mp usata
                    if mp in stato.df_stock_mp.index:
                        stato.df_stock_mp.loc[mp,
                                              'qta'] -= self.dosaggio.materie_prime[mp]
                        
                    del self.dosaggio.materie_prime[mp]
                    if mp in stato.df_stock_mp.index:
                        if mp not in self.save_list:
                            stato.df_stock_mp.loc[mp, 'stato'] = 5
                            stato.df_stock_mp.loc[mp, 'zona'] = 'S'
                        else:
                            stato.df_stock_mp.loc[mp, 'stato'] = 3
                            stato.df_stock_mp.loc[mp, 'zona'] = 'S'
                            self.saved.append(mp)
                    else:
                        stato.df_stock_sl.loc[mp, 'stato'] = 5
                        stato.df_stock_sl.loc[mp, 'zona'] = 'S'

                    if len(self.dosaggio.materie_prime) == 0:
                        wait = False
                else:
                    yield self.wait((orologio, 1, True))
            #  --------------------
            self.dosaggio.fine_dosatura = env.now()
            print('Dosato {} '.format(self.dosaggio.ID), env.now(),
                  self.dosaggio.cono.rfid)
            stato.dict_throughput = module_stats_reeng.kg_cum(stato.dict_throughput,
                                                        env.now(),
                                                        self.dosaggio.kg,
                                                        'staz.dosaggio')
            call_dos.trigger(max=1)
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
            self.cono.posizione = 'HANDLING'
            yield self.hold(db_mir500_coni_pul.sample())
            #  yield self.hold(0)
            self.scarico = env.now()
            self.release()
            self.pulizia.activate()
        if self.mission == 'staz_auto dosaggio':
            self.cono.posizione = 'HANDLING'
            yield self.hold(db_mir500_coni_staz.sample())
            #  yield self.hold(0)
            self.scarico = env.now()
            self.release()
            self.dosaggio.activate()
        stato.dict_timestamp_mir500 =\
            module_stats_reeng.aggiorna_timestamp_mir500(self,
                                                   stato.dict_timestamp_mir500)
        yield self.passivate()


class Estrusore(sim.Component):
    def setup(self, n):
        self.n = n

    def process(self):
        global stato
        i = stato.estrusori.index(self.n)
        while True:
            while len(obj_buffer[i]) == 0:
                yield self.passivate()
            self.dosaggio = obj_buffer[i].pop()
            stato.df_OP.loc[[self.dosaggio.ID], 'stato'] = 'E'
            self.dosaggio.inizio_estrusione = env.now()
            self.dosaggio.cono.posizione = self.n
            extrusion_time = db_extrusion.sample()
            stato.dict_TER[self.n] = extrusion_time + env.now()
            yield self.hold(extrusion_time)
            self.dosaggio.fine_estrusione = env.now()
            print('estruso ', env.now(), str(
                self.n), self.dosaggio.cono.rfid)
            stato.check[self.n].append(self.dosaggio.estrusore)
            self.dosaggio.activate()


class PuliziaGenerator(sim.Component):
    def setup(self):
        self.pul_running = False

    def process(self):
        while True:
            if not self.pul_running:
                Pulizia()
            yield self.wait((orologio, True, 1))


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
                yield self.hold(db_pulizia.sample())
                #  yield self.hold(0)
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
                    module_stats_reeng.aggiorna_timestamp_pulizie(
                        self, stato.dict_timestamp_pulizie)
                break
        self.passivate()


# MAIN
# --------------------------------------------------
h_sim = 48  # totale di ore che si vogliono simulare
n_mission500_coni = 0
n_mission100 = 0
n_mission_forklift = 0

env = sim.Environment()
OrologioSim()

#  states
orologio = sim.State('orologio')
call_dos = sim.State('call_dos')
picking_list_refreshed = sim.State('picking_list_refreshed')
#  -------------

#  DosaggioGenerator()
DosaggioGeneratorAutoNoPicking()

mir500_coni = sim.Resource('MIR500 Coni', capacity=1)

fleet_manager_forklift = FleetManagerForklift()
fleet_manager_mir = FleetManagerMIR()

FL1 = Forklift(n='FL1')
FL2 = Forklift(n='FL2')
FL3 = Forklift(n='FL3')
FL4 = Forklift(n='FL4')
MIR1 = Mir100(n='MIR1')
MIR2 = Mir100(n='MIR2')
MIR3 = Mir100(n='MIR3')

fl_list = [FL1, FL2, FL3]
mir100_list = [MIR1]

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

# creazione Dataframe con tutti i timestamp pulizie
df_timestamp_pulizie = pd.DataFrame.from_dict(
    stato.dict_timestamp_pulizie).sort_values('richiesta_cono')

# creazione Dataframe con tutti i timestamp movimentazione coni
df_timestamp_mir500 = pd.DataFrame.from_dict(
    stato.dict_timestamp_mir500).sort_values('n_mission')

# creazione Dataframe con tutti i timestamp picking
df_timestamp_picking = pd.DataFrame.from_dict(
    stato.dict_timestamp_picking).sort_values('n_mission')

module_stats_reeng.plot_throughput(stato.dict_throughput)
module_stats_reeng.plot_quetot(stato.dict_elements)

print('Tempo richiesto', h_sim * 60)
print('TEMPO DI RUN ', datetime.now() - start)

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
sat_staz1 = stazione1.status.print_histogram(values=True, as_str=True)
sat_staz2 = stazione2.status.print_histogram(values=True, as_str=True)
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
satFL1 = FL1.status.print_histogram(values=True, as_str=True)
satFL2 = FL2.status.print_histogram(values=True, as_str=True)
satFL2 = FL2.status.print_histogram(values=True, as_str=True)
satFL3 = FL3.status.print_histogram(values=True, as_str=True)
satMIR1 = MIR1.status.print_histogram(values=True, as_str=True)
