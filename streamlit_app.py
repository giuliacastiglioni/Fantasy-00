import streamlit as st
import streamlit.components.v1 as components
import random
import json
import io
import textwrap
import requests
import plotly.graph_objects as go
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="Fantasy Quiz", page_icon="🔮", layout="centered")

# ============================================================
# DATI — CASE DI HOGWARTS
# (fondatore, animale, elemento, colori, fantasma, sala comune,
#  valori, alunni celebri: dettagli fattuali dell'universo di
#  Harry Potter, non testo protetto dei libri)
# ============================================================
HOUSES = {
    "Grifondoro": {
        "gradiente": "linear-gradient(135deg, #740001 0%, #ae0001 45%, #d3a625 100%)",
        "rgb_top": (116, 0, 1),
        "rgb_bottom": (211, 166, 37),
        "emoji": "🦁",
        "descrizione": "Il coraggio scorre nelle tue vene. Non sei senza paura — nessun vero grifondoro lo è — ma agisci anche quando hai paura, ed è proprio questo a definirti.",
        "dettagli": [
            ("Fondatore", "Godric Grifondoro"),
            ("Animale", "Leone"),
            ("Elemento", "Fuoco"),
            ("Colori", "Rosso porpora e oro"),
            ("Fantasma", "Nick Quasi Senza Testa"),
            ("Sala comune", "Settimo piano, dietro la Signora Grassa"),
            ("Valori", "Coraggio, audacia, determinazione"),
            ("Alunni celebri", "Harry Potter, Hermione Granger, Albus Silente"),
        ],
    },
    "Serpeverde": {
        "gradiente": "linear-gradient(135deg, #0d1f13 0%, #1a472a 50%, #3c6e47 100%)",
        "rgb_top": (13, 31, 19),
        "rgb_bottom": (60, 110, 71),
        "emoji": "🐍",
        "descrizione": "Sai esattamente cosa vuoi e come ottenerlo. La tua mente strategica e la tua ambizione ti spingono sempre un passo più in là degli altri.",
        "dettagli": [
            ("Fondatore", "Salazar Serpeverde"),
            ("Animale", "Serpente"),
            ("Elemento", "Acqua"),
            ("Colori", "Verde smeraldo e argento"),
            ("Fantasma", "Il Barone Sanguinario"),
            ("Sala comune", "Sotterranei, con vista sul lago"),
            ("Valori", "Ambizione, astuzia, leadership"),
            ("Alunni celebri", "Severus Piton, Tom Riddle, Horace Lumacorno"),
        ],
    },
    "Corvonero": {
        "gradiente": "linear-gradient(135deg, #060d24 0%, #0e1a40 50%, #2b4a8c 100%)",
        "rgb_top": (6, 13, 36),
        "rgb_bottom": (43, 74, 140),
        "emoji": "🦅",
        "descrizione": "La tua mente non si ferma mai. Curiosità e ingegno ti guidano, e per te il sapere non è un dovere ma una delle più grandi gioie della vita.",
        "dettagli": [
            ("Fondatore", "Priscilla Corvonero"),
            ("Animale", "Aquila"),
            ("Elemento", "Aria"),
            ("Colori", "Blu notte e bronzo"),
            ("Fantasma", "La Signora Grigia"),
            ("Sala comune", "Una torre, l'accesso è un enigma"),
            ("Valori", "Intelligenza, creatività, curiosità"),
            ("Alunni celebri", "Luna Lovegood, Gilderoy Allock, Filius Vitious"),
        ],
    },
    "Tassorosso": {
        "gradiente": "linear-gradient(135deg, #4a3b00 0%, #b89b1a 50%, #ffdb00 100%)",
        "rgb_top": (74, 59, 0),
        "rgb_bottom": (255, 219, 0),
        "emoji": "🦡",
        "descrizione": "Non cerchi i riflettori, ma senza di te nessun gruppo reggerebbe. Leale fino in fondo, lavori sodo e tratti tutti con la stessa gentilezza onesta.",
        "dettagli": [
            ("Fondatore", "Helga Tassorosso"),
            ("Animale", "Tasso"),
            ("Elemento", "Terra"),
            ("Colori", "Giallo canarino e nero"),
            ("Fantasma", "Il Frate Grasso"),
            ("Sala comune", "Seminterrato vicino alle cucine"),
            ("Valori", "Lealtà, lavoro duro, pazienza"),
            ("Alunni celebri", "Cedric Diggory, Newton Scamander, Pomona Sprite"),
        ],
    },
}

