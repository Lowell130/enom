<template>
  <section class="page-container pt-10 md:pt-14 pb-20">
    <div class="max-w-[820px] flex flex-col gap-10">
      <div class="flex flex-col gap-4">
        <nav aria-label="Percorso" class="text-[13px] text-ink-mute">
          <NuxtLink to="/" class="hover:text-wine-800">Home</NuxtLink> / <span class="text-ink font-semibold">Guida per le cantine</span>
        </nav>
        <span class="eyebrow-sm tracking-[0.14em]">Area produttori</span>
        <h1 class="title-display">Guida per le cantine</h1>
        <p class="text-ink-soft text-[17px] leading-relaxed m-0">
          Come attivare l'accesso e gestire da soli la pagina della cantina su EnotecaMolise: profilo, vini, eventi e
          richieste dei visitatori. È tutto <strong class="text-ink">gratuito</strong> e funziona anche dal telefono.
        </p>
        <p class="text-[13px] text-ink-mute m-0">Tocca un'immagine per vederla più grande.</p>
      </div>

      <!-- indice -->
      <nav aria-labelledby="indice" class="card p-5 sm:p-6 flex flex-col gap-3">
        <h2 id="indice" class="font-serif text-2xl font-bold m-0">In questa guida</h2>
        <ol class="m-0 pl-5 grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1.5 text-[15px]">
          <li v-for="s in sections" :key="s.id"><a :href="`#${s.id}`" class="font-semibold text-wine-800 hover:underline">{{ s.title }}</a></li>
        </ol>
      </nav>

      <!-- 1 -->
      <section id="attivare" class="guide-section">
        <h2>1. Attivare l'accesso</h2>
        <p>
          Se la tua cantina è già sul sito, ti basta scegliere una password. Ci sono due modi per ricevere il link.
        </p>
        <h3>Dall'email di invito</h3>
        <p>
          Se hai ricevuto da noi l'email <em>«… è su EnotecaMolise: attivate il vostro accesso»</em>, premi il pulsante
          <strong>Scegliete la password e accedete</strong>. Il link è personale e vale 14 giorni: se è scaduto,
          rispondi all'email e te ne mandiamo un altro. Se non la trovi, guarda anche nella cartella spam.
        </p>
        <h3>Dalla pagina della cantina</h3>
        <ol>
          <li>Apri la pagina della tua cantina su EnotecaMolise (la trovi in <NuxtLink to="/produttori" class="guide-link">Cantine</NuxtLink>).</li>
          <li>Scorri fino al riquadro <strong>È la tua cantina?</strong> e premi <strong>Richiedi l'accesso</strong>.</li>
          <li>Premi <strong>Invia il link</strong>: lo mandiamo all'email della cantina che compare sulla pagina (per sicurezza la mostriamo solo in parte).</li>
        </ol>
        <GuideFigure src="/immagini-guida/01-rivendica.jpg" alt="Il riquadro «È la tua cantina?» con il pulsante per ricevere il link" :width="1480" :height="568">
          Il riquadro «È la tua cantina?» in fondo alla pagina pubblica.
        </GuideFigure>
        <p class="guide-tip">
          <strong>Quell'email non la usi più?</strong> Premi <em>«Non hai accesso a questa email o non è corretta?»</em> e
          lascia nome, telefono e l'email giusta. Verifichiamo che sei il titolare (di solito con una telefonata) e ti
          mandiamo il link al nuovo indirizzo.
        </p>
        <h3>Scegli la password</h3>
        <ol>
          <li>Scrivi una password di almeno 8 caratteri e ripetila. Va bene anche una frase facile da ricordare.</li>
          <li>Spunta le due caselle: il permesso a pubblicare testi e foto già presenti (potrai cambiarli o toglierli quando vuoi) e l'informativa sulla privacy.</li>
          <li>Premi <strong>Attiva l'accesso ed entra</strong>: sei già dentro l'area riservata.</li>
        </ol>
        <GuideFigure src="/immagini-guida/02-attiva.jpg" alt="La pagina «Attiva il tuo accesso» con password e caselle da spuntare" :width="1016" :height="1376" narrow />
        <p class="guide-tip">
          <strong>La tua cantina non è ancora sul sito?</strong> Iscrivila da
          <NuxtLink to="/login?mode=register" class="guide-link">Registra la tua cantina</NuxtLink>. Dopo un breve controllo approviamo la
          pagina e ti avvisiamo per email; intanto puoi già inserire i vini.
        </p>
      </section>

      <!-- 2 -->
      <section id="accedere" class="guide-section">
        <h2>2. Entrare nell'area riservata</h2>
        <p>
          Le volte successive vai su <strong>enotecamolise.it</strong>, premi <strong>Accedi</strong> in alto a destra e
          scrivi email e password. Se hai dimenticato la password, premi <strong>Password dimenticata?</strong>: ti
          mandiamo un link per sceglierne una nuova.
        </p>
        <GuideFigure src="/immagini-guida/03-accesso.jpg" alt="La pagina di accesso con email e password" :width="1096" :height="966" narrow />
        <p>
          A sinistra trovi il menu: <strong>Panoramica</strong>, <strong>Vini</strong>, <strong>Eventi</strong>,
          <strong>Richieste</strong> e <strong>Profilo cantina</strong>. In fondo ci sono <strong>Account e password</strong>,
          <strong>Torna al sito</strong> ed <strong>Esci</strong>. Dal telefono il menu si apre con il pulsante in alto a destra.
        </p>
        <div class="grid grid-cols-1 sm:grid-cols-[minmax(0,1fr)_220px] gap-4 items-start">
          <GuideFigure src="/immagini-guida/04-panoramica.jpg" alt="La Panoramica dell'area riservata con il menu a sinistra" :width="1800" :height="527">
            La Panoramica: richieste ricevute, vini più richiesti e cosa manca alle schede.
          </GuideFigure>
          <GuideFigure src="/immagini-guida/21-telefono-menu.jpg" alt="Il menu dell'area riservata aperto sul telefono" :width="780" :height="1000">
            Il menu sul telefono.
          </GuideFigure>
        </div>
      </section>

      <!-- 3 -->
      <section id="profilo" class="guide-section">
        <h2>3. Completare il profilo della cantina</h2>
        <p>
          Apri <strong>Profilo cantina</strong>: è quello che i visitatori vedono nella pagina della cantina. Alla fine
          ricordati di premere <strong>Salva il profilo</strong>.
        </p>
        <h3>Nome e indirizzo</h3>
        <p>Controlla nome, comune, provincia, indirizzo e CAP.</p>
        <GuideFigure src="/immagini-guida/05-profilo-dati.jpg" alt="Nome, comune, provincia, indirizzo e CAP della cantina" :width="1712" :height="656" />
        <h3>Posizione sulla mappa</h3>
        <p>
          Il segnaposto indica dove si trova la cantina: serve per la mappa del sito e per le indicazioni stradali.
          Cercala con l'indirizzo, oppure trascina il segnaposto nel punto giusto (con <strong>Satellite</strong> vedi
          gli edifici). Se hai un link di Google Maps o le coordinate, incollali in
          <strong>Hai le coordinate o un link di Google Maps?</strong>.
        </p>
        <GuideFigure src="/immagini-guida/06-profilo-mappa.jpg" alt="La mappa con il segnaposto della cantina e la ricerca dell'indirizzo" :width="1712" :height="1104">
          Le cantine in campagna spesso sono lontane dal centro del paese: controlla che il segnaposto sia proprio sulla cantina.
        </GuideFigure>
        <h3>Contatti</h3>
        <ul>
          <li><strong>Email per le richieste dei clienti</strong>: qui ti avvisiamo quando un visitatore ti scrive.</li>
          <li><strong>WhatsApp</strong>: il numero di cellulare collegato a WhatsApp, senza +39 (lo aggiungiamo noi). Sulla pagina comparirà il pulsante WhatsApp: con <strong>Prova il link</strong> controlli che si apra la chat giusta.</li>
          <li><strong>Telefono</strong> e <strong>Sito web</strong>, se li hai.</li>
        </ul>
        <GuideFigure src="/immagini-guida/07-profilo-contatti.jpg" alt="I contatti della cantina: email, telefono, WhatsApp e sito web" :width="1712" :height="704" />
        <h3>Logo, foto di copertina e storia</h3>
        <ul>
          <li><strong>Logo</strong>: meglio quadrato.</li>
          <li><strong>Foto di copertina</strong>: una foto orizzontale, per esempio i vigneti o la cantina.</li>
          <li><strong>La storia della cantina</strong>: chi siete, dove sono le vigne, cosa vi rende diversi. Bastano poche righe (almeno 150 caratteri).</li>
        </ul>
        <p>Le foto si caricano anche dal telefono; quelle molto grandi le riduciamo noi.</p>
        <GuideFigure src="/immagini-guida/08-profilo-immagini.jpg" alt="Logo, foto di copertina, storia della cantina e pulsante Salva il profilo" :width="1712" :height="1154" />
      </section>

      <!-- 4 -->
      <section id="vini" class="guide-section">
        <h2>4. Aggiungere e modificare i vini</h2>
        <p>
          In <strong>Vini</strong> trovi tutti i tuoi vini. Per ognuno puoi:
        </p>
        <ul>
          <li><strong>Vedi scheda</strong>: come la vedono i visitatori;</li>
          <li><strong>Modifica</strong>: cambi testi, foto e dati;</li>
          <li><strong>Clona 1-Click</strong>: crea una copia, comoda per una nuova annata (la copia nasce come bozza);</li>
          <li><strong>Elimina</strong>: toglie il vino dal sito.</li>
        </ul>
        <p>Accanto a ogni vino vedi se è <strong>Pubblicato</strong> (visibile a tutti) o in <strong>Bozza</strong> (lo vedi solo tu).</p>
        <GuideFigure src="/immagini-guida/09-vini-elenco.jpg" alt="L'elenco dei vini con i pulsanti Vedi scheda, Clona, Modifica ed Elimina" :width="1800" :height="930" />

        <h3>Un nuovo vino</h3>
        <p>Premi <strong>Nuovo vino</strong> e compila la scheda. I campi con l'asterisco sono obbligatori.</p>
        <ol>
          <li><strong>Dettagli</strong>: nome, tipologia, denominazione, gradazione, temperatura di servizio e prezzo indicativo. Con i pulsanti in alto scegli se indicare annata e menzione Riserva; spunta <strong>Vino biologico</strong> se è certificato.</li>
        </ol>
        <GuideFigure src="/immagini-guida/10-vino-dettagli.jpg" alt="I dettagli generali del vino: nome, tipologia, denominazione, annata e Riserva" :width="1800" :height="970" />
        <ol start="2">
          <li><strong>Vitigni e descrizione</strong>: tocca un vitigno per aggiungerlo e scegli la percentuale. Poi racconta il vino: vinificazione, affinamento, carattere.</li>
        </ol>
        <GuideFigure src="/immagini-guida/12-vino-vitigni.jpg" alt="La scelta dei vitigni con le percentuali e la descrizione del vino" :width="1800" :height="991" />
        <ol start="3">
          <li><strong>Note di degustazione e abbinamenti</strong>: scegli gli abbinamenti dall'elenco o scrivine di tuoi.</li>
          <li><strong>Scheda tecnica</strong>: con <strong>Aggiungi caratteristica</strong> aggiungi altri dati, per esempio vinificazione, affinamento, allergeni o altitudine dei vigneti.</li>
        </ol>
        <GuideFigure src="/immagini-guida/11-vino-scheda-extra.jpg" alt="Il riquadro per aggiungere caratteristiche alla scheda tecnica" :width="1800" :height="412" />
        <ol start="5">
          <li><strong>Foto e PDF</strong>: carica la foto della bottiglia (la prima è quella principale) e, se vuoi, il PDF della scheda tecnica, che i visitatori potranno scaricare.</li>
          <li>Scegli <strong>Pubblicato</strong> o <strong>Bozza</strong> e premi <strong>Salva nuovo vino</strong>.</li>
        </ol>
        <GuideFigure src="/immagini-guida/13-vino-foto.jpg" alt="Foto della bottiglia, PDF della scheda tecnica e stato di pubblicazione" :width="1800" :height="887" />
        <p class="guide-tip">
          <strong>Cosa manca?</strong> Nella <strong>Panoramica</strong> la voce <em>Completezza delle schede</em> indica
          cosa manca a ogni vino: le schede complete si trovano meglio nella ricerca e nei filtri del catalogo.
        </p>

        <h3>Hai già le schede tecniche in PDF?</h3>
        <p>
          Premi <strong>Importa schede (AI)</strong> e carica i PDF o le foto delle schede (anche più di una alla volta):
          il sistema compila le schede dei vini al posto tuo. Prima di salvarle le puoi controllare e correggere una per una.
        </p>
        <GuideFigure src="/immagini-guida/14-vino-ai.jpg" alt="La finestra per importare le schede dei vini da PDF o immagini" :width="1800" :height="814" />
      </section>

      <!-- 5 -->
      <section id="eventi" class="guide-section">
        <h2>5. Pubblicare un evento</h2>
        <p>
          Degustazioni, visite in cantina, cene, vendemmie: gli eventi compaiono nel calendario del sito e nella pagina
          della cantina. Li gestisci da <strong>Eventi</strong>, dove puoi vedere, modificare, duplicare, annullare o eliminare quelli già creati.
        </p>
        <GuideFigure src="/immagini-guida/15-eventi-elenco.jpg" alt="L'elenco degli eventi della cantina" :width="1800" :height="632" />
        <p>Premi <strong>Nuovo evento</strong>:</p>
        <ol>
          <li><strong>L'evento</strong>: titolo, tipo, descrizione e, se vuoi, una foto orizzontale. Nella descrizione le righe che iniziano con «- » diventano un elenco.</li>
        </ol>
        <GuideFigure src="/immagini-guida/16-evento-dati.jpg" alt="Titolo, tipo, descrizione e immagine dell'evento" :width="1712" :height="1032" />
        <ol start="2">
          <li><strong>Quando</strong>: giorno e orari. Se l'evento si ripete (per esempio ogni sabato di ottobre) aggiungi altre date con <strong>Aggiungi un'altra data</strong>.</li>
          <li><strong>Dove</strong>: <em>Presso la cantina</em> usa l'indirizzo del profilo; altrimenti scegli <em>In un altro luogo</em>.</li>
        </ol>
        <GuideFigure src="/immagini-guida/17-evento-quando-dove.jpg" alt="Data, orari e luogo dell'evento" :width="1712" :height="948" />
        <ol start="4">
          <li><strong>Vini in degustazione</strong>: tocca i vini che farai assaggiare.</li>
          <li><strong>Costo</strong> e <strong>come si partecipa</strong>: con <em>Richiesta dal sito</em> i visitatori compilano un modulo e tu ricevi un'email; puoi anche indicare un sito di prenotazione o l'ingresso libero.</li>
          <li>Premi <strong>Pubblica l'evento</strong>, oppure <strong>Salva come bozza</strong> per finirlo dopo.</li>
        </ol>
        <GuideFigure src="/immagini-guida/18-evento-costo.jpg" alt="Vini in degustazione, costo, modalità di partecipazione e pulsanti per pubblicare" :width="1712" :height="1370" />
        <p class="guide-tip">
          <strong>Devi annullare?</strong> Usa <strong>Annulla</strong>, non Elimina: avvisiamo noi via email chi aveva chiesto di
          partecipare, con il messaggio che scrivi tu.
        </p>
      </section>

      <!-- 6 -->
      <section id="richieste" class="guide-section">
        <h2>6. Rispondere alle richieste dei visitatori</h2>
        <p>
          Quando un visitatore ti scrive dalla pagina della cantina, di un vino o di un evento, ricevi un'email
          all'indirizzo indicato nel profilo e trovi il messaggio in <strong>Richieste</strong>. Premi
          <strong>Rispondi via Email</strong> per rispondere dalla tua posta. Le richieste le vedi solo tu.
        </p>
        <GuideFigure src="/immagini-guida/19-richieste.jpg" alt="Una richiesta di un visitatore con il pulsante Rispondi via Email" :width="1528" :height="884" />
        <p>Se hai inserito il numero WhatsApp, i visitatori possono anche scriverti direttamente lì.</p>
      </section>

      <!-- 7 -->
      <section id="account" class="guide-section">
        <h2>7. Password ed email di accesso</h2>
        <p>
          In <strong>Account e password</strong> puoi cambiare la password e l'email con cui entri. Usa una casella che
          leggi davvero: lì arrivano il recupero della password e gli avvisi.
        </p>
        <GuideFigure src="/immagini-guida/20-account.jpg" alt="La pagina Account e password" :width="1244" :height="1102" narrow />
        <p>
          Se vuoi togliere la cantina dal sito, in fondo al <strong>Profilo cantina</strong> trovi
          <strong>Chiedi la cancellazione</strong>.
        </p>
      </section>

      <!-- 8 -->
      <section id="domande" class="guide-section">
        <h2>8. Domande frequenti</h2>
        <dl class="flex flex-col gap-4 m-0">
          <div v-for="f in faq" :key="f.q" class="card p-4 sm:p-5">
            <dt class="font-bold text-ink">{{ f.q }}</dt>
            <dd class="m-0 mt-1 text-ink-soft leading-relaxed">{{ f.a }}</dd>
          </div>
        </dl>
      </section>

      <div class="card p-5 sm:p-6 flex flex-col sm:flex-row sm:items-center gap-4 justify-between">
        <div class="flex flex-col gap-1">
          <h2 class="font-serif text-2xl font-bold m-0">Serve una mano?</h2>
          <p class="m-0 text-ink-soft text-sm">Scrivici: ti aiutiamo volentieri, anche a completare la pagina.</p>
        </div>
        <div class="flex flex-wrap gap-2">
          <NuxtLink to="/contatti" class="btn-primary btn-sm h-11">Scrivici</NuxtLink>
          <NuxtLink to="/login" class="btn-ghost btn-sm h-11">Accedi</NuxtLink>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
