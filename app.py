from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, date
from pony.orm import db_session, select, avg, sum, count, desc
from models import db, Trcanje, izracunaj_brzinu, init_db, get_statistike, get_udaljenosti_po_mjesecima, get_brzine_po_mjesecima, get_dostupne_godine
import os


app = Flask(__name__)
init_db()


@app.route("/")
@db_session
def index():
    trcanja = Trcanje.select().order_by(lambda t: desc(t.datum))

    #izračun osnovnih statistika
    ukupna_udaljenost = sum(t.udaljenost for t in trcanja) or 0
    prosjecna_brzina = avg(t.prosjecna_brzina for t in trcanja) or 0
    broj_trcanja = count(t for t in trcanja)

    #prikaz stranice s preddloškom index.html
    return render_template(
        "index.html",
        trcanja=trcanja,
        ukupna_udaljenost=round(ukupna_udaljenost, 2),
        prosjecna_brzina=round(prosjecna_brzina, 2),
        broj_trcanja=broj_trcanja
    )

#dodavanje novog trčanja
@app.route("/novo", methods=["GET", "POST"])
@db_session
def novo_trcanje():
    if request.method == "POST":
        datum_str = request.form["datum"]
        udaljenost_str = request.form["udaljenost"]
        trajanje_str = request.form["trajanje"]
        komentar = request.form.get("komentar")

        #validacija datuma
        if len(datum_str) == 10 and datum_str[4] == "-" and datum_str[7] == "-":
            dijelovi = datum_str.split("-")
            if all(d.isdigit() for d in dijelovi):
                datum = datetime.strptime(datum_str, "%Y-%m-%d")
                if datum.date() > date.today():
                    return "Datum ne može biti u budućnosti."
            else:
                return "Datum mora biti u formatu YYYY-MM-DD."
        else:
            return "Neispravan format datuma! Koristi YYYY-MM-DD."

        #validacija udaljenosti
        if udaljenost_str.replace(".", "", 1).isdigit():
            udaljenost = float(udaljenost_str)
            if udaljenost <= 0:
                return "Udaljenost mora biti veća od 0."
        else:
            return "Udaljenost mora biti broj."

        #validacija trajanja trčanja
        if trajanje_str.replace(".", "", 1).isdigit():
            trajanje = float(trajanje_str)
            if trajanje <= 0:
                return "Trajanje mora biti veće od 0."
        else:
            return "Trajanje mora biti broj."


        brzina = izracunaj_brzinu(udaljenost, trajanje)
        datum_komentara = datetime.now() if komentar else None

        Trcanje(
            datum=datum,
            udaljenost=udaljenost,
            trajanje=trajanje,
            prosjecna_brzina=brzina,
            komentar=komentar,
            komentar_datum=datum_komentara,
        )

        return redirect(url_for("index"))

    return render_template("create.html", today=date.today())

#uređivanje postojećeg trčanja
@app.route("/uredi/<int:trcanje_id>", methods=["GET", "POST"])
@db_session
def uredi_trcanje(trcanje_id):
    trcanje = Trcanje.get(id=trcanje_id)
    if not trcanje:
        return redirect(url_for("index"))

    if request.method == "POST":
        datum_str = request.form["datum"]
        udaljenost_str = request.form["udaljenost"]
        trajanje_str = request.form["trajanje"]
        novi_komentar = request.form.get("komentar") or None


        if len(datum_str) == 10 and datum_str[4] == "-" and datum_str[7] == "-":
            dijelovi = datum_str.split("-")
            if all(d.isdigit() for d in dijelovi):
                novi_datum = datetime.strptime(datum_str, "%Y-%m-%d")
                if novi_datum.date() > date.today():
                    return "Datum ne može biti u budućnosti."
                trcanje.datum = novi_datum
            else:
                return "Datum mora biti u formatu YYYY-MM-DD."
        else:
            return "Neispravan format datuma! Koristi YYYY-MM-DD."


        if udaljenost_str.replace(".", "", 1).isdigit():
            udaljenost = float(udaljenost_str)
            if udaljenost <= 0:
                return "Udaljenost mora biti veća od 0."
            trcanje.udaljenost = udaljenost
        else:
            return "Udaljenost mora biti broj."


        if trajanje_str.replace(".", "", 1).isdigit():
            trajanje = float(trajanje_str)
            if trajanje <= 0:
                return "Trajanje mora biti veće od 0."
            trcanje.trajanje = trajanje
        else:
            return "Trajanje mora biti broj."

        #ponovni izračun prosječne brzine
        trcanje.prosjecna_brzina = izracunaj_brzinu(trcanje.udaljenost, trcanje.trajanje)


        if novi_komentar != trcanje.komentar:
            trcanje.komentar = novi_komentar
            trcanje.komentar_datum = datetime.now() if novi_komentar else None

        return redirect(url_for("index"))

    return render_template("edit.html", trcanje=trcanje, today=date.today())


#brisanje trčanja
@app.route("/obrisi/<int:trcanje_id>", methods=["POST"])
@db_session
def obrisi_trcanje(trcanje_id):
    trcanje = Trcanje.get(id=trcanje_id)
    if trcanje:
        trcanje.delete()
    return redirect(url_for("index"))


#statistika trčanja po godinama i mjesecima
@app.route("/statistika")
@db_session
def statistika():
    godina = request.args.get('godina', type=int)

    statistike = get_statistike()

    udaljenosti_po_mjesecima = get_udaljenosti_po_mjesecima(godina)
    brzine_po_mjesecima = get_brzine_po_mjesecima(godina)
    dostupne_godine = get_dostupne_godine()

    mjeseci = ['Siječanj', 'Veljača', 'Ožujak', 'Travanj', 'Svibanj', 'Lipanj',
               'Srpanj', 'Kolovoz', 'Rujan', 'Listopad', 'Studeni', 'Prosinac']

    return render_template(
        "statistics.html",
        statistike=statistike,
        udaljenosti_po_mjesecima=udaljenosti_po_mjesecima,
        brzine_po_mjesecima=brzine_po_mjesecima,
        mjeseci=mjeseci,
        odabrana_godina=godina,
        dostupne_godine=dostupne_godine
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