QUESTIONS_HP = [
    {
        "domanda": "Sei nella Foresta Proibita di notte e senti un ramo spezzarsi alle tue spalle. Cosa fai davvero, d'istinto?",
        "opzioni": [
            ("Mi giro di scatto, bacchetta pronta: se c'è un pericolo, meglio affrontarlo subito", {"Grifondoro": 1}),
            ("Resto immobile e calcolo in silenzio quale creatura potrebbe essere, in base ai rumori", {"Corvonero": 1}),
            ("Valuto se conviene fuggire o se posso trarre vantaggio dalla situazione", {"Serpeverde": 1}),
            ("Cerco i miei compagni per assicurarmi che stiano tutti bene prima di muovermi", {"Tassorosso": 1}),
        ],
    },
    {
        "domanda": "Il Cappello Parlante ti fa notare che potresti avere successo in più di una casa. Come rispondi?",
        "opzioni": [
            ("Chiedo di essere messo dove potrò dimostrare più coraggio", {"Grifondoro": 1}),
            ("Chiedo dove potrò imparare di più e sviluppare le mie idee", {"Corvonero": 1}),
            ("Chiedo dove potrò costruire il percorso più solido per il mio futuro", {"Serpeverde": 1}),
            ("Chiedo dove troverò le amicizie più sincere e durature", {"Tassorosso": 1}),
        ],
    },
    {
        "domanda": "Devi scegliere una materia opzionale al terzo anno. Quale scegli?",
        "opzioni": [
            ("Cura delle Creature Magiche: mi piace il rischio e il contatto diretto", {"Grifondoro": 1, "Tassorosso": 0.5}),
            ("Aritmanzia: adoro i sistemi complessi e la logica", {"Corvonero": 1}),
            ("Divinazione: potrebbe darmi un vantaggio che altri non hanno", {"Serpeverde": 0.5, "Corvonero": 0.5}),
            ("Cura delle Creature Magiche, ma per il gusto di prendermi cura di loro", {"Tassorosso": 1}),
        ],
    },
    {
        "domanda": "Un compagno di scuola viene deriso davanti a tutti. Cosa fai?",
        "opzioni": [
            ("Intervengo subito e apertamente, costi quel che costi", {"Grifondoro": 1}),
            ("Aspetto il momento giusto per far notare, con argomenti solidi, quanto sia stato ingiusto", {"Corvonero": 1}),
            ("Valuto la situazione: intervenire ora mi conviene o mi espone inutilmente?", {"Serpeverde": 1}),
            ("Vado subito a stargli vicino dopo, in privato, per fargli sentire che non è solo", {"Tassorosso": 1}),
        ],
    },
    {
        "domanda": "Qual è, onestamente, la tua paura più profonda?",
        "opzioni": [
            ("Essere ricordato come un codardo", {"Grifondoro": 1}),
            ("Restare intrappolato nella mediocrità, senza mai realizzare il mio potenziale", {"Serpeverde": 1}),
            ("Scoprire di aver sbagliato qualcosa per ignoranza, non per sfortuna", {"Corvonero": 1}),
            ("Deludere o perdere le persone di cui mi fido di più", {"Tassorosso": 1}),
        ],
    },
    {
        "domanda": "Hai trovato per caso un oggetto magico molto potente e di dubbia provenienza. Cosa fai?",
        "opzioni": [
            ("Lo uso subito se serve a proteggere qualcuno, senza pensarci troppo", {"Grifondoro": 1}),
            ("Lo studio a fondo prima di decidere qualsiasi cosa: capire viene prima di agire", {"Corvonero": 1}),
            ("Valuto come potrebbe tornarmi utile, con la dovuta cautela", {"Serpeverde": 1}),
            ("Lo consegno a un professore di cui mi fido: non è giusto tenerlo per me", {"Tassorosso": 1}),
        ],
    },
    {
        "domanda": "Come preferisci lavorare a un progetto di gruppo per una materia difficile?",
        "opzioni": [
            ("Mi propongo per la parte più rischiosa o impegnativa", {"Grifondoro": 1}),
            ("Organizzo un piano dettagliato e mi assicuro che tutto proceda come previsto", {"Serpeverde": 1}),
            ("Porto le idee più originali e le soluzioni meno ovvie", {"Corvonero": 1}),
            ("Mi accerto che il lavoro sia distribuito in modo equo e che nessuno resti indietro", {"Tassorosso": 1}),
        ],
    },
    {
        "domanda": "Sei di fronte a uno specchio che mostra il tuo desiderio più profondo. Cosa vedi, con più probabilità?",
        "opzioni": [
            ("Un momento in cui salvo qualcuno a cui tengo", {"Grifondoro": 1}),
            ("Un futuro in cui sono rispettato e ho raggiunto tutto ciò che volevo", {"Serpeverde": 1}),
            ("La risposta a una domanda che mi tormenta da sempre", {"Corvonero": 1}),
            ("La mia famiglia e i miei amici, tutti riuniti e felici", {"Tassorosso": 1}),
        ],
    },
    {
        "domanda": "Un professore ti offre due strade per un esame: una sicura ma banale, una rischiosa ma memorabile. Cosa scegli?",
        "opzioni": [
            ("Quella rischiosa: se va male, almeno ci avrò provato fino in fondo", {"Grifondoro": 1}),
            ("Quella rischiosa, ma solo dopo aver calcolato con precisione le probabilità di riuscita", {"Corvonero": 0.5, "Serpeverde": 0.5}),
            ("Quella che mi porta il risultato migliore sul lungo periodo, qualunque essa sia", {"Serpeverde": 1}),
            ("Quella sicura: preferisco un buon risultato certo a un azzardo inutile", {"Tassorosso": 1}),
        ],
    },
    {
        "domanda": "Cosa ti infastidisce di più in una persona con cui lavori?",
        "opzioni": [
            ("L'indecisione: chi ha paura di agire mi manda in crisi", {"Grifondoro": 1}),
            ("La disonestà o la slealtà verso il gruppo", {"Tassorosso": 1}),
            ("La superficialità: chi non approfondisce mai nulla", {"Corvonero": 1}),
            ("L'incompetenza: chi non è all'altezza dei propri obiettivi", {"Serpeverde": 1}),
        ],
    },
    {
        "domanda": "Se potessi ricevere un solo dono da un professore di Hogwarts, quale sceglieresti?",
        "opzioni": [
            ("Il coraggio di non vacillare mai davanti al pericolo", {"Grifondoro": 1}),
            ("Una biblioteca infinita con ogni sapere del mondo magico", {"Corvonero": 1}),
            ("Il potere di raggiungere qualsiasi obiettivo mi prefigga", {"Serpeverde": 1}),
            ("Amici fedeli per tutta la vita", {"Tassorosso": 1}),
        ],
    },
    {
        "domanda": "È l'ultima notte prima di un evento importante e rischioso (un torneo, una missione, un esame decisivo). Come la passi?",
        "opzioni": [
            ("Non riesco a stare fermo: voglio solo che arrivi il momento di agire", {"Grifondoro": 1}),
            ("Ripasso ogni singolo dettaglio, ancora e ancora, finché non sono certo di essere pronto", {"Corvonero": 1}),
            ("Rifinisco la mia strategia, pensando a ogni possibile imprevisto e a come sfruttarlo", {"Serpeverde": 1}),
            ("Sto con le persone a cui voglio bene: mi danno la forza per il giorno dopo", {"Tassorosso": 1}),
        ],
    },
]


# ============================================================
# DATI — GENITORI DIVINI (Percy Jackson / Campo Mezzosangue)
# (dominio, animale simbolo, colori, cabina, figli noti, valori:
#  dettagli fattuali dell'universo/mitologia, non testo protetto)
# ============================================================
GODS = {
    "Zeus": {
        "gradiente": "linear-gradient(135deg, #1b2f4d 0%, #3a5f8a 50%, #a9c9e8 100%)",
        "rgb_top": (27, 47, 77),
        "rgb_bottom": (169, 201, 232),
        "emoji": "⚡",
        "descrizione": "Nato per guidare. Hai un senso innato dell'autorità e della giustizia, anche se il tuo orgoglio a volte ti gioca brutti scherzi.",
        "dettagli": [
            ("Dominio", "Cielo e fulmini"),
            ("Animale simbolo", "Aquila"),
            ("Colori", "Blu elettrico e argento"),
            ("Cabina", "Cabina 1"),
            ("Figli noti", "Jason Grace, Thalia Grace"),
            ("Valori", "Leadership, autorità, orgoglio"),
        ],
    },
    "Poseidone": {
        "gradiente": "linear-gradient(135deg, #04303a 0%, #0f6e7d 50%, #2ea3b8 100%)",
        "rgb_top": (4, 48, 58),
        "rgb_bottom": (46, 163, 184),
        "emoji": "🌊",
        "descrizione": "Il tuo cuore è imprevedibile come il mare: calmo in superficie, capace di tempeste furiose quando chi ami è minacciato.",
        "dettagli": [
            ("Dominio", "Mare e terremoti"),
            ("Animale simbolo", "Cavallo"),
            ("Colori", "Verde acqua e blu oceano"),
            ("Cabina", "Cabina 3"),
            ("Figli noti", "Percy Jackson, Tyson"),
            ("Valori", "Lealtà, istinto, protezione"),
        ],
    },
    "Ade": {
        "gradiente": "linear-gradient(135deg, #0a0a0a 0%, #3b2f10 55%, #5a4a14 100%)",
        "rgb_top": (10, 10, 10),
        "rgb_bottom": (90, 74, 20),
        "emoji": "💀",
        "descrizione": "Preferisci l'ombra ai riflettori. Sotto la tua apparente freddezza si nasconde un senso del dovere fortissimo.",
        "dettagli": [
            ("Dominio", "Regno dei morti e ricchezze sotterranee"),
            ("Animale simbolo", "Cane infernale"),
            ("Colori", "Nero e oro cupo"),
            ("Cabina", "Nessuna cabina ufficiale, per antico patto"),
            ("Figli noti", "Nico di Angelo, Hazel Levesque"),
            ("Valori", "Senso del dovere, solitudine, rigore"),
        ],
    },
    "Atena": {
        "gradiente": "linear-gradient(135deg, #23232b 0%, #55555f 50%, #8c7850 100%)",
        "rgb_top": (35, 35, 43),
        "rgb_bottom": (140, 120, 80),
        "emoji": "🦉",
        "descrizione": "La tua mente è la tua arma più potente. Pianifichi, osservi, e raramente qualcuno riesce a sorprenderti.",
        "dettagli": [
            ("Dominio", "Saggezza e strategia in battaglia"),
            ("Animale simbolo", "Civetta"),
            ("Colori", "Grigio e bronzo"),
            ("Cabina", "Cabina 6"),
            ("Figli noti", "Annabeth Chase, Malcolm Pace"),
            ("Valori", "Intelligenza, pianificazione, orgoglio"),
        ],
    },
    "Ares": {
        "gradiente": "linear-gradient(135deg, #280404 0%, #6e0f0f 50%, #961414 100%)",
        "rgb_top": (40, 4, 4),
        "rgb_bottom": (150, 20, 20),
        "emoji": "🗡️",
        "descrizione": "Vivi per l'azione e la sfida. Il tuo coraggio in battaglia è innegabile, anche se a volte agisci prima di pensare.",
        "dettagli": [
            ("Dominio", "Guerra e violenza"),
            ("Animale simbolo", "Cinghiale"),
            ("Colori", "Rosso sangue e nero"),
            ("Cabina", "Cabina 5"),
            ("Figli noti", "Clarisse La Rue"),
            ("Valori", "Forza, coraggio, lealtà di gruppo"),
        ],
    },
    "Apollo": {
        "gradiente": "linear-gradient(135deg, #785a0a 0%, #c99b1f 50%, #ffddaa 100%)",
        "rgb_top": (120, 90, 10),
        "rgb_bottom": (255, 221, 170),
        "emoji": "🎵",
        "descrizione": "Porti luce ovunque tu vada, con creatività, ottimismo e una gran voglia di prenderti cura degli altri.",
        "dettagli": [
            ("Dominio", "Sole, musica, profezia e guarigione"),
            ("Animale simbolo", "Cigno"),
            ("Colori", "Oro e bianco"),
            ("Cabina", "Cabina 7"),
            ("Figli noti", "Will Solace, Austin Lake"),
            ("Valori", "Creatività, ottimismo, empatia"),
        ],
    },
    "Afrodite": {
        "gradiente": "linear-gradient(135deg, #5a1e32 0%, #a8496b 50%, #e696b4 100%)",
        "rgb_top": (90, 30, 50),
        "rgb_bottom": (230, 150, 180),
        "emoji": "💗",
        "descrizione": "Il tuo potere è il cuore. Senti tutto intensamente e questo ti rende più coraggioso di quanto pensi.",
        "dettagli": [
            ("Dominio", "Amore e bellezza"),
            ("Animale simbolo", "Colomba"),
            ("Colori", "Rosa cipria e oro rosa"),
            ("Cabina", "Cabina 10"),
            ("Figli noti", "Piper McLean, Silena Beauregard"),
            ("Valori", "Empatia, fascino, autenticità"),
        ],
    },
    "Ermes": {
        "gradiente": "linear-gradient(135deg, #3c2d0a 0%, #7a5c1a 50%, #c89a3c 100%)",
        "rgb_top": (60, 45, 10),
        "rgb_bottom": (200, 154, 60),
        "emoji": "🪽",
        "descrizione": "Sei fatto per il movimento e l'imprevisto. Ingegno, umorismo e un pizzico di sana ribellione ti definiscono.",
        "dettagli": [
            ("Dominio", "Viaggi, commercio e messaggeri"),
            ("Animale simbolo", "Falco"),
            ("Colori", "Giallo senape e marrone cuoio"),
            ("Cabina", "Cabina 11"),
            ("Figli noti", "Luke Castellan, Travis e Connor Stoll"),
            ("Valori", "Ingegno, adattabilità, libertà"),
        ],
    },
}

