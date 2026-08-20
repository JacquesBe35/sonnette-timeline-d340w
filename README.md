# 🔔 Sonnette Timeline D340W

Timeline des **derniers appuis sur la sonnette Reolink D340W** (Front Door) affichée dans le
dashboard **echoshow15** de Home Assistant : **que les photos**, horodatées, du plus récent au
plus ancien. Aucune intégration vidéo (les clips restent dans Média → Reolink).

Projet neuf du 20/08/2026 — **ne reprend pas** les projets précédents
(`journal-visiteurs-d340w`, `journal-evenements-d340w`, supprimés de HAOS).

## Architecture

```
Appui sonnette (binary_sensor.front_door_visiteur → on)
   │
   ▼
automation.sonnette_timeline_appuis_photos
   │  ① camera.snapshot → /config/www/sonnette-events/AAAAMMJJ_HHMMSS.jpg
   │  ② calendar.create_event → calendar.sonnette (LOCATION = chemin photo)
   │  ③ shell_command.sonnette_cleanup (purge photos > 7 j)
   │  ④ homeassistant.update_entity → sensor.sonnette_timeline
   ▼
sensor.sonnette_timeline  (command_line : script → JSON {count, html, events})
   │  lit /config/.storage/local_calendar.sonnette.ics → HTML (8 derniers, photos 80×45)
   ▼
Vue « Sonnette » (dashboard echoshow15) → carte markdown
   {{ state_attr('sensor.sonnette_timeline', 'html') }}
```

Le calendrier local HAOS est la **source de vérité** des appuis ; le script ne fait que
l'afficher (images + heure + date).

## Composants (noms exacts sur HAOS)

| Type | Nom | Détail |
|---|---|---|
| Calendar | `calendar.sonnette` | Calendrier local HAOS (entrée config `local_calendar`, storage `.storage/local_calendar.sonnette.ics`) |
| Automation | `automation.sonnette_timeline_appuis_photos` | Déclencheur : `binary_sensor.front_door_visiteur` → `on` |
| Sensor | `sensor.sonnette_timeline` | `command_line` trigger-based, état = `value_json.count`, attributs `html`, `events` |
| Shell command | `shell_command.sonnette_cleanup` | `find /config/www/sonnette-events -type f -mtime +7 -delete` |
| Vue | « Sonnette » (path `sonnette`, icône `mdi:doorbell`) | Heading 🔔 + carte markdown |

## Fichiers du dépôt

| Fichier | Rôle |
|---|---|
| `config/configuration.yaml` | Extrait déployé : bloc `command_line:` + `shell_command:` (référence, fichier complet sur HAOS) |
| `config/automations.yaml` | Extrait déployé : automation `sonnette_timeline` (référence) |
| `config/lovelace.dashboard_echoshow15.json` | Dashboard complet avec la vue « Sonnette » (référence) |
| `config/local_calendar.sonnette.ics` | Calendrier vide initial (référence) |
| `scripts/sonnette_timeline.py` | Générateur de la timeline (ICS → HTML) |

## Déploiement (résumé réel, 20/08/2026)

1. **Backups** : `cp` horodatés `*.bak-sonnette-20260820_0912*` sur HAOS (configuration.yaml,
   automations.yaml, core.config_entries, lovelace.dashboard_echoshow15).
2. **Fichiers** : script → `/config/scripts/sonnette_timeline.py` (755), ICS →
   `/config/.storage/local_calendar.sonnette.ics`, configs → `/config/`.
3. **Calendrier** : entrée `local_calendar` « Sonnette » insérée dans
   `.storage/core.config_entries` (clone de l'entrée « Anniversaires », `data:
   {calendar_name, import: create_empty, storage_key}`).
4. **Redémarrage HA** : `homeassistant.restart` via API (wrapper Infisical) → ~15 s.
5. **Test à blanc** : `automation.trigger` → photo `20260820_091711.jpg` (32 Ko) + événement
   « 🔔 09:17 · Visiteur » + HTML avec `<img>` ✓.

## Réglages

| Paramètre | Emplacement | Valeur actuelle |
|---|---|---|
| Nombre d'entrées max | `scripts/sonnette_timeline.py` → `MAX` | 8 |
| Taille photo | `scripts/sonnette_timeline.py` → `width/height` | 80×45 px |
| Purge | `shell_command.sonnette_cleanup` | > 7 jours |
| Scan capteur | `config/configuration.yaml` → `scan_interval` | 60 s (+ `update_entity` après chaque appui) |

## Rollback

- Fichiers : restaurer les `*.bak-sonnette-20260820_0912*` + redémarrer HA.
- Calendrier : retirer l'entrée `Sonnette` de `core.config_entries` (+ supprimer
  `local_calendar.sonnette.ics`) + redémarrer.
- Vue : retirer la vue `sonnette` du dashboard.

## Pièges rencontrés

- **`sensor: - platform: command_line` est mort en HA 2026.7** : la plateforme n'est plus
  supportée en YAML classique (`create_platform_yaml_not_supported_issue`), l'entité n'est
  jamais créée **sans erreur visible**. Utiliser la syntaxe trigger-based :
  ```yaml
  command_line:
    - sensor:
        name: Sonnette Timeline
        unique_id: sonnette_timeline
        command: /config/scripts/sonnette_timeline.py
        command_timeout: 20
        scan_interval: 60
        value_template: "{{ value_json.count | default(0) }}"
        json_attributes: [html, events]
  ```
- **Horodatage décalé** : le format ICS `YYYYMMDDTHHMMSS` → `YYYYMMDD_HHMMSS` place l'heure
  aux indices 9-13 (pas 8-12, à cause du `_`).
- **Redémarrage HA** impossible depuis l'addon SSH (protection mode) → `homeassistant.restart`
  via API (wrapper Infisical) ou action Jacques (UI).
