# questo modulo conterrà tutti gli oggetti queue che vengono
# usati nella simulazione

import salabim as sim
env = sim.Environment()

que_staz_dos = sim.Queue("que_staz_dos")
que_staz_dos_1 = sim.Queue("que_staz_dos_1")
que_staz_dos_2 = sim.Queue("que_staz_dos_2")

que_fictious = sim.Queue('que_fictious')

buffer_e1 = sim.Queue('buffer_e1')
buffer_e2 = sim.Queue('buffer_e2')
buffer_e3 = sim.Queue('buffer_e3')
buffer_e4 = sim.Queue('buffer_e4')
buffer_e5 = sim.Queue('buffer_e5')
buffer_e6 = sim.Queue('buffer_e6')
buffer_e7 = sim.Queue('buffer_e7')
buffer_e8 = sim.Queue('buffer_e8')
buffer_e9 = sim.Queue('buffer_e9')

obj_buffer = [buffer_e1, buffer_e2, buffer_e3,
              buffer_e4, buffer_e5, buffer_e6,
              buffer_e7, buffer_e8, buffer_e9]

# STATISTICHE SUI TEMPI DI ATTESA IN CODA
buff1 = buffer_e1.print_statistics(as_str=True)
buff2 = buffer_e2.print_statistics(as_str=True)
buff3 = buffer_e3.print_statistics(as_str=True)
buff4 = buffer_e4.print_statistics(as_str=True)
buff5 = buffer_e5.print_statistics(as_str=True)
buff6 = buffer_e6.print_statistics(as_str=True)
buff7 = buffer_e7.print_statistics(as_str=True)
buff8 = buffer_e8.print_statistics(as_str=True)
buff9 = buffer_e9.print_statistics(as_str=True)
