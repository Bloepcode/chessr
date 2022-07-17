# Chessr

Een schaakcomputer met image detection!

## Installatie:

Word nog aan gewerkt...

## Gebruik:

`python3 start.py`

- `-c/--codes`: `out_codes.json`, het bestand waar informatie over het schaakbord in staan (zoals de positie van het schaakbord)
  - Default: `None`, start automatisch kalibratie modus.
  - Notes: Start kalibratie modus **elke keer** als je de camera of het schaakbord verplaatst!
- `-b/--board`: `board.txt`, het bestand waar het bord in wordt opgeslagen
  - Default: `None` begin met de begin positie.
- `-s/--skill` De skill van de ai (0 tot 20)
  - Default: `5`
- `-c/--cam` Het ID van de camera
  - Default: `2`
