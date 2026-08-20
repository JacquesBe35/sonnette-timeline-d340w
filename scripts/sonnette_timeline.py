#!/usr/bin/env python3
"""Timeline Sonnette D340W — génère le HTML des dernières photos d'appui.

Lit le calendrier local HAOS « Sonnette » (ICS) et affiche les N derniers
appuis sous forme de photos horodatées (que les photos : pas de vidéo,
pas de description). Sortie JSON pour capteur command_line :
{"count", "html", "events"}.
"""
import json
import os
import re

ICS = "/config/.storage/local_calendar.sonnette.ics"
IMG_DIR = "/config/www/sonnette-events"
MAX = 8


def parse_events(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = f.read()
    except FileNotFoundError:
        return []
    events = []
    for block in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", data, re.S):
        def field(name):
            m = re.search(rf"^{name}:(.*)$", block, re.M)
            return m.group(1).strip() if m else ""

        dtstart = field("DTSTART")  # YYYYMMDDTHHMMSS (heure locale)
        if len(dtstart) < 15:
            continue
        events.append({"ts": dtstart.replace("T", "_")})
    events.sort(key=lambda e: e["ts"], reverse=True)
    return events[:MAX]


def main():
    events = parse_events(ICS)
    rows = []
    for ev in events:
        ts = ev["ts"]  # YYYYMMDD_HHMMSS
        local = f"{IMG_DIR}/{ts}.jpg"
        if not os.path.exists(local):
            continue
        hhmm = f"{ts[9:11]}:{ts[11:13]}"
        date = f"{ts[6:8]}/{ts[4:6]}/{ts[0:4]}"
        rows.append(
            '<div style="display:flex;align-items:center;gap:8px;padding:4px 0;'
            'border-bottom:1px solid rgba(255,255,255,0.12);">'
            f'<img src="/local/sonnette-events/{ts}.jpg" '
            'style="width:80px;height:45px;object-fit:cover;border-radius:6px;'
            'flex-shrink:0;" '
            f'onerror="this.style.display=\'none\'">'
            f'<div style="line-height:1.3;"><b style="font-size:1em;">{hhmm}</b><br>'
            f'<span style="color:#999;font-size:0.85em;">{date}</span></div></div>'
        )
    if not rows:
        html_out = (
            '<p style="color:#888;text-align:center;padding:24px 0;">'
            "Aucune photo pour le moment.</p>"
        )
    else:
        html_out = "".join(rows)
    print(json.dumps(
        {"count": len(rows), "html": html_out,
         "events": [e["ts"] for e in events]},
        ensure_ascii=False,
    ))


if __name__ == "__main__":
    main()
