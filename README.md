# Python-test webapp

Funktionel prototype til starttest, midtvejstest, sluttest og evaluering.

## Lokal start

```powershell
python -m venv .venv
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:TEACHER_PASSWORD="vælg-en-adgangskode"
$env:SECRET_KEY="vælg-en-lang-hemmelig-nøgle"
python app.py
```

Åbn derefter http://127.0.0.1:5000

Hvis `TEACHER_PASSWORD` ikke er sat, er udviklingskoden `python123`. Brug ikke denne i drift.

## Før elever kan logge ind

1. Log ind som lærer.
2. Åbn **Elevliste**.
3. Indsæt ét pseudonymiseret elev-ID pr. linje, fx `1X01`.
4. Elever kan nu logge ind med disse ID'er.

Databasen `python_test.db` oprettes automatisk lokalt og er udelukket fra Git via `.gitignore`.

## Version 2

Denne version tilføjer:

- baggrundsspørgsmål om tidligere programmeringserfaring før starttesten
- baggrundsdata som separate variable, der ikke påvirker testscores
- tilfældig rækkefølge af svarmuligheder ved hver testvisning
- baggrundsstatus i elev- og lærerdashboard
- baggrundsdata i CSV-eksporten

Svarmulighederne blandes kun visuelt. Det korrekte svar gemmes fortsat korrekt på serversiden.

## Version 3

Læreren kan nu åbne og lukke midtvejs- og sluttesten fra lærerdashboardet.

- Midtvejstesten er lukket som standard.
- Sluttesten er lukket som standard.
- En elev kan ikke omgå dette ved at skrive test-URL'en direkte.
- Starttesten er fortsat tilgængelig, når baggrundsspørgsmålene er udfyldt.


## Færdiggørelsesversion

Appen opretter automatisk 17 ikke-systematiske elev-ID'er:

T3EV, WHQA, TYPB, PTXJ, FHFB, YHBV, BR68, G8Z2, 3Q7U, XU4Q, B8KX, 3Q7J, F9A6, MFQ4, 6VV8, 33E3, N277

Derudover oprettes TEST01 og TEST02.

Læreren kan fortsat tilføje flere ID'er via **Elevliste**.

Vigtigt: Webappen gemmer ikke elevnavne. Hvis du vil kunne koble et elev-ID til en bestemt elev, skal du opbevare den kobling separat fra webappen.

## Detaljeret CSV-eksport

CSV-eksporten indeholder nu:

- baggrund om tidligere programmeringserfaring
- score, maksimum, procent og dato for start-, midtvejs- og sluttest
- progression fra start til slut i procentpoint
- resultat pr. kompetenceområde for hver test
- elevens evaluering af Escape Room og Wokwi
- elevens selvtillid efter forløbet
- kvalitative svar og kommentarer

Eksporten bruger den seneste gennemførsel af hver testfase pr. elev.
