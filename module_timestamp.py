def aggiorna_timestamp(self, dict_timestamp):
    dict_timestamp['ID'].append(self.dosaggio.ID)
    dict_timestamp['estrusore'].append(self.dosaggio.estrusore)
    dict_timestamp['RFID'].append(self.dosaggio.cono.rfid)
    dict_timestamp['inizio_dosatura'].append(
        int(self.dosaggio.inizio_dosatura))
    dict_timestamp['fine_dosatura'].append(int(self.dosaggio.fine_dosatura))
    dict_timestamp['ingresso_buffer'].append(
        int(self.dosaggio.ingresso_buffer))
    dict_timestamp['inizio_estrusione'].append(
        int(self.dosaggio.inizio_estrusione))
    dict_timestamp['ingresso_gualchierani'].append(int(
        self.dosaggio.ingresso_gualchierani))
    dict_timestamp['fine_gualchierani'].append(
        int(self.dosaggio.fine_gualchierani))
    dict_timestamp['t_tot'].append(int(self.dosaggio.fine_gualchierani)
                                   - int(self.dosaggio.inizio_dosatura))
    return(dict_timestamp)


def aggiorna_timestamp_dos(self, dict_timestamp):
    dict_timestamp['ID'].append(self.ID)
    dict_timestamp['estrusore'].append(self.estrusore)
    dict_timestamp['RFID'].append(self.cono.rfid)
    dict_timestamp['inizio_dosatura'].append(
        int(self.inizio_dosatura))
    dict_timestamp['fine_dosatura'].append(int(self.fine_dosatura))
    dict_timestamp['ingresso_buffer'].append(
        int(self.ingresso_buffer))
    dict_timestamp['inizio_estrusione'].append(
        int(self.inizio_estrusione))
    dict_timestamp['ingresso_gualchierani'].append(int(
        self.ingresso_gualchierani))
    dict_timestamp['fine_gualchierani'].append(
        int(self.fine_gualchierani))
    dict_timestamp['t_tot'].append(int(self.fine_gualchierani)
                                   - int(self.inizio_dosatura))
    return(dict_timestamp)