QUESTIONS_PJ = [
    {
        "domanda": "Sei a capo di una missione importante e il gruppo aspetta il tuo ordine. Cosa fai?",
        "opzioni": [
            ("Do l'ordine con fermezza: la squadra ha bisogno di una guida chiara", {"Zeus": 1}),
            ("Ascolto tutti, ma quando decido nessuno mi fa cambiare idea", {"Poseidone": 1}),
            ("Preferisco restare in disparte e agire solo quando è davvero necessario", {"Ade": 1}),
            ("Valuto ogni scenario possibile prima di dare qualsiasi indicazione", {"Atena": 1}),
        ],
    },
    {
        "domanda": "Come preferisci passare un pomeriggio libero al campo?",
        "opzioni": [
            ("In arena, ad allenarmi con la spada finché non sono esausto", {"Ares": 1}),
            ("Componendo musica o cantando con gli amici", {"Apollo": 1}),
            ("Passando del tempo di qualità con le persone a cui tengo", {"Afrodite": 1}),
            ("Esplorando in giro, magari architettando qualche scherzo innocuo", {"Ermes": 1}),
        ],
    },
    {
        "domanda": "Il gruppo è diviso su come affrontare un pericolo imminente. Tu cosa fai?",
        "opzioni": [
            ("Prendo io la decisione finale: qualcuno deve farlo", {"Zeus": 1}),
            ("Seguo il mio istinto, anche se va contro il parere della maggioranza", {"Poseidone": 1}),
            ("Propongo di affrontarlo di petto, con la forza", {"Ares": 1}),
            ("Cerco di calmare gli animi e trovare un equilibrio", {"Apollo": 1}),
        ],
    },
    {
        "domanda": "Cosa ti fa sentire davvero te stesso?",
        "opzioni": [
            ("Un momento di silenzio e solitudine, lontano dal rumore", {"Ade": 1}),
            ("Risolvere un problema complesso meglio di chiunque altro", {"Atena": 1}),
            ("Una connessione autentica e profonda con qualcuno", {"Afrodite": 1}),
            ("La libertà di andare dove voglio, senza vincoli", {"Ermes": 1}),
        ],
    },
    {
        "domanda": "Qual è, onestamente, il tuo punto debole?",
        "opzioni": [
            ("L'orgoglio: faccio fatica ad ammettere di aver sbagliato", {"Zeus": 1}),
            ("La tendenza a isolarmi quando le cose si complicano", {"Ade": 1}),
            ("Il temperamento: agisco prima di pensare alle conseguenze", {"Ares": 1}),
            ("Mi lascio guidare troppo dalle emozioni, a volte", {"Afrodite": 1}),
        ],
    },
    {
        "domanda": "Un amico ti chiede un consiglio importante. Come rispondi?",
        "opzioni": [
            ("Gli dico quello che sento, con sincerità e istinto", {"Poseidone": 1}),
            ("Analizzo la situazione con lui, punto per punto", {"Atena": 1}),
            ("Cerco di essere di supporto e di rassicurarlo", {"Apollo": 1}),
            ("Gli propongo un'alternativa creativa a cui forse non aveva pensato", {"Ermes": 1}),
        ],
    },
    {
        "domanda": "Qual è, per te, la vera definizione di forza?",
        "opzioni": [
            ("Il potere di far rispettare le regole e l'ordine", {"Zeus": 1}),
            ("La capacità di pianificare meglio dell'avversario", {"Atena": 1}),
            ("Il coraggio fisico e la determinazione in battaglia", {"Ares": 1}),
            ("L'ingegno che ti tira fuori da ogni situazione", {"Ermes": 1}),
        ],
    },
    {
        "domanda": "Come reagisci quando qualcuno che ami è in pericolo?",
        "opzioni": [
            ("Scateno tutto ciò che ho per proteggerlo, senza pensarci", {"Poseidone": 1}),
            ("Divento freddo e calcolatore: niente panico, solo azione", {"Ade": 1}),
            ("Cerco prima di tutto di curare o alleviare la sua sofferenza", {"Apollo": 1}),
            ("Il mio cuore va in mille pezzi, ma trovo la forza per lui", {"Afrodite": 1}),
        ],
    },
    {
        "domanda": "Se potessi avere un solo potere divino, quale sceglieresti?",
        "opzioni": [
            ("Comandare i fulmini e il cielo", {"Zeus": 1}),
            ("Controllare le acque e i mari in tempesta", {"Poseidone": 1}),
            ("Conoscere ogni strategia e segreto del mondo", {"Atena": 1}),
            ("Il fascino per conquistare il cuore di chiunque", {"Afrodite": 1}),
        ],
    },
    {
        "domanda": "Qual è il tuo posto preferito per riflettere?",
        "opzioni": [
            ("Un luogo silenzioso e appartato, lontano da tutti", {"Ade": 1}),
            ("In palestra, sfogandomi con l'allenamento", {"Ares": 1}),
            ("All'aperto, sotto il sole", {"Apollo": 1}),
            ("In viaggio, ovunque i miei piedi mi portino", {"Ermes": 1}),
        ],
    },
    {
        "domanda": "Cosa ti infastidisce di più negli altri?",
        "opzioni": [
            ("La mancanza di rispetto per l'autorità o le regole", {"Zeus": 1}),
            ("La superficialità e la pigrizia mentale", {"Atena": 1}),
            ("La freddezza e la mancanza di empatia", {"Apollo": 1}),
            ("La disonestà nei sentimenti", {"Afrodite": 1}),
        ],
    },
    {
        "domanda": "È l'ultima notte prima di una missione pericolosa. Come la passi?",
        "opzioni": [
            ("Vicino all'acqua, per calmarmi e pensare", {"Poseidone": 1}),
            ("In silenzio, ripassando ogni scenario possibile da solo", {"Ade": 1}),
            ("Continuando ad allenarmi fino all'ultimo minuto", {"Ares": 1}),
            ("Scherzando con gli amici per allentare la tensione", {"Ermes": 1}),
        ],
    },
]


