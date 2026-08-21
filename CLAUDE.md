# meshtastic-case

Custodia stampabile in 3D per un nodo Meshtastic, con guarnizione O-ring.

## Contenuto

- Cella **21700** (21 × 70 mm) in sella semicilindrica sul lato −Y, su **tre
  bande** da 12 mm anziché un blocco pieno
- **Seeed XIAO nRF52840 + Wio-SX1262** (stack 21 × 17.8 × 13 mm) **ruotato di
  90°**, appoggiato sul pavimento nella striscia libera lato +Y. **Nessun
  supporto stampato**: si fissa a biadesivo. Nessuna asola USB.
- Connettore **N bulkhead** (filetto 5/8"-24 ≈ 15.88 mm), foro Ø16.4 mm centrato
  nella parete −X a z = 14.4, con scasso **interno** Ø23 × 4 (faccia esterna
  piana: il dado appoggia a filo e la chiave lo prende)
- **Guarnizione O-ring**: corda di silicone Ø3 mm in cava continua sul bordo
  della base (~312 mm di sviluppo, da giuntare a colla), schiacciata al 33%
- Chiusura con **6 viti M3** su inserti a caldo, in lug esterni **fuori dalla
  linea di tenuta**, raccordati R3 nelle pareti
- **4 alette M4** complanari al pavimento per il fissaggio al dorso del pannello
  solare (o a palo), interasse 76 × 71.8 mm, spigoli esterni smussati 3 × 45° e
  due nervature per aletta affiancate al foro
- **Passacavo Ø5** nella parete +X (opposta all'antenna) a y = 9, z = 15, da
  sigillare a silicone

Ingombro esterno: **117.8 × 58.8 × 32.1 mm**, che diventa **80.8 mm in Y**
contando le alette.

## Montatura del pannello solare

**Un pezzo solo**, in `scripts/build_mount.py`. La scatola **non viene toccata**:
nessun foro nuovo, nessun inserto nuovo, nessuna quota di `build_case.py`
modificata.

- `models/panel_mount.stl` ×1 — anello rettangolare che si infila **fra le teste
  delle viti e il coperchio** usando tutte e sei le M3 esistenti, quattro
  bracci diagonali e quattro teste d'angolo con le linguette a scatto.

Ingombro 175.6 × 175.6 × 12.2 mm, ~22 g in PETG a riempimento 30%. Il pannello
appoggia 8 mm sopra il coperchio.

Il pannello è di **misura fissa** (`PANEL_W`, `PANEL_H`). È la scelta che ha
permesso il pezzo unico: la versione precedente aveva telaio + 4 clip
registrabili, e asole, guide a 45°, piastrini, svasi e quattro viti
autofilettanti esistevano **tutti e soli** per rendere le clip riposizionabili.
Se un giorno serve la regolabilità, si rimette quella meccanica — non si
cerchi di ottenerla deformando questo pezzo.

## Struttura dei file

- `scripts/build_case.py` — sorgente parametrico, unica fonte di verità. Tutte le quote
  sono costanti in cima al file.
- `models/case_base.stl`, `models/case_lid.stl` — output rigenerati a ogni run.
- `models/oring_groove_shim.stl` — rialzo da 0.20 mm per aggiornare la cava O-ring
  3.8 × 2.2 di un case gia` stampato. E` un binario centrale largo 1.8 mm,
  non una fascia larga quanto la cava: cosi` recupera la compressione senza
  togliere al silicone il volume laterale in cui spanciare.
- `models/oring_groove_shim_high_compression.stl` — variante 0.30 × 1.20 mm: porta
  la compressione al 37% conservando lo stesso volume libero della cava nuova.
- `scripts/build_oring_shim.py` — sorgente autonomo del rialzo.
- `scripts/verify_case.py` — rigenera e sonda ~150 punti campione (vedi *Verifica*).
- `scripts/build_mount.py` — montatura del pannello, stessa filosofia: quote in cima,
  `models/panel_mount.stl` rigenerato a ogni run.
- `scripts/verify_mount.py` — topologia (un solo guscio, chiuso) + ~660 punti campione
  sulla montatura.
- `scripts/render_mount.py` — render di controllo dell'assieme.
- `scripts/render_corner_section.py` — sezione della testa d'angolo: come si aggancia.
- `scripts/render_seal_section.py` — sezione della tenuta, corda libera e schiacciata
  affiancate (`renders/seal_section.png`). Taglia con booleane **gli STL importati**,
  non un modello ricostruito: se i file nella cartella non corrispondono più al
  sorgente, il render lo fa vedere invece di nasconderlo. Perciò **non esegue
  `build_case.py`** e non riscrive niente — l'unica cosa disegnata è la corda,
  che negli STL non c'è, e le sue quote si leggono dal sorgente con lo stesso
  mini-parser di `check_case_interface()`. La sezione compressa è a **volume
  costante** (rettangolo alto `GROOVE_D` con i fianchi a semicerchio, largo
  quanto serve perché l'area torni quella della corda tonda): è così che si
  legge il riempimento e l'aria che resta ai fianchi, 0.02 mm per lato.
  L'importer lascia la mesh con più di un utente e `modifier_apply` si
  rifiuta di lavorarci: si stacca con `ob.data = ob.data.copy()` subito dopo
  l'import.
- `scripts/render_shim_section.py` — sezione specifica del case gia` stampato con cava
  3.8 × 2.2 e rialzo ad alta compressione 1.2 × 0.3. Recupera da git gli STL
  reali del commit `3188763`, precedente al cambio della cava, e importa lo
  STL reale del rialzo. Produce `renders/seal_shim_section.png`.
- `tools/` — utility di sviluppo non richieste per generare o verificare i pezzi.

## Rigenerare

```
blender --background --factory-startup --python scripts/build_case.py
blender --background --factory-startup --python scripts/build_mount.py
blender --background --factory-startup --python scripts/build_oring_shim.py
```

Funziona anche da shell. In `/usr/bin/blender` c'è **Blender 4.0.2**, che non
ha `bpy.ops.wm.stl_export`: gli script scelgono da soli fra quello e
`bpy.ops.export_mesh.stl` (4.0/4.1). Gli output vanno sempre in `models/` o
`renders/`, indipendentemente dalla directory da cui si lanciano. Gli script
cancellano la scena e la ricostruiscono da zero. Ignora l'errore
`ModuleNotFoundError: cattrs` all'avvio: è un addon di sistema, non riguarda noi.

## Convenzioni geometriche

- X = asse lungo della cella; Z+ = alto; origine al centro della base.
- La base stampa con l'apertura verso l'alto, il coperchio piatto.

### Tenuta

- Le pareti sono spesse **6.4 mm** perché è la larghezza minima che ospita la
  cava dell'O-ring: 1.2 (spalla interna) + 4.0 (cava) + 1.2 (spalla esterna).
  Non assottigliarle senza rifare questo conto. Il pavimento resta a 2.4.
- Cava **4.0 × 2.0** per corda Ø3: schiacciamento 1.0 mm (33%), riempimento 88%.
  Il coperchio va in **battuta sulle spalle**, che fanno da fine corsa: è la
  battuta a definire la compressione, non il serraggio delle viti.
  Era **3.8 × 2.2** (27%, 85%): sulla carta a norma, in pratica senza margine
  per la planarità di un coperchio stampato lungo 118 mm, e alla prova della
  doccia (21/08/2026) passava acqua. La cava è stata approfondita **e**
  allargata insieme: il riempimento deve restare **sotto il 90%**, altrimenti
  la corda — incomprimibile — non ha dove spanciare e fa da distanziale
  impedendo la battuta, che è il modo più veloce per aprire la tenuta invece
  di chiuderla. `GROOVE_MID` resta 3.2, quindi raggi d'angolo e mezzeria non
  si sono mossi e nulla a valle è cambiato.
- Le **viti stanno fuori dalla tenuta**, su sei lug esterni. È il vincolo che ha
  dettato tutto il resto: se il boss è dentro l'anello, l'acqua che entra nel
  foro del coperchio arriva in cavità passando sopra la testa del boss. Non
  riportare i boss dentro la scatola.
- Sei viti e non quattro: il coperchio è lungo 117.8 mm e con appoggi solo agli
  angoli la cava non riceve pressione in mezzeria. I lug centrali sono a x = 0.
- Gli spigoli verticali interni sono **raccordati R6** apposta. Il raggio serve
  alla cava: con la cavità a spigolo vivo, un anello di raggio decente
  assottiglierebbe la spalla interna negli angoli. Con R6 il centro d'angolo
  della cavità, del labbro e della cava coincide, e la spalla resta 1.3 mm
  ovunque, anche in curva; la corda piega su R9.2, un raggio che il silicone
  Ø3 accetta senza strozzarsi. **Se cambi `INNER_R`, `GROOVE_R` lo segue
  automaticamente — ma non portare `INNER_R` sotto ~5** o l'O-ring inizia a
  strozzarsi negli angoli.
- Il labbro del coperchio è una **cornice** da 3 mm (anello a sezione
  rettangolare), **non un tappo pieno**: un blocco pieno riempirebbe tutta la
  sezione da z = 25.9 in su e appoggerebbe sulla cella invece che sul bordo. Il
  labbro **non fa tenuta**, centra e basta: la tenuta è più esterna.

### Interno

- Il connettore N sporge **20 mm** verso l'interno (corpo metallico + coda di
  cavo rigida). Per questo `INNER_X` è 105 e la cella è spostata a `CELL_CX =
  +4.5`: i primi 20 mm a partire dalla parete −X sono camera libera. **Non
  ricentrare la cella a x=0** e non ridurre `INNER_X` senza rifare questo conto.
- Con la parete a 6.4 mm il filetto del bulkhead non uscirebbe abbastanza per il
  dado, quindi lo spessore utile va riportato a 2.4. Lo scasso che lo fa sta
  **dentro** (`CONN_RELIEF_D, CONN_RELIEF_DEPTH` = Ø23 × 4, tagliato dalla
  faccia interna verso l'esterno): la faccia **esterna resta piana e a filo**,
  così il dado del bulkhead ci appoggia sopra in piano ed è raggiungibile con
  la chiave. **Non riportare lo scasso fuori**: c'era, e infossava il foro in
  una tasca Ø24 dove il dado non si riesce né ad appoggiare né a stringere.
- Lo scasso interno arriva a z = 25.9 e il fondo della cava è a 26.7: restano
  **0.8 mm**. È questo il vincolo che fissa `INNER_Z` a 26.5 — abbassandolo (o
  allargando `CONN_RELIEF_D`), lo scasso sfonda nella cava e la guarnizione
  perde.
- L'anello di guarnizione del connettore (Ø22 mm) appoggia **piatto** sul fondo
  dello scasso (x = −56.5), che è la sua sede: quei 22 mm di superficie devono
  restare liberi e Ø23 lascia 0.5 mm per lato. Arriva a z = 25.4 e il labbro del
  coperchio scende a 25.9: passa per 0.5 mm. (In una versione precedente non
  passava e il labbro era interrotto lì; ora non serve più, la cornice è
  continua — **non reintrodurre quell'intacco**, aprirebbe la tenuta.)
- Il corpo del connettore parte quindi 4 mm più indietro rispetto alla faccia
  interna: dei 20 mm di camera libera ne restano 4 di margine. `CELL_CX` non è
  stato spostato apposta, quel margine è benvenuto.
- Lo stack XIAO è ruotato di 90° attorno a Z (`BOARD_X, BOARD_Y = 17.8, 21.0`):
  serve a far guardare i bordi corti verso ±X, così il connettore IPEX
  dell'antenna — su qualunque bordo si trovi — non punta mai contro la sella
  della cella. **Non riportarlo nell'orientamento originale.** Le quote della
  scheda restano nel sorgente solo per stampare a video gli spazi liberi
  (striscia da 22.3 mm fra sella e parete +Y: la sella è stata allargata a
  `CRADLE_MARGIN` 1.6 per non lasciare il fianco a lama al labbro, e quella
  striscia è ciò che ha pagato — restano 0.65 mm per lato attorno alla scheda,
  quindi `CRADLE_MARGIN` non si può alzare ancora).
- **Niente dentini, niente costole per la scheda**: si fissa a biadesivo. Sono
  stati rimossi apposta. Niente asola USB: ruotata la scheda, la porta guarda ±X
  dove non c'è parete raggiungibile; per riflashare si apre il coperchio.
- La sella è fatta di **tre bande** da 12 mm (estremità e mezzeria, a x =
  `CELL_CX` ± 29), non di un blocco continuo da 70: il blocco pieno era il
  pezzo più pesante della scatola e non serviva a nulla in mezzo.
- L'altezza della sella **non è un parametro libero**: `CRADLE_H = CELL_CZ`,
  cioè il labbro sta esattamente sull'equatore della cella. È l'unica quota per
  cui la bocca della culla vale quanto lo scavo (Ø 21.6) e quindi **qualunque
  cella che sta nella culla ci scende dall'alto**. Abbassandola la bocca si
  stringe e la cella appoggia sui due spigoli del labbro invece che sull'arco:
  la vecchia sella da 7 mm lasciava una bocca di 20.06 mm, cioè 0.47 mm di
  interferenza per lato su fianchi che non flettono.
- Sul fondo della culla c'è una **gola di sfogo** larga 8 (`CRADLE_RELIEF_W`).
  Serve a togliere la lametta di materiale che il cilindro di scavo lascia sopra
  il pavimento. **Non provare a eliminarla portando `CELL_CZ` a `CELL_R`**: il
  cilindro diventa tangente al pavimento e la linea di tangenza è uno spigolo a
  quattro facce, non-manifold, lungo tutta la cella. Per lo stesso motivo la
  gola è più alta di 0.4 mm del punto in cui incontra il cilindro: se ci si
  fermasse esattamente sopra, la tangenza tornerebbe sui due spigoli.
- Gli smussi delle bande vanno tenuti **piccoli**. Al labbro il fianco è spesso
  solo `CRADLE_MARGIN` (1.6 mm): uno smusso confrontabile con quello spessore
  non arrotonda l'angolo, lo riduce a un cuneo che va a zero. Lo smusso
  d'angolo in pianta era 1.5 e lasciava una punta da 0.1 mm. Il controllo è
  `CRADLE_LIP_MIN` (piano residuo sul labbro, ≥ 0.8), verificato da un test.
- **Niente invito sul labbro della culla**: c'era (0.4 × 45°, tagliato in YZ
  lungo la banda) e negli angoli incontrava lo smusso d'angolo lasciando una
  faccetta triangolare che si assottigliava fino a zero. Non serve: la bocca
  vale già quanto lo scavo. Il labbro resta uno spigolo netto.
- **Niente costola ferma-cella sul coperchio**: la vecchia costola premeva sulla
  cella e inarcava il coperchio, che è esattamente ciò che apre la tenuta. La
  cella la tiene un biadesivo gommoso. Non rimetterla.
- Il passacavo del pannello è un **foro nudo Ø5** nella parete +X, spostato a
  y = +9 per stare lontano dalla cella (che arriva a y = −0.9) e lasciare
  liberi gli 11 mm davanti al polo + per il contatto. Si sigilla a silicone.
  Niente pressacavo PG: era troppo ingombrante e vincolava una sede piana.

### Esterno

- Le alette di fissaggio sono **complanari al pavimento** (z da 0 a 4) apposta:
  qualunque sporgenza *sotto* il pavimento (rail, coda di rondine) costringerebbe
  a stampare l'intera scatola su supporti. Non spostarle sotto. Le nervature a
  45° che le collegano alla parete sono autoportanti.
- Le nervature sono **due per aletta, affiancate al foro** (asse a x = ±5.3
  dall'asse dell'aletta, spessore 2.6): fra la loro faccia interna e il foro
  M4 restano 1.75 mm, così testa e rondella appoggiano in piano sul dorso.
  **Non tornare alla nervatura unica centrata sull'asse**: era larga 3 mm
  proprio sopra il foro e, arrivando a 8 mm dalla parete contro un foro
  centrato a 6.5, ci lasciava sopra un ponte di ~0.4 mm che tappava il passante.
- I due spigoli esterni di ogni aletta sono **smussati 3 × 45°** (`EAR_CHAMF`,
  taglio verticale nel profilo estruso, quindi nessun costo in stampa). Il
  piede delle nervature deve restare **dentro** il profilo smussato: con
  nervatura lunga 8 e smusso che parte a 8 dalla parete, il bordo esterno
  della nervatura (a 6.6 dall'asse) trova il profilo a 8.4. Se allunghi
  `EAR_GUSSET_H` o allarghi lo smusso, rifai questo conto o la nervatura
  finisce a sbalzo sul vuoto.
- I lug delle viti sono **colonne piene da terra al bordo**: così non hanno
  sbalzi e non servono nervature. Stanno a x = 0, ±52 e y = ±31.6; fra il foro
  dell'inserto e il bordo esterno della cava restano 1.8 mm.
- I lug non nascono a spigolo dalla parete: c'è un **raccordo concavo R3**
  (`LUG_FILLET`, `lug_fillets`) che li fonde nella parete come una nervatura
  tonda, per ~±7.6 mm attorno a ogni lug. È un cerchio tangente insieme alla
  faccia esterna della parete e al cilindro del lug, estruso in verticale: si
  costruisce come blocco d'angolo meno i due cilindri di raccordo. Tre cose da
  non toccare:
  - va **fuso prima delle forature**: il blocco copre anche l'asse del lug e,
    se arrivasse dopo, ritapperebbe il foro dell'inserto;
  - il blocco si chiude al **punto di tangenza** (`LUG_FIL_TOP`), non al centro
    del cerchio di raccordo: oltre quel punto non c'è più raccordo e la lama
    fra i due cilindri manda in schegge il solver EXACT;
  - il tutto è **intersecato con l'ingombro in X del corpo**, perché il
    raccordo dei lug d'angolo finirebbe 0.7 mm oltre la parete ±X. Lì il
    taglio è alto 0.07 mm, quindi non si vede.
  Sul coperchio c'è lo stesso raccordo con le stesse quote: i due profili
  devono coincidere, altrimenti resta uno scalino sopra il piede dei lug.
- **Niente smusso sui bordi dei lug**: c'era (`lug_chamfers`, 45° sopra e
  sotto), è stato rimosso perché non serviva. Non rimetterlo: l'utensile
  conico rasenta tangenzialmente la superficie del raccordo e il solver
  EXACT ci si spacca.
- Il coperchio è a 3.2 mm: **niente svasatura**, si usano viti M3 a testa bombata
  (M3×10) che sporgono. Una svasatura lascerebbe troppo poco materiale e
  ridurrebbe la rigidezza, che qui serve a comprimere la guarnizione.

### Montatura del pannello (`build_mount.py`)

- È **un pezzo solo**: anello + bracci + teste d'angolo con le linguette. Non
  tornare a telaio e clip separate. Le clip erano separate per essere
  *registrabili*, e la registrazione (asole, guida a 45°, piastrini, svasi,
  quattro viti autofilettanti) era metà della complessità del file. Il pannello
  ora è di misura fissa: si cambiano `PANEL_W`/`PANEL_H` e si ristampa.
- L'anello usa **tutte e sei** le viti ed è **chiuso**. Non spezzarlo in due
  staffe a U, una per lato: le tre viti di un lato sono **allineate**, e tre
  punti in fila non bloccano la rotazione attorno alla loro linea. Due staffe
  separate farebbero cerniera e il pannello sbatterebbe. Sono le traverse
  d'estremità a chiudere il vincolo.
- Le traverse d'estremità stanno a `END_X` = 62, cioè **fuori dall'ingombro
  della scatola** (`CASE_HX` = 58.9). È deliberato: così del coperchio il pezzo
  tocca solo la striscia sopra i lug e sopra le pareti da 6.4 mm — materiale
  sostenuto — e mai la campata centrale, che è quella che inarcandosi aprirebbe
  la tenuta. **Non portare le traverse verso il centro** per accorciare il
  pezzo.
- **Niente piedini.** La versione precedente teneva il piano a `FOOT_H` = 3.5
  sopra il coperchio, appoggiato su sei piedini: geometricamente corretto e
  **instampabile**, perché un piano di 170 mm sospeso su sei colonnine Ø9.2
  vuole i supporti sotto tutto, e capovolgendo il pezzo finiscono in aria i
  bracci. Qui il corpo parte da z = 0 e appoggia sul piatto per intero.
- **La lastra è sottile (`PLATE_T` = 3.5) e sale a `RISE_H` = 8 solo dove
  serve**: i sei bossi delle viti, i quattro bracci e le teste d'angolo. Il
  piano d'appoggio del pannello è la faccia a 8; l'anello passa 4.5 mm più in
  basso e non tocca niente.
- I bracci **non si possono assottigliare**. Sono mensole da 49 mm caricate dal
  vento: a 8 mm di altezza stanno a ~8 MPa con 0.9 mm di freccia, a 3 mm
  andrebbero a ~44 MPa (il PETG cede intorno a 50) con 13 mm di freccia. In Z
  la sezione conta al quadrato, quindi è l'altezza a contare, non la larghezza:
  il report stampa entrambi i numeri a ogni run, guardali prima di toccare
  `RISE_H` o `ARM_W`.
- I **bossi** delle viti servono a due cose insieme: ospitare lo svaso (sotto
  la testa restano esattamente `PLATE_T`, perché `CBORE_DEPTH` è derivata come
  `RISE_H - PLATE_T`) e portare la sezione alta fin sopra la vite, così il
  momento dei bracci finisce nella vite invece che nella lastra sottile. **Non
  togliere i bossi lasciando i bracci a innestarsi sulla lastra.**
- Sotto la testa ci sono 3.5 di lastra + 3.2 di coperchio, quindi la vite è
  **M3×12** (impegno 5.3 mm). Se cambi `PLATE_T` o `RISE_H` rifai il conto:
  l'impegno deve restare fra ~4.5 e `INSERT_DEPTH`, oltre la vite tocca il
  fondo del foro e non tira più. `HEAD_GAP` (aria fra testa vite e pannello,
  2.3 mm) è stampata nel report e un test la controlla.
- `check_case_interface()` rilegge `build_case.py` a ogni run e si ferma se
  `LUG_CX/LUG_CY/LUG_R/SCREW_D/INSERT_DEPTH/LID_T` sono cambiati. Le costanti
  sono duplicate apposta invece di importare `build_case`: importarlo lo
  eseguirebbe. **Non trasformarlo in un import.**
- I bracci sono alti 7 mm (tutto `BASE_T`) e larghi 9: il vento carica il
  pannello **normale al suo piano**, quindi flette i bracci in Z, e in Z la
  sezione conta al quadrato. Allargarli serve poco, assottigliare `BASE_T` è
  quello che li rompe. Con un pannello 170 × 170 a 100 km/h sono ~12 N per
  angolo su uno sbalzo di 49.1 mm → ~8 MPa nel materiale, con le fibre nel
  verso giusto.
- Le quattro teste d'angolo sono **lo stesso disegno** in coordinate locali
  (`mapper(sx, sy)`: origine sull'angolo del pannello, u e v verso l'interno),
  e ogni testa è simmetrica rispetto alla propria bisettrice. Lavorare in quel
  frame è ciò che tiene il file corto: si scrive una testa, non quattro.
- **Niente alette di sgancio in punta alle linguette.** C'erano e sporgevano
  oltre lo spigolo del pannello: erano l'unica cosa che usciva dal profilo.
  Non servono: la linguetta sta tutta fuori dal bordo del pannello, quindi la
  si preme direttamente sul fianco per sganciare.
- Il pannello si aggancia premendolo giù: due linguette per angolo, otto in
  tutto, ognuna 24 × 2.4 mm con un dente da 1.5. Deformazione allo scatto
  0.94% (il PETG regge ~3% a breve termine), forza ~8 N per linguetta, ~15 N
  per angolo. Se allunghi il dente o accorci la linguetta ricontrolla il numero
  stampato dal report: sopra il 3% la linguetta non scatta, si spezza.
- Le linguette sono **alte tutto il pezzo e partono dal piano di stampa**:
  flettono **in pianta**, non in Z. È questo che le rende stampabili senza
  supporti in un pezzo unico — una linguetta corta sospesa a metà altezza, come
  quella della vecchia clip, qui sarebbe in aria. Nota che l'altezza entra
  linearmente nella forza di scatto e **non** nella deformazione: sono
  `RAIL_T` e `TONGUE_L` a governare lo strain, l'altezza governa solo quanto
  è dura.
- **Montante e linguetta sono lo stesso prisma** (`rail_*`), che corre dal
  vertice dell'angolo fino alla punta: avevano già la stessa sezione nella
  stessa banda, separarli non separava niente. Il tratto `u < RAIL_L` è
  fasciato dal piano d'appoggio e quindi rigido — è lui il fermo laterale in
  pianta — e oltre `RAIL_L` è la linguetta che flette. `RAIL_L` è la posizione
  della radice: `TONGUE_L` si misura da lì, quindi spostandolo la linguetta
  non cambia lunghezza, cambia solo quanto pezzo la precede.
- **Niente blocco d'angolo.** C'era un quadrato pieno 15 × 15 × 8 per angolo
  che faceva da tramite fra montanti, piano e braccio: era il pezzo più pesante
  della testa e non portava carico che il piano non porti già. Ora i due rami
  del piano si sovrappongono nel quadrato d'angolo e ci si innestano da soli il
  braccio e le due lamelle. La testa d'angolo è passata da 4.5 a 3.3 cm³ e da
  9 prismi a 6, il pezzo intero da 36.1 a 32.2 cm³.
- **La radice della linguetta la fissa il piano d'appoggio**, che perciò
  finisce **netto a `RAIL_L`**: da lì in poi la lamella ha tutti e due i
  fianchi liberi. È il motivo per cui non serve più nessuna aria di manovra
  fra linguetta e piano (prima era `GAP` = 1.2 mm, con un test apposito a
  sondarla, e bastava sbagliare un segno perché l'unione le saldasse insieme).
  Se allunghi il piano oltre `RAIL_L` te la ricompri.
- Il braccio finisce sullo **spigolo rientrante** fra i due rami del piano,
  cioè a `HEAD_IN = PAD_W` dallo spigolo del pannello: è la sola posizione in
  cui tutta la faccia di testa del braccio cade dentro il piano (metà in un
  ramo, metà nell'altro) e l'innesto è di piatto. Non è un numero libero: si
  muove con `PAD_W`, ed è per questo che è scritto così.
- Il pezzo è **unione di prismi convessi estrusi in Z da z = 0**: niente
  sottosquadri, si stampa senza un solo supporto e con adesione piena. L'unica
  sporgenza è il dente (1.5 mm) e la sua rampa a 45°. **Non introdurre feature
  non prismatiche** senza guardare cosa succede in stampa.
- Due degenerazioni del solver EXACT sono già state pagate una volta, **non
  reintrodurle**:
  - la rampa a 45° del dente passava *esattamente* per due spigoli del dente,
    e il taglio tangente lasciava la faccia inclinata sdoppiata. `RAMP_LEAD`
    (0.3 mm) sposta la retta quel tanto che basta; in cima al dente resta
    0.3 mm di sporgenza invece di zero, che non cambia nulla di funzionale.
  - i tre cilindri concentrici della vite (bosso, svaso, foro) avevano lo
    stesso numero di lati, quindi i vertici cadevano sulle stesse generatrici
    radiali: restava un triangolo sciolto sul bordo del foro. Ora sono
    **64 / 56 / 48**. Non uniformarli.
  Provato e scartato: costruire tutto a partire da −0.6 e tagliare a filo z=0
  per evitare le facce complanari sul piano di stampa. Peggiora e basta — il
  taglio finale rompe la mesh in tre gusci.
- `verify_mount.py` controlla per primo che il pezzo sia **un solo guscio
  chiuso**. Non è pignoleria: ogni testa d'angolo è tenuta insieme da
  sovrapposizioni volumetriche di pochi millimetri, e basta un segno sbagliato
  perché una lamella resti staccata — lo slicer stamperebbe un coriandolo e il
  pannello non avrebbe aggancio, senza che nessun test di appartenenza per
  punti se ne accorga.
- `weld()` toglie anche la **geometria sciolta** (spigoli e vertici senza
  facce). Dove due facce si sfiorano tangenti il solver EXACT ne lascia ogni
  tanto uno lungo qualche micron: il guscio resta chiuso, ma è roba che non
  deve finire nell'STL e `verify_mount.py` la conta — a ragione — come spigolo
  non-manifold. Si cancella solo ciò che **non ha facce**, quindi nessuna
  superficie vera può sparire di lì.
- La montatura si smonta con il pannello attaccato; per aprire la scatola si
  tolgono le sei viti e viene via tutto insieme.

## Verifica

Non fidarti del render dall'alto in Workbench, è illeggibile su volumi cavi.
Per controllare la geometria usa test di appartenenza per ray-cast (BVHTree +
conteggio intersezioni) su punti campione: mezzeria della cava, spalle interna
ed esterna, cavità, fori. Un giro di campioni lungo tutto il perimetro della
cava è l'unico modo serio di verificare che l'anello sia continuo. In
alternativa una vista isometrica con il coperchio nascosto.

Entrambe le parti passano da `weld()` prima dell'export: la booleana sdoppia
qualche vertice dove tre superfici si incontrano (sul coperchio, il foro della
vite sulla cucitura del raccordo). La tolleranza è 1e-4 e **non va alzata**: a
1e-3 fonde anche i vertici veri del raccordo lungo la tangenza col lug e apre
dei buchi veri — è quello che faceva il vecchio `cleanup()`, che infatti è
stato tolto insieme agli smussi.
