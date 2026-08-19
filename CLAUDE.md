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
  della base (~312 mm di sviluppo, da giuntare a colla)
- Chiusura con **6 viti M3** su inserti a caldo, in lug esterni **fuori dalla
  linea di tenuta**, raccordati R3 nelle pareti
- **4 alette M4** complanari al pavimento per il fissaggio al dorso del pannello
  solare (o a palo), interasse 76 × 71.8 mm, spigoli esterni smussati 3 × 45° e
  due nervature per aletta affiancate al foro
- **Passacavo Ø5** nella parete +X (opposta all'antenna) a y = 9, z = 15, da
  sigillare a silicone

Ingombro esterno: **117.8 × 58.8 × 32.1 mm**, che diventa **80.8 mm in Y**
contando le alette.

## File

- `build_case.py` — sorgente parametrico, unica fonte di verità. Tutte le quote
  sono costanti in cima al file.
- `case_base.stl`, `case_lid.stl` — output rigenerati a ogni run.
- `verify_case.py` — rigenera e sonda ~150 punti campione (vedi *Verifica*).

## Rigenerare

```
blender --background --factory-startup --python build_case.py
```

Funziona anche da shell (Blender 5.2 installato in `/usr/bin/blender`; esporter
`bpy.ops.wm.stl_export`). In alternativa via MCP (`execute_blender_code`) dentro
una sessione Blender aperta. Lo script cancella la scena, la ricostruisce da
zero ed esporta i due STL in questa cartella. Ignora l'errore
`ModuleNotFoundError: cattrs` all'avvio: è un addon di sistema, non riguarda noi.

## Convenzioni geometriche

- X = asse lungo della cella; Z+ = alto; origine al centro della base.
- La base stampa con l'apertura verso l'alto, il coperchio piatto.

### Tenuta

- Le pareti sono spesse **6.4 mm** perché è la larghezza minima che ospita la
  cava dell'O-ring: 1.3 (spalla interna) + 3.8 (cava) + 1.3 (spalla esterna).
  Non assottigliarle senza rifare questo conto. Il pavimento resta a 2.4.
- Cava **3.8 × 2.2** per corda Ø3: schiacciamento 0.8 mm (27%), riempimento 85%.
  Il coperchio va in **battuta sulle spalle**, che fanno da fine corsa: è la
  battuta a definire la compressione, non il serraggio delle viti.
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
