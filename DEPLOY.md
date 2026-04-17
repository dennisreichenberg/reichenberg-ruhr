# Deployment: GitHub Pages + IONOS DNS

## Übersicht

Hosting: **GitHub Pages** (kostenlos, HTTPS automatisch)
DNS: **IONOS** (Domain reichenberg.ruhr, E-Mail bleibt unberührt)
Repo: https://github.com/amokK89/reichenberg-ruhr

---

## Einmalige Einrichtung

### 1. GitHub Pages aktivieren

Im GitHub-Repo:
- Settings → Pages
- Source: **GitHub Actions** auswählen (nicht "Deploy from a branch")
- Speichern

Der Deploy-Workflow (`.github/workflows/deploy.yml`) startet automatisch beim nächsten Push auf `master`.

### 2. DNS bei IONOS konfigurieren

Im IONOS-Kundencenter → Domains → reichenberg.ruhr → DNS:

**Für den Apex (reichenberg.ruhr) — 4 A-Records:**

| Typ | Name | Wert              | TTL  |
|-----|------|-------------------|------|
| A   | @    | 185.199.108.153   | 3600 |
| A   | @    | 185.199.109.153   | 3600 |
| A   | @    | 185.199.110.153   | 3600 |
| A   | @    | 185.199.111.153   | 3600 |

**Für www (optional):**

| Typ   | Name | Wert               | TTL  |
|-------|------|--------------------|------|
| CNAME | www  | amokK89.github.io  | 3600 |

> **Wichtig:** Bestehende MX-Records für E-Mail NICHT anfassen.
> Den alten XING-Redirect-Record löschen (falls als A- oder CNAME-Record vorhanden).

### 3. Custom Domain in GitHub Pages eintragen

Im GitHub-Repo → Settings → Pages → Custom domain:
- `reichenberg.ruhr` eintragen → Save
- "Enforce HTTPS" aktivieren (erscheint nach DNS-Propagation, ~30 min)

Die Datei `public/CNAME` im Repo enthält bereits `reichenberg.ruhr` und verhindert, dass GitHub die Domain bei jedem Deploy zurücksetzt.

---

## Laufende Updates

```bash
git add .
git commit -m "Update: [Beschreibung]"
git push
```

GitHub Actions deployt automatisch nach jedem Push auf `master`.

---

## Google Search Console

1. https://search.google.com/search-console → "Property hinzufügen"
2. Domain-Property: `reichenberg.ruhr`
3. TXT-Verifikationsrecord in IONOS DNS eintragen (Google gibt den Wert vor)
4. Nach Verifikation: Sitemap einreichen → `https://reichenberg.ruhr/sitemap-index.xml`

---

## Inhalte aktualisieren (Checkliste)

- [x] `public/profile.jpg` — Profilbild vorhanden
- [x] `src/components/Hero.astro` — `hasProfileImage` auf `true`
- [x] `src/pages/index.astro` — `og:image` gesetzt
- [ ] `src/components/TechStack.astro` — Platzhalter durch Dennis' echten Stack ersetzen
- [ ] Bio-Text von Dennis bestätigen lassen