# ============================================================
# CSS GLOBALE — sfondo condiviso + due identità tipografiche
# (pergamena/Hogwarts e marmo/Olimpo)
# ============================================================
st.markdown(
    textwrap.dedent("""\
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700&family=Cinzel+Decorative:wght@700;900&family=EB+Garamond:ital,wght@0,400;0,600;1,400&family=IM+Fell+English:ital@0;1&family=Lora:ital,wght@0,500;1,500&family=IBM+Plex+Mono:wght@500&display=swap');

    html, body, [class*="css"] { font-family: 'EB Garamond', serif; }

    .stApp {
        background:
            radial-gradient(ellipse at top left, rgba(120,90,30,0.25), transparent 55%),
            radial-gradient(ellipse at bottom right, rgba(40,20,60,0.35), transparent 55%),
            linear-gradient(180deg, #120d08 0%, #1c140b 40%, #120d08 100%);
        background-attachment: fixed;
    }

    #MainMenu, footer, header {visibility: hidden;}

    .hat-title {
        font-family: 'Cinzel Decorative', serif;
        font-size: 2.6rem;
        text-align: center;
        background: linear-gradient(180deg, #f3d98b 0%, #c9a227 55%, #8a6a12 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 25px rgba(201,162,39,0.25);
        margin-bottom: 0;
        animation: flicker 4s infinite ease-in-out;
    }
    @keyframes flicker { 0%, 100% { opacity: 1; } 50% { opacity: 0.88; } }

    .subtitle {
        font-family: 'IM Fell English', serif;
        font-style: italic;
        text-align: center;
        color: #cbb989;
        font-size: 1.05rem;
        margin-top: -8px;
        margin-bottom: 1.6rem;
        letter-spacing: 0.5px;
    }

    .parchment {
        background:
            radial-gradient(circle at 15% 20%, rgba(139,110,60,0.18), transparent 40%),
            radial-gradient(circle at 85% 80%, rgba(90,60,20,0.22), transparent 45%),
            linear-gradient(135deg, #ecdcb2 0%, #e2cd9a 50%, #dcc389 100%);
        border: 1px solid #8a6a12;
        outline: 6px solid #120d08;
        outline-offset: -12px;
        border-radius: 4px;
        padding: 2rem 2.2rem;
        box-shadow: 0 15px 45px rgba(0,0,0,0.55), inset 0 0 60px rgba(120,90,40,0.25);
        color: #2b1d0e;
        margin-bottom: 1.4rem;
    }
    .parchment h3 {
        font-family: 'Cinzel Decorative', serif;
        font-size: 1.25rem;
        color: #4a2f0e;
        border-bottom: 1px solid #8a6a12;
        padding-bottom: 8px;
        margin-top: 0;
    }

    .marble {
        background:
            radial-gradient(circle at 20% 25%, rgba(150,160,170,0.35), transparent 45%),
            radial-gradient(circle at 80% 75%, rgba(120,130,145,0.3), transparent 45%),
            linear-gradient(135deg, #eef0ee 0%, #e3e6e6 50%, #d9dcdb 100%);
        border: 1px solid #a68a3c;
        outline: 6px solid #120d08;
        outline-offset: -12px;
        border-radius: 2px;
        padding: 2rem 2.2rem;
        box-shadow: 0 15px 45px rgba(0,0,0,0.55), inset 0 0 50px rgba(120,130,140,0.25);
        color: #1c2430;
        margin-bottom: 1.4rem;
    }
    .marble h3 {
        font-family: 'Cinzel', serif;
        font-size: 1.2rem;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: #1c2430;
        border-bottom: 1px solid #a68a3c;
        padding-bottom: 8px;
        margin-top: 0;
    }

    .qcounter {
        font-family: 'IM Fell English', serif;
        font-style: italic;
        color: #cbb989;
        text-align: center;
        font-size: 1rem;
        margin-bottom: 6px;
    }
    .qcounter.oly {
        font-family: 'IBM Plex Mono', monospace;
        font-style: normal;
        letter-spacing: 2px;
        text-transform: uppercase;
        font-size: 0.8rem;
        color: #2b3b4a;
    }

    .camp-title {
        font-family: 'Cinzel', serif;
        font-size: 2.6rem;
        text-align: center;
        letter-spacing: 3px;
        background: linear-gradient(180deg, #0b3d59 0%, #145c86 55%, #b8860b 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .camp-subtitle {
        font-family: 'Lora', serif;
        font-style: italic;
        text-align: center;
        color: #3a4a3a;
        font-size: 1.05rem;
        margin-top: -8px;
        margin-bottom: 1.2rem;
        letter-spacing: 0.3px;
    }

    div.stButton > button {
        width: 100%;
        background: linear-gradient(180deg, #2a1e10 0%, #1a1108 100%);
        color: #e9d9ad;
        border: 1px solid #8a6a12;
        border-radius: 3px;
        padding: 0.8rem 1rem;
        font-family: 'EB Garamond', serif;
        font-size: 1.02rem;
        text-align: left;
        transition: all 0.25s ease;
        box-shadow: inset 0 0 12px rgba(0,0,0,0.4);
    }
    div.stButton > button:hover {
        border-color: #f3d98b;
        color: #f3d98b;
        box-shadow: 0 0 18px rgba(243,217,139,0.35), inset 0 0 12px rgba(0,0,0,0.4);
        transform: translateX(3px);
    }
    div.stButton > button:focus-visible {
        outline: 2px solid #f3d98b;
        outline-offset: 2px;
    }

    .result-card {
        border-radius: 6px;
        padding: 2.2rem 1.8rem;
        text-align: center;
        box-shadow: 0 20px 60px rgba(0,0,0,0.6);
        border: 2px solid rgba(255,255,255,0.25);
        animation: reveal 0.9s ease-out;
    }
    @keyframes reveal {
        0% { opacity: 0; transform: scale(0.85) translateY(20px); }
        100% { opacity: 1; transform: scale(1) translateY(0); }
    }
    .result-house {
        font-family: 'Cinzel Decorative', serif;
        font-size: 2.4rem;
        color: white;
        text-shadow: 0 3px 10px rgba(0,0,0,0.5);
        margin: 0.3rem 0;
    }
    .result-house.oly {
        font-family: 'Cinzel', serif;
        letter-spacing: 3px;
        text-transform: uppercase;
        font-size: 2.1rem;
    }
    .result-desc {
        font-family: 'IM Fell English', serif;
        font-style: italic;
        color: rgba(255,255,255,0.92);
        font-size: 1.15rem;
        max-width: 520px;
        margin: 0.6rem auto 0;
    }
    .result-desc.oly {
        font-family: 'Lora', serif;
        font-style: italic;
        letter-spacing: 0.2px;
    }

    .fact-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin-top: 1.4rem;
        font-family: 'EB Garamond', serif;
    }
    .fact-item {
        background: rgba(0,0,0,0.25);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 4px;
        padding: 10px 12px;
        color: white;
    }
    .fact-item.span2 { grid-column: span 2; }
    .fact-label {
        font-family: 'IM Fell English', serif;
        font-style: italic;
        font-size: 0.85rem;
        opacity: 0.75;
        display: block;
    }
    .fact-label.oly {
        font-family: 'IBM Plex Mono', monospace;
        font-style: normal;
        letter-spacing: 1px;
        text-transform: uppercase;
        font-size: 0.7rem;
    }
    .fact-value { font-size: 1rem; font-weight: 600; }

    .menu-card {
        border-radius: 6px;
        padding: 1.8rem 1.5rem;
        text-align: center;
        margin-bottom: 0.8rem;
        border: 2px solid rgba(255,255,255,0.18);
        box-shadow: 0 15px 40px rgba(0,0,0,0.5);
        transition: transform 0.25s ease;
    }
    .menu-card:hover { transform: translateY(-4px); }
    .menu-card-icon { font-size: 2.6rem; margin-bottom: 0.4rem; }
    .menu-card-title {
        font-family: 'Cinzel Decorative', serif;
        font-size: 1.4rem;
        color: #f3e9c9;
        margin-bottom: 0.5rem;
    }
    .menu-card-title.oly {
        font-family: 'Cinzel', serif;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        font-size: 1.25rem;
    }
    .menu-card-desc {
        font-family: 'EB Garamond', serif;
        font-style: italic;
        color: rgba(255,255,255,0.85);
        font-size: 0.95rem;
    }
    </style>
    """),
    unsafe_allow_html=True,
)


