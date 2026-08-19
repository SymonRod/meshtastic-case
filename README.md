# meshtastic-case

Custodia stampabile in 3D per un nodo Meshtastic, con guarnizione O-ring.

Generata in modo interamente parametrico via script Python/`bpy` per Blender:
nessun file `.blend` da versionare, tutte le quote sono costanti in cima a
[`build_case.py`](build_case.py), unica fonte di verità del progetto.

| Base | Coperchio |
|---|---|
| ![Base della custodia, vista interna](case_base_render.png) | ![Coperchio](case_lid_render.png) |

## Contenuto

- Cella **21700** (21 × 70 mm) in sella semicilindrica sul lato −Y, su tre
  bande da 12 mm anziché un blocco pieno
- **Seeed XIAO nRF52840 + Wio-SX1262** (stack 21 × 17.8 × 13 mm), appoggiato
  sul pavimento nella striscia libera lato +Y, fissato a biadesivo (nessun
  supporto stampato, nessuna asola USB)
- Connettore **N bulkhead** (filetto 5/8"-24) sulla parete −X, con scasso
  interno per dado e chiave
- **Guarnizione O-ring**: corda di silicone Ø3 mm in cava continua sul bordo
  della base (~312 mm di sviluppo)
- Chiusura con **6 viti M3** su inserti a caldo, in lug esterni fuori dalla
  linea di tenuta
- **4 alette M4** complanari al pavimento per il fissaggio al dorso del
  pannello solare (o a palo)
- Passacavo Ø5 nella parete +X (opposta all'antenna), da sigillare a silicone

Ingombro esterno: **117.8 × 58.8 × 32.1 mm**, **80.8 mm** in Y contando le
alette.

Il dettaglio di ogni scelta progettuale (perché le pareti sono a 6.4 mm,
perché la sella è divisa in tre bande, i vincoli sullo scasso del
connettore, ecc.) è documentato in [`CLAUDE.md`](CLAUDE.md).

## Montatura del pannello solare

Accessorio opzionale ([`build_mount.py`](build_mount.py)) per appendere un
pannello da ~170 × 170 mm **senza forarlo e senza toccare la custodia**: il
telaio si infila fra le teste delle sei viti M3 e il coperchio, e quattro clip
a scatto prendono il pannello per gli angoli.

![Telaio e clip montati sulla custodia](mount_assembly.png)

- Telaio a **H su tutte e sei le viti**: tre viti in fila, da sole, non
  bloccherebbero la rotazione attorno alla loro linea
- Appoggia **solo sui sei lug**, gli unici punti in cui il coperchio è
  sostenuto dalla vite: il coperchio non viene inarcato e la tenuta non si apre
- **Quattro clip identiche** (lo stesso pezzo ruotato di 0/90/180/270°), a
  scatto, con aletta per aprirle a mano
- Registrabili di ±12 mm in diagonale: **pannelli da 153 a 187 mm di lato**
  senza ristampare il telaio
- Tutto prismatico: **nessun supporto** in stampa

| Dettaglio di una clip |
|---|
| ![Clip d'angolo con il pannello inserito](mount_clip.png) |

Come si aggancia, in sezione attraverso una linguetta: il pannello scende, la
rampa a 45° apre la linguetta verso l'esterno di 1.5 mm, e appena il dorso
appoggia sul piano il dente scatta sopra la faccia anteriore.

![Sezione: pannello che scende e pannello agganciato](mount_clip_section.png)

## File

- `build_case.py` — sorgente parametrico, unica fonte di verità
- `case_base.stl`, `case_lid.stl` — output STL pronti per lo slicer
- `verify_case.py` — rigenera e verifica la geometria via ray-casting su
  punti campione (cava O-ring, spalle, cavità, fori)
- `build_mount.py` — montatura del pannello solare
- `panel_frame.stl` ×1, `panel_clip.stl` ×4 — output della montatura
- `verify_mount.py`, `render_mount.py` — verifica e render della montatura

## Rigenerare gli STL

Richiede [Blender](https://www.blender.org/) (testato con 4.x/5.x):

```sh
blender --background --factory-startup --python build_case.py
blender --background --factory-startup --python build_mount.py
```

Lo script cancella la scena, la ricostruisce da zero ed esporta gli STL
nella cartella corrente.

## Stampa

- Base: apertura verso l'alto, nessun supporto necessario
- Coperchio: piatto, nessun supporto
- Guarnizione: corda di silicone Ø3 mm, giuntata a colla nella cava
- Chiusura: 6 inserti filettati M3 a caldo + viti M3×10 a testa bombata
- Fissaggio: 4 viti/bulloni M4 nelle alette
- Montatura: telaio con i piedini sul piatto, clip con il piano d'appoggio sul
  piatto; niente supporti. Con la montatura le sei viti diventano **M3×16**
  (il telaio aggiunge 7.5 mm di pacco), più 4 M3×10 autofilettanti per le clip

## Licenza

[MIT](LICENSE)
