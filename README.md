# Python-progression – prototype

En enkel Flask-webapp til starttest, midtvejstest, sluttest og evaluering af et Python-undervisningsforløb.

## Start lokalt

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Åbn derefter `http://127.0.0.1:5000`.

## Funktioner
- anonymt elev-ID
- starttest uden visning af facit
- midtvejstest med læringsfeedback efter aflevering
- sluttest uden facit og med kompetenceprofil
- elevens progression
- evaluering af Escape Room, Wokwi og oplevet sikkerhed
- lærerdashboard
- CSV-eksport

## Prototypebemærkninger
Lærerdashboardet har endnu ikke login/adgangskontrol. Før brug med rigtige elever bør der tilføjes lærerlogin, CSRF-beskyttelse, bedre sessionsikkerhed og en beslutning om datalagring/GDPR.