# ============================================================
# STEMMA HOGWARTS (SVG originale) e EMBLEMA DELL'OLIMPO (SVG originale)
# ============================================================
def render_crest():
    svg_code = textwrap.dedent("""\
    <div style="display:flex; justify-content:center; margin: 0.4rem 0 1.6rem;">
    <svg width="190" height="220" viewBox="0 0 200 240" xmlns="http://www.w3.org/2000/svg">
    <defs>
    <clipPath id="shieldClip">
    <path d="M12,12 H188 V145 C188,192 100,228 100,228 C100,228 12,192 12,145 Z" />
    </clipPath>
    <radialGradient id="glow" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#f3d98b" stop-opacity="0.9"/>
    <stop offset="100%" stop-color="#f3d98b" stop-opacity="0"/>
    </radialGradient>
    </defs>
    <g style="animation: crest-rotate 30s linear infinite; transform-origin: 100px 120px;" opacity="0.55">
    <circle cx="100" cy="10" r="2.4" fill="#f3d98b"/>
    <circle cx="190" cy="120" r="2.4" fill="#f3d98b"/>
    <circle cx="100" cy="230" r="2.4" fill="#f3d98b"/>
    <circle cx="10" cy="120" r="2.4" fill="#f3d98b"/>
    </g>
    <g clip-path="url(#shieldClip)">
    <rect x="12" y="12" width="88" height="108" fill="#740001"/>
    <rect x="100" y="12" width="88" height="108" fill="#1a472a"/>
    <rect x="12" y="120" width="88" height="108" fill="#0e1a40"/>
    <rect x="100" y="120" width="88" height="108" fill="#4a3b00"/>
    <path d="M45,55 q10,-18 20,0 q-10,8 0,20 q-15,4 -20,-20 Z" fill="#d3a625" opacity="0.85"/>
    <path d="M150,70 q-18,-4 -14,-22 q16,2 14,22 Z M136,48 q6,-10 12,0 q-6,6 -12,0 Z" fill="#c0c0c0" opacity="0.85"/>
    <path d="M40,170 q4,-14 18,-14 q-2,14 -18,14 Z M45,168 q10,4 18,-2" fill="none" stroke="#946B2D" stroke-width="3" opacity="0.85"/>
    <path d="M145,165 q-16,6 -16,-8 q10,-6 16,8 Z" fill="#2b2b2b" opacity="0.85"/>
    </g>
    <path d="M12,12 H188 V145 C188,192 100,228 100,228 C100,228 12,192 12,145 Z" fill="none" stroke="#f3d98b" stroke-width="3" opacity="0.9"/>
    <circle cx="100" cy="120" r="34" fill="url(#glow)">
    <animate attributeName="r" values="30;36;30" dur="3.5s" repeatCount="indefinite"/>
    </circle>
    <circle cx="100" cy="120" r="26" fill="#120d08" stroke="#f3d98b" stroke-width="2"/>
    <text x="100" y="130" font-family="Cinzel Decorative, serif" font-size="24" font-weight="700" fill="#f3d98b" text-anchor="middle">H</text>
    </svg>
    </div>
    <style>
    @keyframes crest-rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    </style>
    """)
    st.markdown(svg_code, unsafe_allow_html=True)


def render_olympus_emblem():
    svg_code = textwrap.dedent("""\
    <div style="display:flex; justify-content:center; margin: 0.4rem 0 1.6rem;">
    <svg width="190" height="200" viewBox="0 0 200 210" xmlns="http://www.w3.org/2000/svg">
    <defs>
    <radialGradient id="glow2" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#f3d98b" stop-opacity="0.9"/>
    <stop offset="100%" stop-color="#f3d98b" stop-opacity="0"/>
    </radialGradient>
    </defs>
    <g style="animation: oly-rotate 26s linear infinite; transform-origin: 100px 105px;" opacity="0.5">
    <path d="M100,8 l4,8 l-8,0 Z" fill="#f3d98b"/>
    <path d="M192,105 l-8,4 l0,-8 Z" fill="#f3d98b"/>
    <path d="M100,202 l4,-8 l-8,0 Z" fill="#f3d98b"/>
    <path d="M8,105 l8,4 l0,-8 Z" fill="#f3d98b"/>
    </g>
    <path d="M100,20 L172,58 V132 L100,190 L28,132 V58 Z" fill="none" stroke="#a68a3c" stroke-width="2" opacity="0.6"/>
    <path d="M30,64 L100,26 L170,64 L158,70 L100,38 L42,70 Z" fill="#d9dcdb" stroke="#a68a3c" stroke-width="1.5"/>
    <path d="M55,120 q-10,20 0,40 q6,-4 4,-20 q8,10 10,-4 q-8,-2 -14,-16 Z" fill="#8fa6ad" opacity="0.85"/>
    <path d="M145,120 q10,20 0,40 q-6,-4 -4,-20 q-8,10 -10,-4 q8,-2 14,-16 Z" fill="#8fa6ad" opacity="0.85"/>
    <path d="M100,55 L106,95 L96,95 Z M92,90 L108,90 L112,100 L88,100 Z" fill="#c9a227"/>
    <circle cx="100" cy="105" r="30" fill="url(#glow2)">
    <animate attributeName="r" values="26;32;26" dur="3.5s" repeatCount="indefinite"/>
    </circle>
    <circle cx="100" cy="105" r="22" fill="#120d08" stroke="#f3d98b" stroke-width="2"/>
    <text x="100" y="113" font-family="Cinzel, serif" font-size="20" font-weight="700" fill="#f3d98b" text-anchor="middle">Ω</text>
    </svg>
    </div>
    <style>
    @keyframes oly-rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    </style>
    """)
    st.markdown(svg_code, unsafe_allow_html=True)


