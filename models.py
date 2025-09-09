from pony.orm import Database, PrimaryKey, Required, Optional, select, avg, sum, count, desc, distinct, db_session
from datetime import datetime
import calendar

db = Database()

#entitet Trčanje
class Trcanje(db.Entity):
    id = PrimaryKey(int, auto=True)
    datum = Required(datetime)
    udaljenost = Required(float)
    trajanje = Required(float)
    prosjecna_brzina = Required(float)
    komentar = Optional(str)
    komentar_datum = Optional(datetime)


#izračun prosječne brzine u km/h, zaokruženo na 2 decimale
def izracunaj_brzinu(udaljenost_km: float, trajanje_min: float) -> float:
    if trajanje_min <= 0:
        return 0.0
    return round(udaljenost_km / (trajanje_min / 60.0), 2)


#računanje ukupne udaljenosti, prosječne brzine i broja trčanja
def get_statistike():
    with db_session:
        ukupna_udaljenost = select(sum(t.udaljenost) for t in Trcanje).first() or 0
        prosjecna_brzina = select(avg(t.prosjecna_brzina) for t in Trcanje).first() or 0
        broj_trcanja = select(count(t) for t in Trcanje).first() or 0

        return {
            'ukupna_udaljenost': round(ukupna_udaljenost, 2),
            'prosjecna_brzina': round(prosjecna_brzina, 2),
            'broj_trcanja': broj_trcanja
        }

#zbroj udaljenosti po mjesecima za zadanu godinu ili za sve godine
def get_udaljenosti_po_mjesecima(godina=None):
    with db_session:
        if godina:
            trcanja = select(t for t in Trcanje if t.datum.year == godina)
        else:
            trcanja = select(t for t in Trcanje)

        mjeseci = {i: 0 for i in range(1, 13)}

        for t in trcanja:
            mjesec = t.datum.month
            mjeseci[mjesec] += t.udaljenost

        rezultat = [round(mjeseci[i], 2) for i in range(1, 13)]
        return rezultat


#prosječna brzina po mjesecima za zadanu godinu ili za sve godine
def get_brzine_po_mjesecima(godina=None):
    with db_session:
        if godina:
            trcanja = select(t for t in Trcanje if t.datum.year == godina)
        else:
            trcanja = select(t for t in Trcanje)

        mjeseci = {i: {'suma': 0, 'broj': 0} for i in range(1, 13)}

        for t in trcanja:
            mjesec = t.datum.month
            mjeseci[mjesec]['suma'] += t.prosjecna_brzina
            mjeseci[mjesec]['broj'] += 1

        rezultat = []
        for i in range(1, 13):
            if mjeseci[i]['broj'] > 0:
                prosjek = mjeseci[i]['suma'] / mjeseci[i]['broj']
                rezultat.append(round(prosjek, 2))
            else:
                rezultat.append(0)
        return rezultat


#lista godina za koje postoje zapisi
def get_dostupne_godine():
    with db_session:
        # Dohvati sve datume i izvuci jedinstvene godine
        sve_godine = select(t.datum.year for t in Trcanje)
        jedinstvene_godine = sorted(set(sve_godine), reverse=True)
        return jedinstvene_godine

def init_db():
    db.bind(provider='sqlite', filename='joglog.sqlite', create_db=True)
    db.generate_mapping(create_tables=True)