useSeoMeta({
  title: 'Guida per le cantine - EnotecaMolise',
  description: 'Come attivare l\'accesso e gestire la pagina della cantina su EnotecaMolise: profilo, vini, eventi e richieste.',
  robots: 'noindex, nofollow'
})

const sections = [
  { id: 'attivare', title: 'Attivare l\'accesso' },
  { id: 'accedere', title: 'Entrare nell\'area riservata' },
  { id: 'profilo', title: 'Completare il profilo' },
  { id: 'vini', title: 'Aggiungere i vini' },
  { id: 'eventi', title: 'Pubblicare un evento' },
  { id: 'richieste', title: 'Rispondere alle richieste' },
  { id: 'account', title: 'Password ed email' },
  { id: 'domande', title: 'Domande frequenti' }
]

const faq = [
  { q: 'Quanto costa?', a: 'Niente. EnotecaMolise è un portale gratuito e senza scopo di lucro: nessun abbonamento e nessuna commissione sulle vendite.' },
  { q: 'Non mi arriva l\'email con il link.', a: 'Controlla nella cartella spam o promozioni. Il link di attivazione vale 14 giorni: se è scaduto, richiedine un altro dalla pagina della cantina o scrivici.' },
  { q: 'Posso fare tutto dal telefono?', a: 'Sì: l\'area riservata funziona anche dal telefono, comprese le foto scattate al momento.' },
  { q: 'Chi vede le richieste dei visitatori?', a: 'Solo tu. Arrivano alla tua email e nell\'area riservata, senza intermediari: prezzi, vendite e prenotazioni li gestisci direttamente tu.' },
  { q: 'Posso togliere o cambiare i testi e le foto già presenti?', a: 'Sì, in qualsiasi momento: dal Profilo cantina per la pagina della cantina, da Vini per le schede dei vini.' },
  { q: 'Ho sbagliato e voglio annullare una modifica.', a: 'Correggi il campo e salva di nuovo. Se non riesci, scrivici dalla pagina Contatti e sistemiamo insieme.' }
]
</script>

<style scoped>
.guide-section {
  display: flex;
  flex-direction: column;
  gap: 14px;
  scroll-margin-top: 90px;
}
.guide-section h2 {
  font-family: 'Cormorant Garamond', Georgia, serif;
  font-size: 34px;
  font-weight: 700;
  line-height: 1.1;
  margin: 0;
  padding-top: 8px;
  border-top: 1px solid rgb(0 0 0 / 0.08);
}
.guide-section h3 {
  font-size: 18px;
  font-weight: 700;
  margin: 10px 0 0;
}
.guide-section p,
.guide-section li {
  font-size: 16px;
  line-height: 1.65;
}
.guide-section p {
  margin: 0;
}
.guide-section ol,
.guide-section ul {
  margin: 0;
  padding-left: 1.3rem;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.guide-section ol { list-style: decimal; }
.guide-section ul { list-style: disc; }
.guide-link {
  color: #6B1D2F;
  font-weight: 600;
  text-decoration: underline;
  text-underline-offset: 2px;
}
.guide-tip {
  padding: 14px 16px;
  border-radius: 12px;
  background: #FBF5E8;
  border: 1px solid #E8D9B8;
  color: #5A4524;
}
</style>