def render_light_background():
    st.markdown(
        textwrap.dedent("""\
        <style>
        .stApp {
            background:
                radial-gradient(ellipse at top right, rgba(255, 221, 138, 0.35), transparent 55%),
                radial-gradient(ellipse at bottom left, rgba(63, 151, 173, 0.25), transparent 60%),
                linear-gradient(180deg, #cfe8f3 0%, #eaf4e0 45%, #f6e4b8 100%) !important;
            background-attachment: fixed !important;
        }
        </style>
        """),
        unsafe_allow_html=True,
    )


def render_camp_banner():
    svg_code = textwrap.dedent("""\
    <div style="margin: 0 0 1.4rem; border-radius:6px; overflow:hidden; border:1px solid #a68a3c; box-shadow:0 15px 40px rgba(0,0,0,0.25);">
    <svg viewBox="0 0 800 220" xmlns="http://www.w3.org/2000/svg" style="display:block; width:100%; height:auto;">
    <defs>
    <linearGradient id="camp-sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#bfe3f5"/>
    <stop offset="55%" stop-color="#eaf4e0"/>
    <stop offset="100%" stop-color="#f6e4b8"/>
    </linearGradient>
    <linearGradient id="camp-sea" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#3f97ad"/>
    <stop offset="100%" stop-color="#1f6b80"/>
    </linearGradient>
    </defs>
    <rect x="0" y="0" width="800" height="220" fill="url(#camp-sky)"/>
    <circle cx="680" cy="55" r="30" fill="#ffdf8a" opacity="0.9"/>
    <path d="M0,150 Q200,110 400,140 T800,120 V220 H0 Z" fill="#7fae6b" opacity="0.9"/>
    <path d="M0,175 Q220,150 430,168 T800,155 V220 H0 Z" fill="#5f8f52"/>
    <g fill="#3d3226" opacity="0.9">
    <path d="M110,150 l24,-22 l24,22 Z"/>
    <path d="M170,158 l22,-20 l22,20 Z"/>
    <path d="M300,148 l24,-22 l24,22 Z"/>
    <path d="M540,152 l22,-20 l22,20 Z"/>
    </g>
    <g opacity="0.85">
    <rect x="600" y="120" width="10" height="45" fill="#e6e2d6"/>
    <rect x="622" y="120" width="10" height="45" fill="#e6e2d6"/>
    <rect x="644" y="120" width="10" height="45" fill="#e6e2d6"/>
    <rect x="592" y="112" width="70" height="10" fill="#d8d2bd"/>
    <path d="M592,112 L627,90 L662,112 Z" fill="#cfc7a8"/>
    </g>
    <rect x="0" y="196" width="800" height="24" fill="url(#camp-sea)"/>
    <path d="M0,200 q20,-6 40,0 t40,0 t40,0 t40,0 t40,0 t40,0 t40,0 t40,0 t40,0 t40,0 t40,0 t40,0 t40,0 t40,0 t40,0 t40,0 t40,0 t40,0 t40,0" fill="none" stroke="#eaf4e8" stroke-width="2" opacity="0.5"/>
    </svg>
    </div>
    """)
    st.markdown(svg_code, unsafe_allow_html=True)


