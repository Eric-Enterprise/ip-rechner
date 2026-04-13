# IP-Rechner

> Minimalistisches Subnetz-Tool für den Desktop — immer im Vordergrund, immer bereit.

![Python](https://img.shields.io/badge/Python-3.8+-3a6040?style=flat-square&logo=python&logoColor=white)
![GUI](https://img.shields.io/badge/GUI-customtkinter-1e3025?style=flat-square)
![Hotkey](https://img.shields.io/badge/Hotkey-pynput-1e3025?style=flat-square)
![License](https://img.shields.io/badge/Lizenz-MIT-4a6050?style=flat-square)

---

## Vorschau

```
┌─────────────────────────────────────┐
│  IP-Rechner              ⚙  –  ×   │
├─────────────────────────────────────┤
│  192.168.1.0        /  24     [▶]   │
├─────────────────────────────────────┤
│  Netzadresse    192.168.1.0         │
│  Broadcast      192.168.1.255       │
│  Subnetzmaske   255.255.255.0 (/24) │
│  Erster Host    192.168.1.1         │
│  Letzter Host   192.168.1.254       │
│  Hosts          254 Hosts           │
├─────────────────────────────────────┤
│  [hide]   [ghost]   [solid]         │
└─────────────────────────────────────┘
```

---

## Features

| Feature | Beschreibung |
|---|---|
| **CIDR-Kalkulation** | Netzadresse, Broadcast, Maske, erster/letzter Host und Hostanzahl auf einen Blick |
| **Always-on-Top** | Schwebt über jeder Anwendung, chromlos via `overrideredirect` |
| **Transparenzmodi** | `ghost` für unsichtbares Overlay, `solid` für volle Lesbarkeit |
| **Globaler Hotkey** | Frei konfigurierbare Taste blendet das Fenster ein/aus — auch ohne Fensterfokus |
| **Freie Positionierung** | Fenster per Titelleiste beliebig verschieben |
| **Einstellungen** | Hotkey aufnehmen, Alpha-Werte anpassen, Always-on-Top umschalten |
| **Minimieren** | Fenster auf reine Titelleiste reduzieren (24 px hoch) |

---

## Installation

### 1. Abhängigkeiten installieren

```bash
# Pflicht
pip install customtkinter

# Empfohlen — für globale Hotkeys ohne Fensterfokus
pip install pynput
```

### 2. Starten

```bash
python ip_rechner.py
```

### Linux / macOS — direkt ausführbar

```bash
chmod +x ip_rechner.py
./ip_rechner.py
```

---

## Abhängigkeiten

| Paket | Zweck | Status |
|---|---|---|
| `customtkinter` | Modernes Tkinter-Theme (Dark Mode, grüne Akzente) | **Pflicht** |
| `pynput` | Globale Tastenkombinationen ohne Fensterfokus | Optional |
| `struct`, `socket` | IP-Arithmetik (Standardbibliothek) | Stdlib |

> **Hinweis:** Ohne `pynput` funktioniert der Hotkey nur, wenn das Fenster selbst fokussiert ist. Ein entsprechender Hinweis erscheint dann im Einstellungs-Dialog.

---

## Bedienung

### Berechnung

1. IP-Adresse im ersten Feld eingeben (z. B. `10.0.0.0`)
2. CIDR-Präfix im zweiten Feld eingeben (z. B. `16`)
3. `▶` klicken **oder** `Enter` drücken

### Tastenkürzel

| Taste | Aktion |
|---|---|
| `H` *(Standard)* | Fenster global ein-/ausblenden |
| `Enter` | Berechnung auslösen |
| `Escape` | Programm beenden |
| `–` *(Titelleiste)* | Fenster auf Titelleiste minimieren |
| `⚙` *(Titelleiste)* | Einstellungen öffnen |

### Transparenz

- **ghost** — fast unsichtbar (Standard: 12 %), ideal als Hintergrund-Overlay
- **solid** — volle Deckkraft (Standard: 75 %)
- **hide / show** — Fenster vollständig ein-/ausblenden (Alpha = 0)

---

## Einstellungen

Über die `⚙`-Schaltfläche in der Titelleiste erreichbar:

- **Hotkey** — beliebige Taste durch Klick auf *„aufnehmen"* neu belegen
- **ghost %** — Alpha-Wert für den Ghost-Modus (1–99)
- **solid %** — Alpha-Wert für den Solid-Modus (1–100)
- **Immer vorne** — Always-on-Top ein-/ausschalten

---

## Berechnungslogik

```
Subnetzmaske  = 0xFFFFFFFF << (32 − CIDR)  &  0xFFFFFFFF
Netzadresse   = IP  &  Maske
Broadcast     = Netz  |  ~Maske

Erster Host   = Netz + 1        (für /0 – /30)
Letzter Host  = Broadcast − 1  (für /0 – /30)

/31  →  2 Hosts  (Punkt-zu-Punkt, RFC 3021)
/32  →  1 Host   (einzelne Adresse / Loopback)
```

---

## Projektstruktur

```
ip_rechner.py      # Gesamter Quellcode (eine Datei)
README.md          # Diese Datei
```

---

## Voraussetzungen

- Python **3.8** oder neuer
- Tkinter (in den meisten Python-Distributionen enthalten)
- Betriebssystem: Windows, macOS oder Linux

---

## Lizenz

MIT — freie Nutzung, Weitergabe und Modifikation erlaubt.