# ============================================================
# EFFETTO MACCHINA DA SCRIVERE per il testo della domanda
# (due varianti estetiche: pergamena e marmo)
# ============================================================
def render_typewriter_question(testo, stile="pergamena"):
    righe = max(2, -(-len(testo) // 50))
    altezza = 70 + righe * 30
    testo_js = json.dumps(testo)

    if stile == "pergamena":
        box_bg = """
            radial-gradient(circle at 15% 20%, rgba(139,110,60,0.18), transparent 40%),
            radial-gradient(circle at 85% 80%, rgba(90,60,20,0.22), transparent 45%),
            linear-gradient(135deg, #ecdcb2 0%, #e2cd9a 50%, #dcc389 100%)"""
        border_color = "#8a6a12"
        text_color = "#4a2f0e"
        font_import = "Cinzel+Decorative:wght@700"
        font_family = "'Cinzel Decorative', serif"
        text_transform = "none"
        letter_spacing = "normal"
    else:
        box_bg = """
            radial-gradient(circle at 20% 25%, rgba(150,160,170,0.35), transparent 45%),
            radial-gradient(circle at 80% 75%, rgba(120,130,145,0.3), transparent 45%),
            linear-gradient(135deg, #eef0ee 0%, #e3e6e6 50%, #d9dcdb 100%)"""
        border_color = "#a68a3c"
        text_color = "#1c2430"
        font_import = "Cinzel:wght@700"
        font_family = "'Cinzel', serif"
        text_transform = "uppercase"
        letter_spacing = "0.5px"

    html_code = f"""
    <html>
    <head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family={font_import}&display=swap');
        body {{ margin:0; background:transparent; }}
        .box {{
            background: {box_bg};
            border: 1px solid {border_color};
            outline: 6px solid #120d08;
            outline-offset: -12px;
            border-radius: 4px;
            padding: 1.4rem 1.6rem;
            box-shadow: inset 0 0 60px rgba(120,90,40,0.2);
            box-sizing: border-box;
        }}
        h3 {{
            font-family: {font_family};
            font-size: 1.1rem;
            color: {text_color};
            font-weight: 700;
            margin: 0;
            border-bottom: 1px solid {border_color};
            padding-bottom: 8px;
            line-height: 1.5;
            text-transform: {text_transform};
            letter-spacing: {letter_spacing};
        }}
        .cursor {{
            display: inline-block;
            animation: blink 0.8s step-end infinite;
            color: {text_color};
        }}
        @keyframes blink {{ 50% {{ opacity: 0; }} }}
    </style>
    </head>
    <body>
        <div class="box"><h3 id="q"></h3></div>
        <script>
            const testo = {testo_js};
            const el = document.getElementById('q');
            let i = 0;
            function scrivi() {{
                if (i <= testo.length) {{
                    el.innerHTML = testo.slice(0, i) + '<span class="cursor">|</span>';
                    i++;
                    setTimeout(scrivi, 16);
                }} else {{
                    el.innerHTML = testo;
                }}
            }}
            scrivi();
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=altezza)


# ============================================================
# GENERAZIONE IMMAGINE CONDIVIDIBILE (generica per entrambi i quiz)
# ============================================================
@st.cache_resource(show_spinner=False)
def carica_font():
    fonts = {}
    sorgenti = {
        "titolo_hp": "https://github.com/google/fonts/raw/main/ofl/cinzeldecorative/CinzelDecorative-Bold.ttf",
        "titolo_pj": "https://github.com/google/fonts/raw/main/ofl/cinzel/Cinzel[wght].ttf",
        "corpo": "https://github.com/google/fonts/raw/main/ofl/ebgaramond/EBGaramond-Regular.ttf",
        "corsivo": "https://github.com/google/fonts/raw/main/ofl/ebgaramond/EBGaramond-Italic.ttf",
    }
    for nome, url in sorgenti.items():
        try:
            r = requests.get(url, timeout=6)
            r.raise_for_status()
            fonts[nome] = r.content
        except Exception:
            fonts[nome] = None
    return fonts


def _font(fonts_bytes, chiave, size):
    if fonts_bytes.get(chiave):
        try:
            return ImageFont.truetype(io.BytesIO(fonts_bytes[chiave]), size)
        except Exception:
            pass
    return ImageFont.load_default()


def genera_immagine_condivisione(nome_entita, info, eyebrow_text, footer_text, titolo_font_key="titolo_hp"):
    W, H = 1080, 1080
    top = info["rgb_top"]
    bottom = info["rgb_bottom"]
    img = Image.new("RGB", (W, H), top)
    draw = ImageDraw.Draw(img)

    for y in range(H):
        t = y / H
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    margine = 46
    draw.rectangle([margine, margine, W - margine, H - margine], outline=(243, 217, 139), width=6)
    draw.rectangle(
        [margine + 14, margine + 14, W - margine - 14, H - margine - 14],
        outline=(243, 217, 139, 120), width=1,
    )

    fonts_bytes = carica_font()
    f_eyebrow = _font(fonts_bytes, "corsivo", 32)
    f_titolo = _font(fonts_bytes, titolo_font_key, 88)
    f_desc = _font(fonts_bytes, "corpo", 34)
    f_footer = _font(fonts_bytes, "corsivo", 26)

    def testo_centrato(testo, y, font, fill=(255, 255, 255)):
        bbox = draw.textbbox((0, 0), testo, font=font)
        larghezza = bbox[2] - bbox[0]
        draw.text(((W - larghezza) / 2, y), testo, font=font, fill=fill)

    testo_centrato(eyebrow_text, 165, f_eyebrow, (255, 255, 255))
    testo_centrato(nome_entita.upper(), 225, f_titolo, (255, 255, 255))

    testo_avvolto = textwrap.fill(info["descrizione"], width=42)
    y_desc = 410
    for riga in testo_avvolto.split("\n"):
        testo_centrato(riga, y_desc, f_desc, (255, 255, 255))
        y_desc += 46

    dettagli = info["dettagli"][:4]
    y_box = y_desc + 60
    box_h = 240
    draw.rectangle([120, y_box, W - 120, y_box + box_h], outline=(255, 255, 255, 150), width=2)
    riga_h = box_h / len(dettagli)
    for i, (label, valore) in enumerate(dettagli):
        y_riga = y_box + i * riga_h + riga_h / 2 - 16
        draw.text((150, y_riga - 22), label.upper(), font=f_footer, fill=(255, 255, 255, 200))
        draw.text((150, y_riga + 8), valore, font=f_desc, fill=(255, 255, 255))
        if i < len(dettagli) - 1:
            draw.line(
                [(150, y_box + (i + 1) * riga_h), (W - 150, y_box + (i + 1) * riga_h)],
                fill=(255, 255, 255, 60), width=1,
            )

    testo_centrato(footer_text, H - 110, f_footer, (255, 255, 255))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


# ============================================================
# MOTORE GENERICO DEL QUIZ (usato da entrambi i quiz)
# ============================================================
def init_state(prefix, entities):
    if f"{prefix}_iniziato" not in st.session_state:
        st.session_state[f"{prefix}_iniziato"] = False
    if f"{prefix}_domanda" not in st.session_state:
        st.session_state[f"{prefix}_domanda"] = 0
    if f"{prefix}_punteggi" not in st.session_state:
        st.session_state[f"{prefix}_punteggi"] = {nome: 0.0 for nome in entities}
    if f"{prefix}_finito" not in st.session_state:
        st.session_state[f"{prefix}_finito"] = False


def reset_quiz(prefix, entities, questions):
    st.session_state[f"{prefix}_iniziato"] = False
    st.session_state[f"{prefix}_domanda"] = 0
    st.session_state[f"{prefix}_punteggi"] = {nome: 0.0 for nome in entities}
    st.session_state[f"{prefix}_ordine"] = list(range(len(questions)))
    random.shuffle(st.session_state[f"{prefix}_ordine"])
    st.session_state[f"{prefix}_finito"] = False


def rispondi(prefix, questions, punti_assegnati):
    for nome, punti in punti_assegnati.items():
        st.session_state[f"{prefix}_punteggi"][nome] += punti
    st.session_state[f"{prefix}_domanda"] += 1
    if st.session_state[f"{prefix}_domanda"] >= len(questions):
        st.session_state[f"{prefix}_finito"] = True


def render_radar(labels, valori):
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=valori + [valori[0]],
        theta=labels + [labels[0]],
        fill='toself',
        fillcolor='rgba(201,162,39,0.25)',
        line=dict(color='#f3d98b', width=2),
        marker=dict(size=6, color='#f3d98b'),
    ))
    fig.update_layout(
        polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(visible=True, showticklabels=False, gridcolor='rgba(255,255,255,0.15)'),
            angularaxis=dict(color='#e9d9ad', gridcolor='rgba(255,255,255,0.15)'),
        ),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e9d9ad', family='EB Garamond'),
        margin=dict(l=40, r=40, t=20, b=20),
        height=380,
    )
    st.plotly_chart(fig, use_container_width=True)


# ============================================================
# QUIZ 1 — SMISTAMENTO DI HOGWARTS
# ============================================================
def render_hogwarts():
    prefix = "hp"
    init_state(prefix, HOUSES)
    if f"{prefix}_ordine" not in st.session_state:
        st.session_state[f"{prefix}_ordine"] = list(range(len(QUESTIONS_HP)))
        random.shuffle(st.session_state[f"{prefix}_ordine"])

    if st.button("← Torna al menu"):
        st.session_state.pagina = "menu"
        st.rerun()

    st.markdown('<div class="hat-title">🎩 Il Cappello Parlante 🎩</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">"Mmh... difficile, molto difficile. Vediamo cosa nascondi davvero..."</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state[f"{prefix}_iniziato"]:
        render_crest()
        st.markdown(
            textwrap.dedent("""\
            <div class="parchment">
            <h3>Prima dello Smistamento</h3>
            Rispondi con sincerità a 12 situazioni ispirate al mondo di Hogwarts.
            Non esistono risposte giuste o sbagliate: il Cappello guarda oltre le
            parole, dritto nella tua natura. Alla fine scoprirai la casa più affine
            a te, con il tuo profilo completo tra le quattro — e potrai scaricare
            la tua card da condividere.
            </div>
            """),
            unsafe_allow_html=True,
        )
        if st.button("🕯️ Indossa il Cappello", use_container_width=True):
            st.session_state[f"{prefix}_iniziato"] = True
            st.rerun()

    elif not st.session_state[f"{prefix}_finito"]:
        idx = st.session_state[f"{prefix}_ordine"][st.session_state[f"{prefix}_domanda"]]
        domanda = QUESTIONS_HP[idx]

        st.markdown(
            f'<div class="qcounter">Domanda {st.session_state[f"{prefix}_domanda"] + 1} di {len(QUESTIONS_HP)}</div>',
            unsafe_allow_html=True,
        )
        st.progress(st.session_state[f"{prefix}_domanda"] / len(QUESTIONS_HP))
        render_typewriter_question(domanda["domanda"], stile="pergamena")

        opzioni = list(domanda["opzioni"])
        random.Random(idx + 100).shuffle(opzioni)
        for testo_opzione, punti in opzioni:
            if st.button(testo_opzione, key=f"{prefix}_{idx}_{testo_opzione}"):
                rispondi(prefix, QUESTIONS_HP, punti)
                st.rerun()

    else:
        punteggi = st.session_state[f"{prefix}_punteggi"]
        vincitore = max(punteggi, key=punteggi.get)
        info = HOUSES[vincitore]

        st.balloons()

        dettagli_html = "".join(
            f'<div class="fact-item"><span class="fact-label">{label}</span><span class="fact-value">{valore}</span></div>'
            for label, valore in info["dettagli"]
        )

        st.markdown(
            textwrap.dedent(f"""\
            <div class="result-card" style="background:{info['gradiente']};">
            <div style="font-size:3.2rem;">{info['emoji']}</div>
            <div class="result-house">{vincitore}</div>
            <div class="result-desc">{info['descrizione']}</div>
            <div class="fact-grid">{dettagli_html}</div>
            </div>
            """),
            unsafe_allow_html=True,
        )

        st.write("")
        with st.spinner("Sto preparando la tua card da condividere..."):
            buf = genera_immagine_condivisione(
                vincitore, info,
                "IL CAPPELLO PARLANTE MI HA SMISTATO A",
                "SMISTAMENTO DI HOGWARTS",
                titolo_font_key="titolo_hp",
            )
        col1, col2 = st.columns([1, 1])
        with col1:
            st.image(buf, use_container_width=True)
        with col2:
            st.write("")
            st.write("Scarica la tua card e condividila dove vuoi.")
            st.download_button(
                "📥 Scarica la card", data=buf,
                file_name=f"smistamento_{vincitore.lower()}.png",
                mime="image/png", use_container_width=True,
            )

        st.write("")
        st.markdown('<div class="parchment"><h3>Il tuo profilo tra le quattro case</h3></div>', unsafe_allow_html=True)
        case = list(HOUSES.keys())
        render_radar(case, [punteggi[c] for c in case])

        for casa, punti in sorted(punteggi.items(), key=lambda x: -x[1]):
            pct = punti / len(QUESTIONS_HP)
            st.write(f"{HOUSES[casa]['emoji']} **{casa}** — {punti:g} punti")
            st.progress(min(pct, 1.0))

        st.write("")
        if st.button("🔄 Rifai lo Smistamento", use_container_width=True):
            reset_quiz(prefix, HOUSES, QUESTIONS_HP)
            st.rerun()


# ============================================================
# QUIZ 2 — CHI È IL TUO GENITORE DIVINO?
# ============================================================
def render_percy():
    prefix = "pj"
    init_state(prefix, GODS)
    if f"{prefix}_ordine" not in st.session_state:
        st.session_state[f"{prefix}_ordine"] = list(range(len(QUESTIONS_PJ)))
        random.shuffle(st.session_state[f"{prefix}_ordine"])

    if st.button("← Torna al menu"):
        st.session_state.pagina = "menu"
        st.rerun()

    render_light_background()

    st.markdown('<div class="camp-title">⚡ CAMPO MEZZOSANGUE ⚡</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="camp-subtitle">"Gli dèi dell\'Olimpo osservano... quale sangue scorre davvero nelle tue vene?"</div>',
        unsafe_allow_html=True,
    )
    render_camp_banner()

    if not st.session_state[f"{prefix}_iniziato"]:
        render_olympus_emblem()
        st.markdown(
            textwrap.dedent("""\
            <div class="marble">
            <h3>Prima del Responso dell'Oracolo</h3>
            Rispondi con sincerità a 12 situazioni ispirate al Campo Mezzosangue.
            Non esistono risposte giuste o sbagliate: gli dèi guardano dritto nella
            tua vera natura. Alla fine scoprirai quale dio dell'Olimpo è il tuo
            genitore divino, con il tuo profilo completo — e potrai scaricare la
            tua card da condividere.
            </div>
            """),
            unsafe_allow_html=True,
        )
        if st.button("⚡ Consulta l'Oracolo", use_container_width=True):
            st.session_state[f"{prefix}_iniziato"] = True
            st.rerun()

    elif not st.session_state[f"{prefix}_finito"]:
        idx = st.session_state[f"{prefix}_ordine"][st.session_state[f"{prefix}_domanda"]]
        domanda = QUESTIONS_PJ[idx]

        st.markdown(
            f'<div class="qcounter oly">Domanda {st.session_state[f"{prefix}_domanda"] + 1} di {len(QUESTIONS_PJ)}</div>',
            unsafe_allow_html=True,
        )
        st.progress(st.session_state[f"{prefix}_domanda"] / len(QUESTIONS_PJ))
        render_typewriter_question(domanda["domanda"], stile="marmo")

        opzioni = list(domanda["opzioni"])
        random.Random(idx + 200).shuffle(opzioni)
        for testo_opzione, punti in opzioni:
            if st.button(testo_opzione, key=f"{prefix}_{idx}_{testo_opzione}"):
                rispondi(prefix, QUESTIONS_PJ, punti)
                st.rerun()

    else:
        punteggi = st.session_state[f"{prefix}_punteggi"]
        vincitore = max(punteggi, key=punteggi.get)
        info = GODS[vincitore]

        st.balloons()

        dettagli_html = "".join(
            f'<div class="fact-item"><span class="fact-label oly">{label}</span><span class="fact-value">{valore}</span></div>'
            for label, valore in info["dettagli"]
        )

        st.markdown(
            textwrap.dedent(f"""\
            <div class="result-card" style="background:{info['gradiente']};">
            <div style="font-size:3.2rem;">{info['emoji']}</div>
            <div class="result-house oly">{vincitore}</div>
            <div class="result-desc oly">{info['descrizione']}</div>
            <div class="fact-grid">{dettagli_html}</div>
            </div>
            """),
            unsafe_allow_html=True,
        )

        st.write("")
        with st.spinner("Sto preparando la tua card da condividere..."):
            buf = genera_immagine_condivisione(
                vincitore, info,
                "L'ORACOLO HA PARLATO: SEI FIGLIO DI",
                "CHI È IL TUO GENITORE DIVINO?",
                titolo_font_key="titolo_pj",
            )
        col1, col2 = st.columns([1, 1])
        with col1:
            st.image(buf, use_container_width=True)
        with col2:
            st.write("")
            st.write("Scarica la tua card e condividila dove vuoi.")
            st.download_button(
                "📥 Scarica la card", data=buf,
                file_name=f"genitore_divino_{vincitore.lower()}.png",
                mime="image/png", use_container_width=True,
            )

        st.write("")
        st.markdown('<div class="marble"><h3>Il tuo profilo tra gli dèi</h3></div>', unsafe_allow_html=True)
        divinita = list(GODS.keys())
        render_radar(divinita, [punteggi[d] for d in divinita])

        for dio, punti in sorted(punteggi.items(), key=lambda x: -x[1]):
            pct = punti / len(QUESTIONS_PJ)
            st.write(f"{GODS[dio]['emoji']} **{dio}** — {punti:g} punti")
            st.progress(min(pct, 1.0))

        st.write("")
        if st.button("🔄 Consulta di nuovo l'Oracolo", use_container_width=True):
            reset_quiz(prefix, GODS, QUESTIONS_PJ)
            st.rerun()


# ============================================================
# MENU INIZIALE
# ============================================================
def render_menu():
    st.markdown('<div class="hat-title">Fantasy Quiz</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Scegli quale mondo vuoi lasciare che ti smisti</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            textwrap.dedent("""\
            <div class="menu-card" style="background:linear-gradient(160deg, #3d0a0a 0%, #1a2f14 100%);">
            <div class="menu-card-icon">🎩</div>
            <div class="menu-card-title">Smistamento di Hogwarts</div>
            <div class="menu-card-desc">Scopri in quale delle quattro case verresti smistato</div>
            </div>
            """),
            unsafe_allow_html=True,
        )
        if st.button("Entra a Hogwarts", key="entra_hp", use_container_width=True):
            st.session_state.pagina = "hogwarts"
            st.rerun()

    with col2:
        st.markdown(
            textwrap.dedent("""\
            <div class="menu-card" style="background:linear-gradient(160deg, #0e2233 0%, #3a2a05 100%);">
            <div class="menu-card-icon">⚡</div>
            <div class="menu-card-title oly">Chi è il tuo genitore divino?</div>
            <div class="menu-card-desc">Scopri quale dio dell'Olimpo scorre nel tuo sangue</div>
            </div>
            """),
            unsafe_allow_html=True,
        )
        if st.button("Entra al Campo", key="entra_pj", use_container_width=True):
            st.session_state.pagina = "percy"
            st.rerun()


# ============================================================
# NAVIGAZIONE PRINCIPALE
# ============================================================
if "pagina" not in st.session_state:
    st.session_state.pagina = "menu"

if st.session_state.pagina == "menu":
    render_menu()
elif st.session_state.pagina == "hogwarts":
    render_hogwarts()
elif st.session_state.pagina == "percy":
    render_percy()