import streamlit as st
import streamlit.components.v1 as components
import random
import json
import io
import re
import html
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
    "Efesto": {
        "gradiente": "linear-gradient(135deg, #281406 0%, #6e3a12 50%, #c8782e 100%)",
        "rgb_top": (40, 20, 6),
        "rgb_bottom": (200, 120, 46),
        "emoji": "🔨",
        "descrizione": "Le tue mani parlano più della tua voce. Costruisci, ripari, inventi: la tua genialità pratica è la tua forma più autentica di espressione, anche se pochi la notano subito.",
        "dettagli": [
            ("Dominio", "Fabbri, fuoco e creazioni meccaniche"),
            ("Animale simbolo", "Asino"),
            ("Colori", "Bronzo e rosso fuoco"),
            ("Cabina", "Cabina 9"),
            ("Figli noti", "Leo Valdez, Charles Beckendorf"),
            ("Valori", "Ingegno pratico, pazienza, perseveranza"),
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
            ("In officina, a costruire o riparare qualcosa con le mie mani", {"Efesto": 1}),
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
            ("Costruire qualcosa con le mie mani, dall'inizio alla fine", {"Efesto": 1}),
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
            ("Gli costruisco o aggiusto qualcosa di concreto che possa aiutarlo davvero", {"Efesto": 1}),
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
            ("Costruisco silenziosamente qualcosa che possa proteggerlo davvero", {"Efesto": 1}),
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
            ("In un'officina, lavorando con le mani mentre penso", {"Efesto": 1}),
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
            ("Controllando e riparando ogni pezzo del mio equipaggiamento", {"Efesto": 1}),
        ],
    },
]


# ============================================================
# DATI — FAZIONI DI DIVERGENT
# (sede, simbolo, colori, valori, personaggi noti: dettagli
#  fattuali dell'universo del romanzo, non testo protetto)
# ============================================================
DIVERGENT = {
    "Abneganti": {
        "gradiente": "linear-gradient(135deg, #3c3c40 0%, #6b6b70 50%, #aaaaad 100%)",
        "rgb_top": (60, 60, 64),
        "rgb_bottom": (170, 170, 173),
        "emoji": "🤲",
        "descrizione": "Ti dimentichi facilmente di te stesso per mettere gli altri al primo posto. Il servizio silenzioso, per te, vale più di qualsiasi riconoscimento.",
        "dettagli": [
            ("Sede", "Quartiere vicino al Recinto"),
            ("Simbolo", "Mani unite a coppa"),
            ("Colori", "Grigio"),
            ("Valori", "Altruismo, umiltà, servizio"),
            ("Personaggi noti", "Tris Prior (di origine), Andrew e Natalie Prior"),
        ],
    },
    "Eruditi": {
        "gradiente": "linear-gradient(135deg, #0a1e3c 0%, #1d3f6b 50%, #5b8fd6 100%)",
        "rgb_top": (10, 30, 60),
        "rgb_bottom": (91, 143, 214),
        "emoji": "👁️",
        "descrizione": "La conoscenza è il tuo faro. Non smetti mai di fare domande, e la verità ti interessa più delle comodità.",
        "dettagli": [
            ("Sede", "La grande biblioteca centrale"),
            ("Simbolo", "Occhio"),
            ("Colori", "Blu"),
            ("Valori", "Intelligenza, curiosità, logica"),
            ("Personaggi noti", "Caleb Prior, Jeanine Matthews"),
        ],
    },
    "Intrepidi": {
        "gradiente": "linear-gradient(135deg, #100a08 0%, #4a1a0a 50%, #c8641e 100%)",
        "rgb_top": (16, 10, 8),
        "rgb_bottom": (200, 100, 30),
        "emoji": "🔥",
        "descrizione": "Vivi per il momento in cui la paura si trasforma in azione. Il salto nel vuoto non ti spaventa: è lì che ti senti più vivo.",
        "dettagli": [
            ("Sede", "Ex parco divertimenti, vicino ai binari"),
            ("Simbolo", "Fiamme"),
            ("Colori", "Nero"),
            ("Valori", "Coraggio, audacia, adrenalina"),
            ("Personaggi noti", "Tris Prior (per scelta), Tobias 'Four' Eaton"),
        ],
    },
    "Pacifici": {
        "gradiente": "linear-gradient(135deg, #4a1608 0%, #8a4a12 50%, #e0c04a 100%)",
        "rgb_top": (74, 22, 8),
        "rgb_bottom": (224, 192, 74),
        "emoji": "🌳",
        "descrizione": "Cerchi l'armonia ovunque tu vada. Preferisci costruire ponti piuttosto che vincere una battaglia.",
        "dettagli": [
            ("Sede", "Frutteti e fattorie fuori città"),
            ("Simbolo", "Albero"),
            ("Colori", "Rosso e giallo"),
            ("Valori", "Pace, gentilezza, armonia"),
            ("Personaggi noti", "Robert Black"),
        ],
    },
    "Candidi": {
        "gradiente": "linear-gradient(135deg, #141414 0%, #6a6a6a 50%, #e6e6e6 100%)",
        "rgb_top": (20, 20, 20),
        "rgb_bottom": (230, 230, 230),
        "emoji": "⚖️",
        "descrizione": "Non sopporti le bugie, nemmeno quelle gentili. Dici quello che pensi, sempre, anche quando fa male.",
        "dettagli": [
            ("Sede", "Il tribunale, edificio bianco e nero"),
            ("Simbolo", "Bilancia"),
            ("Colori", "Bianco e nero"),
            ("Valori", "Onestà, schiettezza, verità"),
            ("Personaggi noti", "Christina"),
        ],
    },
}

QUESTIONS_DIV = [
    {
        "domanda": "Il Giorno della Scelta è arrivato e il coltello trema nella tua mano. Cosa pensi in quell'istante?",
        "opzioni": [
            ("Penso a chi resterebbe senza il mio aiuto se me ne andassi", {"Abneganti": 1}),
            ("Penso a quale scelta sia oggettivamente la più razionale per il mio futuro", {"Eruditi": 1}),
            ("Penso solo al salto che sto per fare, senza guardarmi indietro", {"Intrepidi": 1}),
            ("Penso a restare in pace con tutti, qualunque cosa scelga", {"Pacifici": 1}),
            ("Penso che dovrei semplicemente dire ad alta voce cosa provo davvero", {"Candidi": 1}),
        ],
    },
    {
        "domanda": "Durante l'addestramento, un compagno ti sfida apertamente davanti al gruppo. Come reagisci?",
        "opzioni": [
            ("Cerco di calmare la situazione, mettendo da parte il mio orgoglio", {"Abneganti": 1}),
            ("Rispondo con un argomento logico che smonta la sua provocazione", {"Eruditi": 1}),
            ("Accetto la sfida subito, qualunque essa sia", {"Intrepidi": 1}),
            ("Provo a capire cosa lo turba davvero, oltre la sfida", {"Pacifici": 1}),
            ("Gli dico chiaramente cosa penso di lui, senza girarci intorno", {"Candidi": 1}),
        ],
    },
    {
        "domanda": "Scopri un segreto scomodo su qualcuno che rispetti. Cosa fai?",
        "opzioni": [
            ("Lo tengo per me, se rivelarlo farebbe più male che bene", {"Abneganti": 1}),
            ("Verifico i fatti con cura prima di trarre conclusioni", {"Eruditi": 1}),
            ("Lo affronto di petto, subito, senza troppi giri di parole", {"Intrepidi": 1}),
            ("Aspetto il momento giusto per parlarne con gentilezza", {"Pacifici": 1}),
            ("Non riesco a tenermelo dentro: la verità va detta", {"Candidi": 1}),
        ],
    },
    {
        "domanda": "Cosa temi di più, in fondo?",
        "opzioni": [
            ("Diventare egoista e dimenticarmi degli altri", {"Abneganti": 1}),
            ("Restare ignorante o commettere un errore per superficialità", {"Eruditi": 1}),
            ("Essere paralizzato dalla paura nel momento decisivo", {"Intrepidi": 1}),
            ("Il conflitto costante e la perdita dell'armonia", {"Pacifici": 1}),
            ("Essere costretto a mentire o nascondere chi sono davvero", {"Candidi": 1}),
        ],
    },
    {
        "domanda": "Il tuo posto ideale nella società sarebbe...",
        "opzioni": [
            ("Un ruolo di servizio silenzioso, senza bisogno di riconoscimenti", {"Abneganti": 1}),
            ("Un laboratorio o una biblioteca dove poter studiare senza limiti", {"Eruditi": 1}),
            ("In prima linea, a proteggere gli altri con azioni concrete", {"Intrepidi": 1}),
            ("Un luogo che favorisca la pace e la collaborazione tra tutti", {"Pacifici": 1}),
            ("Un posto dove la verità venga sempre a galla, senza eccezioni", {"Candidi": 1}),
        ],
    },
    {
        "domanda": "Un amico ti chiede un parere sincero su una sua scelta importante. Come rispondi?",
        "opzioni": [
            ("Penso soprattutto a come la mia risposta influirà su di lui", {"Abneganti": 1}),
            ("Gli offro un'analisi oggettiva dei pro e dei contro", {"Eruditi": 1}),
            ("Lo incoraggio a buttarsi, qualunque sia il rischio", {"Intrepidi": 1}),
            ("Cerco la risposta più delicata, che non ferisca nessuno", {"Pacifici": 1}),
            ("Gli dico esattamente quello che penso, anche se è scomodo", {"Candidi": 1}),
        ],
    },
    {
        "domanda": "Cosa ti fa sentire più forte?",
        "opzioni": [
            ("Sapere di aver aiutato qualcuno senza chiedere nulla in cambio", {"Abneganti": 1}),
            ("Aver capito qualcosa che nessun altro aveva colto", {"Eruditi": 1}),
            ("Aver superato una paura che mi bloccava da tempo", {"Intrepidi": 1}),
            ("Aver riportato la calma in una situazione tesa", {"Pacifici": 1}),
            ("Aver detto la verità anche quando era difficile farlo", {"Candidi": 1}),
        ],
    },
    {
        "domanda": "Come reagisci di fronte a un'ingiustizia?",
        "opzioni": [
            ("Cerco di risolverla aiutando concretamente chi ne soffre", {"Abneganti": 1}),
            ("Cerco prove e argomenti solidi per dimostrarla", {"Eruditi": 1}),
            ("Reagisco d'istinto, subito, senza troppi calcoli", {"Intrepidi": 1}),
            ("Provo a mediare, cercando un accordo che vada bene a tutti", {"Pacifici": 1}),
            ("La denuncio apertamente, senza paura delle conseguenze", {"Candidi": 1}),
        ],
    },
    {
        "domanda": "Se dovessi scegliere un solo valore da portare avanti per sempre, quale sarebbe?",
        "opzioni": [
            ("L'altruismo", {"Abneganti": 1}),
            ("La conoscenza", {"Eruditi": 1}),
            ("Il coraggio", {"Intrepidi": 1}),
            ("La pace", {"Pacifici": 1}),
            ("L'onestà", {"Candidi": 1}),
        ],
    },
    {
        "domanda": "È l'ultima notte prima di una prova decisiva. Come la passi?",
        "opzioni": [
            ("Penso a come posso essere utile agli altri il giorno dopo", {"Abneganti": 1}),
            ("Ripasso ogni singolo dettaglio che potrebbe servirmi", {"Eruditi": 1}),
            ("Non riesco a stare fermo, voglio solo che arrivi il momento", {"Intrepidi": 1}),
            ("Sto con le persone care, per affrontare tutto con serenità", {"Pacifici": 1}),
            ("Mi confronto apertamente con me stesso su cosa provo davvero", {"Candidi": 1}),
        ],
    },
]


# ============================================================
# DATI — DISTRETTI DI HUNGER GAMES
# (industria, simbolo, colori, tributi noti, valori: dettagli
#  fattuali dell'universo del romanzo, non testo protetto)
# ============================================================
DISTRICTS = {
    "Distretto 1": {
        "gradiente": "linear-gradient(135deg, #6b5108 0%, #b8952e 50%, #f0dfa0 100%)",
        "rgb_top": (107, 81, 8),
        "rgb_bottom": (240, 223, 160),
        "emoji": "💎",
        "descrizione": "Sei cresciuto per vincere. La competizione ti motiva più di ogni altra cosa, e raramente dubiti delle tue capacità.",
        "dettagli": [
            ("Industria", "Beni di lusso e gioielli"),
            ("Simbolo", "Diamante"),
            ("Colori", "Oro e avorio"),
            ("Tributi noti", "Glimmer, Marvel"),
            ("Valori", "Ambizione, competitività, sicurezza di sé"),
        ],
    },
    "Distretto 2": {
        "gradiente": "linear-gradient(135deg, #2b2b2b 0%, #5a1414 50%, #8a2020 100%)",
        "rgb_top": (43, 43, 43),
        "rgb_bottom": (138, 32, 32),
        "emoji": "⛏️",
        "descrizione": "Ti sei allenato tutta la vita per essere pronto a qualsiasi sfida. La disciplina è la tua corazza.",
        "dettagli": [
            ("Industria", "Cave di pietra e addestramento"),
            ("Simbolo", "Martello e piccone incrociati"),
            ("Colori", "Grigio pietra e rosso"),
            ("Tributi noti", "Cato, Clove"),
            ("Valori", "Forza, disciplina, addestramento rigoroso"),
        ],
    },
    "Distretto 3": {
        "gradiente": "linear-gradient(135deg, #1c2128 0%, #384a5c 50%, #6fa3c9 100%)",
        "rgb_top": (28, 33, 40),
        "rgb_bottom": (111, 163, 201),
        "emoji": "⚙️",
        "descrizione": "La tua mente lavora come un meccanismo perfetto: precisa, metodica, sempre un passo avanti nel trovare soluzioni che nessun altro vede.",
        "dettagli": [
            ("Industria", "Elettronica e tecnologia"),
            ("Simbolo", "Ingranaggio e circuito"),
            ("Colori", "Grigio metallizzato e blu elettrico"),
            ("Tributi noti", "Beetee, Wiress"),
            ("Valori", "Ingegno, precisione, pensiero laterale"),
        ],
    },
    "Distretto 4": {
        "gradiente": "linear-gradient(135deg, #063a42 0%, #157a8a 50%, #6ec6d4 100%)",
        "rgb_top": (6, 58, 66),
        "rgb_bottom": (110, 198, 212),
        "emoji": "🎣",
        "descrizione": "Ti muovi con la stessa naturalezza di chi è cresciuto tra le onde: capace di adattarti a ogni corrente, ma con radici profonde.",
        "dettagli": [
            ("Industria", "Pesca e prodotti del mare"),
            ("Simbolo", "Rete e tridente"),
            ("Colori", "Turchese e argento"),
            ("Tributi noti", "Finnick Odair, Annie Cresta"),
            ("Valori", "Adattabilità, fascino, resistenza silenziosa"),
        ],
    },
    "Distretto 5": {
        "gradiente": "linear-gradient(135deg, #3a3418 0%, #7a6d1e 50%, #c9b93c 100%)",
        "rgb_top": (58, 52, 24),
        "rgb_bottom": (201, 185, 60),
        "emoji": "🔌",
        "descrizione": "Ti muovi silenziosamente, osservando tutto prima di agire. La tua intelligenza pratica ti permette di sopravvivere senza mai esporti troppo.",
        "dettagli": [
            ("Industria", "Produzione di energia elettrica"),
            ("Simbolo", "Fulmine stilizzato"),
            ("Colori", "Giallo e grigio industriale"),
            ("Tributi noti", "Foxface (la ragazza dal volto di volpe)"),
            ("Valori", "Intuito, prudenza, autosufficienza"),
        ],
    },
    "Distretto 7": {
        "gradiente": "linear-gradient(135deg, #14200e 0%, #355c26 50%, #6e9b4f 100%)",
        "rgb_top": (20, 32, 14),
        "rgb_bottom": (110, 155, 79),
        "emoji": "🪓",
        "descrizione": "Dietro un'apparenza ruvida nascondi una mente scaltra. Non sottovalutare mai chi sembra il più debole della stanza: potrebbe essere tu.",
        "dettagli": [
            ("Industria", "Taglio del legname"),
            ("Simbolo", "Ascia"),
            ("Colori", "Verde bosco e marrone"),
            ("Tributi noti", "Johanna Mason"),
            ("Valori", "Resistenza, astuzia nascosta, indipendenza"),
        ],
    },
    "Distretto 8": {
        "gradiente": "linear-gradient(135deg, #2e1a38 0%, #5e3970 50%, #a97fc0 100%)",
        "rgb_top": (46, 26, 56),
        "rgb_bottom": (169, 127, 192),
        "emoji": "🧵",
        "descrizione": "Trasformi la fatica in qualcosa di bello. Dietro un lavoro spesso invisibile agli altri, nascondi una creatività capace di lasciare il segno.",
        "dettagli": [
            ("Industria", "Produzione tessile"),
            ("Simbolo", "Telaio e spola"),
            ("Colori", "Viola e grigio perla"),
            ("Tributi noti", "Cinna (stilista originario del Distretto 8)"),
            ("Valori", "Creatività, resistenza silenziosa, senso estetico"),
        ],
    },
    "Distretto 11": {
        "gradiente": "linear-gradient(135deg, #2e2a0a 0%, #6b5f1a 50%, #a8973c 100%)",
        "rgb_top": (46, 42, 10),
        "rgb_bottom": (168, 151, 60),
        "emoji": "🌾",
        "descrizione": "Il senso di comunità è la tua bussola. Proteggi gli altri con una lealtà silenziosa ma incrollabile.",
        "dettagli": [
            ("Industria", "Agricoltura su larga scala"),
            ("Simbolo", "Spiga di grano"),
            ("Colori", "Verde oliva e ocra"),
            ("Tributi noti", "Rue, Thresh"),
            ("Valori", "Comunità, gentilezza, forza silenziosa"),
        ],
    },
    "Distretto 12": {
        "gradiente": "linear-gradient(135deg, #0a0a0a 0%, #2e2e30 50%, #5a5a5e 100%)",
        "rgb_top": (10, 10, 10),
        "rgb_bottom": (90, 90, 94),
        "emoji": "🔥",
        "descrizione": "Hai imparato a sopravvivere con poco, e questo ti ha reso più forte di quanto immagini. Per le persone che ami, saresti pronto a tutto.",
        "dettagli": [
            ("Industria", "Estrazione del carbone"),
            ("Simbolo", "Fiamma"),
            ("Colori", "Nero antracite e grigio"),
            ("Tributi noti", "Katniss Everdeen, Peeta Mellark"),
            ("Valori", "Sopravvivenza, sacrificio, resilienza"),
        ],
    },
}

QUESTIONS_HG = [
    {
        "domanda": "Il giorno della Mietitura, il tuo nome viene chiamato ad alta voce. Qual è il tuo primo pensiero?",
        "opzioni": [
            ("È la mia occasione per brillare davanti a tutti", {"Distretto 1": 1}),
            ("Sono pronto: mi sono allenato tutta la vita per questo momento", {"Distretto 2": 1}),
            ("Comincio subito a valutare ogni scenario possibile, con lucidità", {"Distretto 3": 1}),
            ("Penso a come dovrò adattarmi in fretta a un ambiente che non conosco", {"Distretto 4": 1}),
        ],
    },
    {
        "domanda": "Sei nell'arena e trovi la Cornucopia piena di rifornimenti. Cosa fai?",
        "opzioni": [
            ("Osservo tutto da lontano prima di avvicinarmi, senza fretta", {"Distretto 5": 1}),
            ("Aspetto in disparte, osservando chi si fida meno degli altri", {"Distretto 7": 1}),
            ("Cerco qualcosa di utile ma non essenziale, senza rischiare troppo", {"Distretto 8": 1}),
            ("Penso prima a chi potrebbe avere più bisogno di me di un oggetto", {"Distretto 11": 1}),
        ],
    },
    {
        "domanda": "Un alleato ti tradisce nel momento del bisogno. Come reagisci?",
        "opzioni": [
            ("Trovo comunque la forza di andare avanti da solo", {"Distretto 12": 1}),
            ("Mi infastidisco, ma me lo aspettavo: l'alleanza serve solo finché conviene", {"Distretto 1": 1}),
            ("Non mi lascio destabilizzare: continuo secondo il mio addestramento", {"Distretto 2": 1}),
            ("Analizzo a freddo cosa questo cambia per il resto del mio piano", {"Distretto 3": 1}),
        ],
    },
    {
        "domanda": "Qual è la tua strategia preferita per sopravvivere?",
        "opzioni": [
            ("Adattarmi rapidamente a qualsiasi ambiente mi capiti", {"Distretto 4": 1}),
            ("Restare defilato, osservare tutto, muovermi solo quando serve", {"Distretto 5": 1}),
            ("Restare nell'ombra finché non è il momento di colpire", {"Distretto 7": 1}),
            ("Costruire con pazienza qualcosa di utile con le mie mani", {"Distretto 8": 1}),
        ],
    },
    {
        "domanda": "Cosa temi di più, in fondo?",
        "opzioni": [
            ("Non riuscire a proteggere chi ha bisogno di me", {"Distretto 11": 1}),
            ("Non riuscire a proteggere le persone che amo", {"Distretto 12": 1}),
            ("Essere dimenticato o considerato non abbastanza forte", {"Distretto 1": 1}),
            ("Fallire dopo essermi allenato per tutta la vita", {"Distretto 2": 1}),
        ],
    },
    {
        "domanda": "Come ti comporti davanti alle telecamere, durante le interviste?",
        "opzioni": [
            ("Rispondo in modo calcolato, senza rivelare troppo", {"Distretto 3": 1}),
            ("Cerco di essere carismatico, ma senza scoprire troppo di me", {"Distretto 4": 1}),
            ("Parlo il minimo indispensabile, resto sfuggente", {"Distretto 5": 1}),
            ("Lascio che gli altri mi sottovalutino: mi conviene", {"Distretto 7": 1}),
        ],
    },
    {
        "domanda": "Il tuo più grande punto di forza è...",
        "opzioni": [
            ("La pazienza e la cura nei dettagli", {"Distretto 8": 1}),
            ("La capacità di ispirare fiducia negli altri", {"Distretto 11": 1}),
            ("La resilienza: resisto anche quando tutto sembra perduto", {"Distretto 12": 1}),
            ("Il fascino e la sicurezza che trasmetto agli altri", {"Distretto 1": 1}),
        ],
    },
    {
        "domanda": "Trovi cibo scarso nell'arena. Cosa fai?",
        "opzioni": [
            ("Vado a caccia attivamente, senza aspettare", {"Distretto 2": 1}),
            ("Costruisco una trappola calcolata con quello che ho a disposizione", {"Distretto 3": 1}),
            ("Mi affido all'istinto per trovare una fonte d'acqua o cibo vicina", {"Distretto 4": 1}),
            ("Razziono con attenzione quello che ho, senza sprechi", {"Distretto 5": 1}),
        ],
    },
    {
        "domanda": "Cosa ti motiva davvero a lottare fino alla fine?",
        "opzioni": [
            ("Dimostrare che chi sembra debole può sorprendere tutti", {"Distretto 7": 1}),
            ("Il desiderio di tornare a creare qualcosa di mio", {"Distretto 8": 1}),
            ("Le persone della mia comunità che contano su di me", {"Distretto 11": 1}),
            ("Le persone a cui voglio bene, a casa", {"Distretto 12": 1}),
        ],
    },
    {
        "domanda": "Come scegli i tuoi alleati?",
        "opzioni": [
            ("Cerco chi può portarmi un vantaggio concreto", {"Distretto 1": 1}),
            ("Valuto con attenzione chi ha competenze complementari alle mie", {"Distretto 3": 1}),
            ("Mi fido raramente: preferisco contare soprattutto su me stesso", {"Distretto 5": 1}),
            ("Cerco chi condivide la mia stessa pazienza e lealtà", {"Distretto 8": 1}),
        ],
    },
    {
        "domanda": "Qual è il tuo rapporto con le regole imposte dall'alto?",
        "opzioni": [
            ("Le seguo con disciplina: mi sono allenato per questo", {"Distretto 2": 1}),
            ("Le rispetto, ma so adattarmi se la situazione cambia", {"Distretto 4": 1}),
            ("Le aggiro silenziosamente, senza farmi notare", {"Distretto 7": 1}),
            ("Le rispetto se proteggono la mia comunità, altrimenti no", {"Distretto 11": 1}),
        ],
    },
    {
        "domanda": "Se sopravvivessi ai Giochi, cosa faresti per primo?",
        "opzioni": [
            ("Proteggerei chi amo, più fermamente di prima", {"Distretto 12": 1}),
            ("Godrei del riconoscimento che ho conquistato", {"Distretto 1": 1}),
            ("Cercherei un posto tranquillo, lontano dai riflettori", {"Distretto 5": 1}),
            ("Tornerei a creare qualcosa di bello con le mie mani", {"Distretto 8": 1}),
        ],
    },
]


# ============================================================
# DATI — CREATORE DI PERSONAGGIO (elementi originali per ogni
# mondo: tratti, oggetti, alleati; l'affiliazione finale viene
# scelta tra le entità già definite sopra per ciascun mondo)
# ============================================================
CREATOR_DATA = {
    "hogwarts": {
        "titolo": "Crea il tuo Mago",
        "eyebrow": "IL MINISTERO DELLA MAGIA REGISTRA UN NUOVO STREGONE",
        "tratti": ["Coraggioso", "Astuto", "Leale", "Curioso", "Ambizioso", "Gentile", "Ribelle", "Studioso"],
        "oggetti": ["Una bacchetta di legno di sorbo", "Un mantello dell'invisibilità di famiglia",
                    "Un giratempo dimenticato in soffitta", "Uno specchio che rivela le emozioni",
                    "Una scopa da corsa arrugginita ma veloce", "Un calderone che ribolle da solo"],
        "alleati": ["Un gufo messaggero fedele", "Un gatto dagli occhi dorati", "Un piccolo drago addomesticato",
                    "Un elfo domestico devoto", "Una fenice compagna", "Un ippogrifo leale"],
        "entita": HOUSES,
        "gradiente_default": "linear-gradient(135deg, #1c140b 0%, #4a2f0e 50%, #8a6a12 100%)",
        "rgb_top": (28, 20, 11),
        "rgb_bottom": (138, 106, 18),
        "font_titolo": "titolo_hp",
    },
    "percy": {
        "titolo": "Crea il tuo Semidio",
        "eyebrow": "IL CAMPO MEZZOSANGUE ACCOGLIE UN NUOVO CAMPISTA",
        "tratti": ["Coraggioso", "Leale", "Astuto", "Impulsivo", "Protettivo", "Curioso", "Ironico", "Determinato"],
        "oggetti": ["Una spada di bronzo celeste", "Uno scudo inciso con simboli antichi",
                    "Un arco che non manca mai il bersaglio", "Un pugnale forgiato nell'ombra",
                    "Un amuleto di protezione", "Un paio di sandali alati"],
        "alleati": ["Un satiro esploratore", "Una ninfa dei boschi", "Un cane infernale addomesticato",
                    "Un pegaso fedele", "Uno spirito guida silenzioso", "Un compagno semidio inseparabile"],
        "entita": GODS,
        "gradiente_default": "linear-gradient(135deg, #060d24 0%, #0e1a40 50%, #2b4a8c 100%)",
        "rgb_top": (6, 13, 36),
        "rgb_bottom": (43, 74, 140),
        "font_titolo": "titolo_pj",
    },
    "divergent": {
        "titolo": "Crea il tuo Iniziato",
        "eyebrow": "LA CERIMONIA DELLA SCELTA ACCOGLIE UN NUOVO INIZIATO",
        "tratti": ["Altruista", "Coraggioso", "Intelligente", "Onesto", "Pacifico", "Ambizioso", "Leale", "Indipendente"],
        "oggetti": ["Un coltello da lancio perfettamente bilanciato", "Una giacca corazzata",
                    "Un manuale di simulazioni", "Un walkie-talkie di fazione",
                    "Un diario segreto", "Un paio di scarpe da salto"],
        "alleati": ["Un compagno di addestramento fidato", "Un mentore severo ma giusto",
                    "Un amico d'infanzia leale", "Un informatore misterioso",
                    "Un istruttore Intrepido", "Un alleato Erudito"],
        "entita": DIVERGENT,
        "gradiente_default": "linear-gradient(135deg, #0d1114 0%, #2b3238 50%, #4a555e 100%)",
        "rgb_top": (13, 17, 20),
        "rgb_bottom": (74, 85, 94),
        "font_titolo": "titolo_div",
    },
    "hunger": {
        "titolo": "Crea il tuo Tributo",
        "eyebrow": "IL CAMPIDOGLIO PRESENTA UN NUOVO TRIBUTO",
        "tratti": ["Resiliente", "Astuto", "Leale", "Silenzioso", "Carismatico", "Protettivo", "Calcolatore", "Coraggioso"],
        "oggetti": ["Un arco con faretra", "Un coltello da lancio", "Una rete da pesca",
                    "Un kit di erbe medicinali", "Una fionda", "Un mantello mimetico"],
        "alleati": ["Un tributo alleato fidato", "Un mentore esperto", "Uno sponsor misterioso",
                    "Un compagno di distretto", "Una guida silenziosa", "Un animale della foresta addomesticato"],
        "entita": DISTRICTS,
        "gradiente_default": "linear-gradient(135deg, #0c0f08 0%, #2c3322 50%, #6b7a4a 100%)",
        "rgb_top": (12, 15, 8),
        "rgb_bottom": (107, 122, 74),
        "font_titolo": "titolo_hg",
    },
}


# ============================================================
# DATI — SOPRAVVIVENZA NELL'ARENA (Hunger Games)
# Simulatore narrativo a bivi originale, non testo protetto.
# Ogni scelta modifica salute e provviste; se la salute crolla
# a zero il tributo viene eliminato prima della fine dei giorni.
# ============================================================
GIORNI_ARENA = [
    {
        "situazione": "Il gong suona e la Cornucopia è a pochi passi, circondata da rifornimenti e altri tributi pronti a scattare. Cosa fai?",
        "scelte": [
            ("Mi fiondo al centro per prendere il massimo possibile, rischiando lo scontro", {"salute": -15, "provviste": 25}),
            ("Scappo subito verso la foresta, senza rischiare nulla", {"salute": 0, "provviste": 0}),
            ("Prendo solo ciò che è alla portata sul bordo, senza avvicinarmi troppo", {"salute": -3, "provviste": 10}),
        ],
    },
    {
        "situazione": "Trovi una fonte d'acqua, ma un altro tributo sembra sorvegliarla in agguato tra i cespugli. Cosa fai?",
        "scelte": [
            ("Lo affronto apertamente per avere via libera", {"salute": -15, "provviste": 15}),
            ("Aspetto nascosto che si allontani", {"salute": 0, "provviste": 5}),
            ("Cerco un'altra fonte d'acqua più lontana e sicura", {"salute": -5, "provviste": -5}),
        ],
    },
    {
        "situazione": "Incontri un altro tributo, ferito e disarmato, che non sembra una minaccia. Cosa fai?",
        "scelte": [
            ("Lo aiuto, condividendo parte delle mie provviste", {"salute": 0, "provviste": -15}),
            ("Lo ignoro e proseguo per la mia strada", {"salute": 0, "provviste": 0}),
            ("Ne approfitto per recuperare il suo equipaggiamento", {"salute": 0, "provviste": 12}),
        ],
    },
    {
        "situazione": "Di notte scoppia un violento temporale scatenato dai Game Maker. Come reagisci?",
        "scelte": [
            ("Cerco subito un riparo sicuro, anche se mi costa tempo e provviste", {"salute": 8, "provviste": -10}),
            ("Continuo a muovermi per non perdere terreno prezioso", {"salute": -12, "provviste": -5}),
            ("Mi rannicchio dove sono, risparmiando le forze", {"salute": -5, "provviste": 0}),
        ],
    },
    {
        "situazione": "Le provviste iniziano a scarseggiare e la fame si fa sentire. Cosa fai?",
        "scelte": [
            ("Vado a caccia, rischiando di essere scoperto dagli altri tributi", {"salute": -10, "provviste": 20}),
            ("Razioni quello che hai e aspetti un momento più sicuro", {"salute": -5, "provviste": -8}),
            ("Mandi un segnale nella speranza che uno sponsor ti aiuti", {"salute": 0, "provviste": 12}),
        ],
    },
    {
        "situazione": "È rimasto solo un pugno di tributi. Il gong finale sta per suonare. Come affronti l'ultimo scontro?",
        "scelte": [
            ("Affronto l'ultimo avversario a viso aperto", {"salute": -20, "provviste": 0}),
            ("Tendo un'imboscata strategica, sfruttando il terreno", {"salute": -10, "provviste": 0}),
            ("Aspetto in disparte che gli altri si eliminino a vicenda", {"salute": -5, "provviste": 0}),
        ],
    },
]


# ============================================================
# DATI — MAPPE INTERATTIVE (punti d'interesse per ogni mondo:
# dettagli fattuali dell'universo narrativo, non testo protetto)
# ============================================================
MAP_POIS = {
    "hogwarts": {
        "titolo": "Mappa di Hogwarts",
        "eyebrow": "\"Giuro solennemente di non avere buone intenzioni...\"",
        "stile_card": "parchment",
        "font_titolo_css": "hat-title",
        "luoghi": [
            {"slug": "salone", "nome": "La Sala Grande", "x": 130, "y": 120,
             "desc": "Cuore pulsante del castello: qui si consumano i pasti sotto un soffitto incantato che riflette il cielo reale, e si tengono le grandi cerimonie come lo Smistamento."},
            {"slug": "biblioteca", "nome": "La Biblioteca", "x": 400, "y": 90,
             "desc": "Una sterminata raccolta di libri e pergamene magiche, custodita con rigore. Alcune sezioni, quelle più pericolose, sono accessibili solo con permesso speciale."},
            {"slug": "foresta", "nome": "La Foresta Proibita", "x": 620, "y": 220,
             "desc": "Un bosco fitto e oscuro ai confini della scuola, rifugio di creature magiche potenti e imprevedibili. Gli studenti non possono entrarvi senza autorizzazione."},
            {"slug": "quidditch", "nome": "Il Campo di Quidditch", "x": 250, "y": 300,
             "desc": "Un ampio campo ovale dove si disputano le partite tra le quattro case, seguite dall'intera scuola dagli spalti."},
            {"slug": "torre", "nome": "La Torre di Astronomia", "x": 520, "y": 60,
             "desc": "Il punto più alto del castello, usato per le lezioni di osservazione del cielo notturno e raggiungibile da una lunga scalinata a chiocciola."},
        ],
    },
    "percy": {
        "titolo": "Mappa del Campo Mezzosangue",
        "eyebrow": "\"Non è sicuro per un semidio restare fermo troppo a lungo.\"",
        "stile_card": "marble",
        "font_titolo_css": "camp-title",
        "luoghi": [
            {"slug": "casa_grande", "nome": "La Casa Grande", "x": 400, "y": 100,
             "desc": "Sede amministrativa del campo, dove risiedono gli istruttori e si tengono le riunioni più importanti tra i capicampo."},
            {"slug": "arena", "nome": "L'Arena di Combattimento", "x": 160, "y": 200,
             "desc": "Uno spazio a cielo aperto dedicato all'addestramento con la spada e le altre armi, sorvegliato dagli istruttori più esperti."},
            {"slug": "bosco", "nome": "Il Bosco", "x": 620, "y": 160,
             "desc": "Un'ampia area selvaggia dove i campisti affrontano prove pratiche e, talvolta, creature mitologiche vere e proprie."},
            {"slug": "spiaggia", "nome": "La Spiaggia", "x": 300, "y": 320,
             "desc": "Il tratto di costa dove il campo si affaccia sul mare, territorio in cui l'influenza di Poseidone si fa sentire più forte."},
            {"slug": "cabine", "nome": "Le Cabine", "x": 500, "y": 280,
             "desc": "L'area residenziale del campo, con un edificio dedicato a ciascun dio dell'Olimpo che ha figli tra i campisti."},
        ],
    },
    "divergent": {
        "titolo": "Mappa della Città delle Fazioni",
        "eyebrow": "\"Fazione prima del sangue.\"",
        "stile_card": "steel",
        "font_titolo_css": "steel-title",
        "luoghi": [
            {"slug": "erudito", "nome": "Il Quartier Erudito", "x": 150, "y": 100,
             "desc": "Un complesso di biblioteche e laboratori dove gli Eruditi conducono ricerche e conservano il sapere della città."},
            {"slug": "pozzo", "nome": "Il Pozzo", "x": 420, "y": 90,
             "desc": "L'ingresso sotterraneo al quartiere Intrepido, raggiungibile solo con un salto nel vuoto per i nuovi iniziati."},
            {"slug": "recinto", "nome": "Il Recinto", "x": 620, "y": 240,
             "desc": "Il confine esterno della città, pattugliato e mantenuto dagli Abneganti per proteggere chi vive all'interno."},
            {"slug": "tribunale", "nome": "Il Tribunale", "x": 300, "y": 300,
             "desc": "L'edificio bianco e nero dove i Candidi amministrano la giustizia, basandosi sulla ricerca collettiva della verità."},
            {"slug": "frutteti", "nome": "I Frutteti", "x": 500, "y": 340,
             "desc": "Le terre agricole coltivate dai Pacifici, fuori dal centro città, fonte di gran parte del cibo della comunità."},
        ],
    },
    "hunger": {
        "titolo": "Mappa di Panem",
        "eyebrow": "\"Che le probabilità siano sempre a tuo favore.\"",
        "stile_card": "canvas",
        "font_titolo_css": "arena-title",
        "luoghi": [
            {"slug": "capitol", "nome": "Il Campidoglio", "x": 400, "y": 80,
             "desc": "Il cuore politico e amministrativo di Panem, sede del governo centrale e dei fasti mostrati durante i Giochi."},
            {"slug": "arena", "nome": "L'Arena", "x": 180, "y": 180,
             "desc": "Il teatro artificiale costruito ogni anno per ospitare i Giochi, con un ambiente e delle regole sempre diverse."},
            {"slug": "villaggio", "nome": "Il Villaggio dei Vincitori", "x": 620, "y": 200,
             "desc": "Un quartiere di case riservate a chi ha vinto i Giochi in passato, situato ai margini del proprio distretto natale."},
            {"slug": "miniera", "nome": "La Miniera di Carbone", "x": 280, "y": 320,
             "desc": "Il cuore industriale del Distretto 12, dove gran parte della popolazione lavora in condizioni durissime."},
            {"slug": "giustizia", "nome": "Il Palazzo di Giustizia", "x": 500, "y": 300,
             "desc": "L'edificio principale di ogni distretto, dove si svolge la cerimonia della Mietitura ogni anno."},
        ],
    },
}



# ============================================================
# CSS GLOBALE — sfondo condiviso + due identità tipografiche
# (pergamena/Hogwarts e marmo/Olimpo)
# ============================================================
st.markdown(
    textwrap.dedent("""\
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700&family=Cinzel+Decorative:wght@700;900&family=EB+Garamond:ital,wght@0,400;0,600;1,400&family=IM+Fell+English:ital@0;1&family=Lora:ital,wght@0,500;1,500&family=IBM+Plex+Mono:wght@500&family=Barlow+Condensed:wght@600;700&family=Barlow:ital,wght@0,400;1,400&family=Philosopher:wght@700&family=Bebas+Neue&family=Crimson+Text:ital@0;1&display=swap');

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

    .steel-title {
        font-family: 'Barlow Condensed', sans-serif;
        font-weight: 700;
        font-size: 2.8rem;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 4px;
        color: #d8dde2;
        text-shadow: 0 0 20px rgba(120,140,160,0.35);
        margin-bottom: 0;
    }
    .steel-subtitle {
        font-family: 'Barlow', sans-serif;
        font-style: italic;
        text-align: center;
        color: #8a95a0;
        font-size: 1rem;
        margin-top: -6px;
        margin-bottom: 1.4rem;
        letter-spacing: 0.5px;
    }
    .steel {
        background:
            repeating-linear-gradient(135deg, rgba(255,255,255,0.02) 0px, rgba(255,255,255,0.02) 2px, transparent 2px, transparent 14px),
            linear-gradient(135deg, #2b3238 0%, #3a434b 50%, #4a555e 100%);
        border: 1px solid #6b7680;
        outline: 6px solid #0d1114;
        outline-offset: -12px;
        border-radius: 2px;
        padding: 2rem 2.2rem;
        box-shadow: 0 15px 45px rgba(0,0,0,0.6), inset 0 0 40px rgba(0,0,0,0.35);
        color: #e4e8eb;
        margin-bottom: 1.4rem;
    }
    .steel h3 {
        font-family: 'Barlow Condensed', sans-serif;
        font-weight: 700;
        font-size: 1.3rem;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #e4e8eb;
        border-bottom: 1px solid #6b7680;
        padding-bottom: 8px;
        margin-top: 0;
    }
    .qcounter.steel {
        font-family: 'IBM Plex Mono', monospace;
        font-style: normal;
        letter-spacing: 2px;
        text-transform: uppercase;
        font-size: 0.8rem;
        color: #8a95a0;
    }
    .result-house.steel {
        font-family: 'Barlow Condensed', sans-serif;
        font-weight: 700;
        letter-spacing: 3px;
        text-transform: uppercase;
        font-size: 2.2rem;
    }
    .result-desc.steel {
        font-family: 'Barlow', sans-serif;
        font-style: italic;
    }
    .fact-label.steel {
        font-family: 'IBM Plex Mono', monospace;
        font-style: normal;
        letter-spacing: 1px;
        text-transform: uppercase;
        font-size: 0.7rem;
    }

    .nexus-title {
        font-family: 'Philosopher', sans-serif;
        font-weight: 700;
        font-size: 2.7rem;
        text-align: center;
        letter-spacing: 2px;
        background: linear-gradient(90deg, #f3d98b 0%, #7fc7d9 50%, #e08a3c 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 30px rgba(255,255,255,0.15);
        margin-bottom: 0;
    }
    .nexus-subtitle {
        font-family: 'IBM Plex Mono', monospace;
        text-align: center;
        color: #b8b6c9;
        font-size: 0.85rem;
        letter-spacing: 2.5px;
        text-transform: uppercase;
        margin-top: -4px;
        margin-bottom: 0.6rem;
    }

    .arena-title {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 3.2rem;
        text-align: center;
        letter-spacing: 3px;
        color: #e0995c;
        text-shadow: 0 0 22px rgba(224,153,92,0.4), 0 2px 4px rgba(0,0,0,0.6);
        margin-bottom: 0;
    }
    .arena-subtitle {
        font-family: 'Crimson Text', serif;
        font-style: italic;
        text-align: center;
        color: #9fae95;
        font-size: 1.05rem;
        margin-top: -6px;
        margin-bottom: 1.4rem;
        letter-spacing: 0.3px;
    }
    .canvas {
        background:
            radial-gradient(circle at 20% 20%, rgba(90,110,70,0.35), transparent 45%),
            radial-gradient(circle at 80% 70%, rgba(60,50,30,0.4), transparent 50%),
            linear-gradient(135deg, #3a4230 0%, #2c3322 50%, #241f16 100%);
        border: 1px solid #6b7a4a;
        outline: 6px solid #120d08;
        outline-offset: -12px;
        border-radius: 2px;
        padding: 2rem 2.2rem;
        box-shadow: 0 15px 45px rgba(0,0,0,0.6), inset 0 0 45px rgba(0,0,0,0.4);
        color: #e6e4d4;
        margin-bottom: 1.4rem;
    }
    .canvas h3 {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.5rem;
        letter-spacing: 2px;
        color: #e0995c;
        border-bottom: 1px solid #6b7a4a;
        padding-bottom: 8px;
        margin-top: 0;
    }
    .qcounter.arena {
        font-family: 'IBM Plex Mono', monospace;
        font-style: normal;
        letter-spacing: 2px;
        text-transform: uppercase;
        font-size: 0.8rem;
        color: #9fae95;
    }
    .result-house.arena {
        font-family: 'Bebas Neue', sans-serif;
        letter-spacing: 3px;
        font-size: 2.6rem;
    }
    .result-desc.arena {
        font-family: 'Crimson Text', serif;
        font-style: italic;
    }
    .fact-label.arena {
        font-family: 'IBM Plex Mono', monospace;
        font-style: normal;
        letter-spacing: 1px;
        text-transform: uppercase;
        font-size: 0.7rem;
    }
    .menu-card-title.arena {
        font-family: 'Bebas Neue', sans-serif;
        letter-spacing: 2px;
        font-size: 1.5rem;
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


def render_steel_background():
    st.markdown(
        textwrap.dedent("""\
        <style>
        .stApp {
            background:
                repeating-linear-gradient(0deg, rgba(255,255,255,0.015) 0px, rgba(255,255,255,0.015) 1px, transparent 1px, transparent 3px),
                radial-gradient(ellipse at top left, rgba(90,110,130,0.25), transparent 55%),
                radial-gradient(ellipse at bottom right, rgba(40,50,60,0.4), transparent 60%),
                linear-gradient(180deg, #0d1114 0%, #171c20 45%, #0d1114 100%) !important;
            background-attachment: fixed !important;
        }
        </style>
        """),
        unsafe_allow_html=True,
    )


def render_nexus_background():
    st.markdown(
        textwrap.dedent("""\
        <style>
        .stApp {
            background:
                radial-gradient(circle at 18% 22%, rgba(243,217,139,0.14), transparent 38%),
                radial-gradient(circle at 82% 28%, rgba(63,151,173,0.18), transparent 38%),
                radial-gradient(circle at 50% 85%, rgba(224,138,60,0.14), transparent 42%),
                radial-gradient(circle, rgba(255,255,255,0.9) 1px, transparent 1.5px) 0 0/160px 160px,
                radial-gradient(circle, rgba(255,255,255,0.55) 1px, transparent 1.5px) 55px 70px/190px 190px,
                radial-gradient(circle, rgba(255,255,255,0.4) 1px, transparent 1.5px) 100px 30px/220px 220px,
                linear-gradient(180deg, #05060f 0%, #0b0a1a 50%, #05060f 100%) !important;
            background-attachment: fixed !important;
        }
        </style>
        """),
        unsafe_allow_html=True,
    )


def render_nexus_emblem():
    svg_code = textwrap.dedent("""\
    <div style="display:flex; justify-content:center; margin: 0.2rem 0 1.6rem;">
    <svg width="210" height="170" viewBox="0 0 210 170" xmlns="http://www.w3.org/2000/svg">
    <g style="animation: nexus-rotate 34s linear infinite; transform-origin: 105px 92px;" opacity="0.5">
    <circle cx="105" cy="14" r="2" fill="#ffffff"/>
    <circle cx="197" cy="92" r="2" fill="#ffffff"/>
    <circle cx="105" cy="170" r="2" fill="#ffffff"/>
    <circle cx="13" cy="92" r="2" fill="#ffffff"/>
    </g>
    <g style="mix-blend-mode: screen;">
    <circle cx="72" cy="100" r="52" fill="#f3d98b" opacity="0.45"/>
    <circle cx="138" cy="100" r="52" fill="#3f97ad" opacity="0.45"/>
    <circle cx="105" cy="55" r="52" fill="#e08a3c" opacity="0.45"/>
    </g>
    <circle cx="72" cy="100" r="52" fill="none" stroke="#f3d98b" stroke-width="1.2" opacity="0.7"/>
    <circle cx="138" cy="100" r="52" fill="none" stroke="#7fc7d9" stroke-width="1.2" opacity="0.7"/>
    <circle cx="105" cy="55" r="52" fill="none" stroke="#e08a3c" stroke-width="1.2" opacity="0.7"/>
    <circle cx="105" cy="88" r="9" fill="#ffffff" opacity="0.9">
    <animate attributeName="opacity" values="0.6;1;0.6" dur="3s" repeatCount="indefinite"/>
    </circle>
    </svg>
    </div>
    <style>
    @keyframes nexus-rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    </style>
    """)
    st.markdown(svg_code, unsafe_allow_html=True)


def render_faction_wheel():
    svg_code = textwrap.dedent("""\
    <div style="display:flex; justify-content:center; margin: 0.4rem 0 1.6rem;">
    <svg width="190" height="190" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
    <defs>
    <radialGradient id="glow3" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#d8dde2" stop-opacity="0.85"/>
    <stop offset="100%" stop-color="#d8dde2" stop-opacity="0"/>
    </radialGradient>
    </defs>
    <g stroke="#0d1114" stroke-width="2">
    <path d="M100,100 L100,10 L185.6,72.2 Z" fill="#6b6b70"/>
    <path d="M100,100 L185.6,72.2 L152.9,172.8 Z" fill="#1d3f6b"/>
    <path d="M100,100 L152.9,172.8 L47.1,172.8 Z" fill="#201010"/>
    <path d="M100,100 L47.1,172.8 L14.4,72.2 Z" fill="#8a4a12"/>
    <path d="M100,100 L14.4,72.2 L100,10 Z" fill="#3a3a3a"/>
    </g>
    <circle cx="65" cy="55" r="6" fill="none" stroke="#d8dde2" stroke-width="2" opacity="0.8"/>
    <ellipse cx="150" cy="105" rx="9" ry="5" fill="none" stroke="#9fc2ea" stroke-width="2" opacity="0.85"/>
    <circle cx="150" cy="105" r="2" fill="#9fc2ea"/>
    <path d="M92,155 q8,-16 0,-28 q10,4 8,18 q6,-6 4,4 q-6,4 -12,6 Z" fill="#e0995c" opacity="0.85"/>
    <path d="M35,140 q0,-16 12,-20 q4,10 -4,18 q8,-2 2,8 q-6,2 -10,-6 Z" fill="#e0c04a" opacity="0.85"/>
    <line x1="45" y1="60" x2="65" y2="60" stroke="#d8dde2" stroke-width="2" opacity="0.85"/>
    <line x1="55" y1="60" x2="55" y2="45" stroke="#d8dde2" stroke-width="2" opacity="0.85"/>
    <circle cx="100" cy="100" r="32" fill="url(#glow3)">
    <animate attributeName="r" values="28;34;28" dur="3.5s" repeatCount="indefinite"/>
    </circle>
    <circle cx="100" cy="100" r="24" fill="#0d1114" stroke="#d8dde2" stroke-width="2"/>
    <path d="M100,86 L110,100 L100,114 L90,100 Z" fill="none" stroke="#d8dde2" stroke-width="2"/>
    </svg>
    </div>
    """)
    st.markdown(svg_code, unsafe_allow_html=True)


def render_arena_background():
    st.markdown(
        textwrap.dedent("""\
        <style>
        .stApp {
            background:
                radial-gradient(ellipse at top, rgba(224,153,92,0.14), transparent 50%),
                radial-gradient(ellipse at bottom left, rgba(60,80,45,0.35), transparent 55%),
                linear-gradient(180deg, #0c0f08 0%, #161d10 45%, #0c0f08 100%) !important;
            background-attachment: fixed !important;
        }
        </style>
        """),
        unsafe_allow_html=True,
    )


def render_arena_compass():
    svg_code = textwrap.dedent("""\
    <div style="display:flex; justify-content:center; margin: 0.4rem 0 1.6rem;">
    <svg width="190" height="190" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
    <defs>
    <radialGradient id="glow4" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#e0995c" stop-opacity="0.9"/>
    <stop offset="100%" stop-color="#e0995c" stop-opacity="0"/>
    </radialGradient>
    </defs>
    <g style="animation: arena-rotate 40s linear infinite; transform-origin: 100px 100px;">
    <circle cx="100" cy="100" r="88" fill="none" stroke="#6b7a4a" stroke-width="1.5" opacity="0.6"/>
    <g stroke="#6b7a4a" stroke-width="1.5" opacity="0.7">
    <line x1="100" y1="12" x2="100" y2="26"/>
    <line x1="100" y1="174" x2="100" y2="188"/>
    <line x1="12" y1="100" x2="26" y2="100"/>
    <line x1="174" y1="100" x2="188" y2="100"/>
    <line x1="37.6" y1="37.6" x2="47.5" y2="47.5"/>
    <line x1="152.5" y1="152.5" x2="162.4" y2="162.4"/>
    <line x1="37.6" y1="162.4" x2="47.5" y2="152.5"/>
    <line x1="152.5" y1="47.5" x2="162.4" y2="37.6"/>
    </g>
    </g>
    <circle cx="100" cy="100" r="34" fill="url(#glow4)">
    <animate attributeName="r" values="30;36;30" dur="3.5s" repeatCount="indefinite"/>
    </circle>
    <circle cx="100" cy="100" r="24" fill="#0c0f08" stroke="#e0995c" stroke-width="2"/>
    <path d="M100,84 L104,98 L118,100 L104,102 L100,116 L96,102 L82,100 L96,98 Z" fill="#e0995c"/>
    </svg>
    </div>
    <style>
    @keyframes arena-rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    </style>
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
    elif stile == "marmo":
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
    elif stile == "acciaio":
        box_bg = """
            repeating-linear-gradient(135deg, rgba(255,255,255,0.02) 0px, rgba(255,255,255,0.02) 2px, transparent 2px, transparent 14px),
            linear-gradient(135deg, #2b3238 0%, #3a434b 50%, #4a555e 100%)"""
        border_color = "#6b7680"
        text_color = "#e4e8eb"
        font_import = "Barlow+Condensed:wght@700"
        font_family = "'Barlow Condensed', sans-serif"
        text_transform = "uppercase"
        letter_spacing = "1px"
    else:
        box_bg = """
            radial-gradient(circle at 20% 20%, rgba(90,110,70,0.35), transparent 45%),
            radial-gradient(circle at 80% 70%, rgba(60,50,30,0.4), transparent 50%),
            linear-gradient(135deg, #3a4230 0%, #2c3322 50%, #241f16 100%)"""
        border_color = "#6b7a4a"
        text_color = "#e6e4d4"
        font_import = "Bebas+Neue"
        font_family = "'Bebas Neue', sans-serif"
        text_transform = "none"
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
        "titolo_div": "https://github.com/google/fonts/raw/main/ofl/barlowcondensed/BarlowCondensed-Bold.ttf",
        "titolo_hg": "https://github.com/google/fonts/raw/main/ofl/bebasneue/BebasNeue-Regular.ttf",
        "corpo": "https://github.com/google/fonts/raw/main/ofl/ebgaramond/EBGaramond[wght].ttf",
        "corsivo": "https://github.com/google/fonts/raw/main/ofl/ebgaramond/EBGaramond-Italic[wght].ttf",
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

    testo_avvolto = textwrap.fill(info["descrizione"], width=46)
    y_desc = 410
    for riga in testo_avvolto.split("\n"):
        testo_centrato(riga, y_desc, f_desc, (255, 255, 255))
        y_desc += 46

    dettagli = info["dettagli"][:4]
    padding_box = 22
    gap_label_valore = 6
    gap_tra_righe = 16

    def altezza_testo(testo, font):
        bbox = draw.textbbox((0, 0), testo, font=font)
        return bbox[3] - bbox[1]

    altezze_righe = []
    for label, valore in dettagli:
        h = altezza_testo(label.upper(), f_footer) + gap_label_valore + altezza_testo(valore, f_desc)
        altezze_righe.append(h)

    box_h = padding_box * 2 + sum(altezze_righe) + gap_tra_righe * (len(dettagli) - 1)
    y_box = y_desc + 60
    draw.rectangle([120, y_box, W - 120, y_box + box_h], outline=(255, 255, 255, 150), width=2)

    y_cursor = y_box + padding_box
    for i, (label, valore) in enumerate(dettagli):
        draw.text((150, y_cursor), label.upper(), font=f_footer, fill=(255, 255, 255, 200))
        y_valore = y_cursor + altezza_testo(label.upper(), f_footer) + gap_label_valore
        draw.text((150, y_valore), valore, font=f_desc, fill=(255, 255, 255))
        y_fine_riga = y_valore + altezza_testo(valore, f_desc)
        if i < len(dettagli) - 1:
            y_line = y_fine_riga + gap_tra_righe / 2
            draw.line(
                [(150, y_line), (W - 150, y_line)],
                fill=(255, 255, 255, 60), width=1,
            )
        y_cursor = y_fine_riga + gap_tra_righe

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
# QUIZ 3 — A QUALE FAZIONE APPARTIENI?
# ============================================================
def render_divergent():
    prefix = "div"
    init_state(prefix, DIVERGENT)
    if f"{prefix}_ordine" not in st.session_state:
        st.session_state[f"{prefix}_ordine"] = list(range(len(QUESTIONS_DIV)))
        random.shuffle(st.session_state[f"{prefix}_ordine"])

    if st.button("← Torna al menu"):
        st.session_state.pagina = "menu"
        st.rerun()

    render_steel_background()

    st.markdown('<div class="steel-title">A quale fazione appartieni?</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="steel-subtitle">"Fazione prima del sangue. Ma chi sei, davvero, quando nessuno ti guarda?"</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state[f"{prefix}_iniziato"]:
        render_faction_wheel()
        st.markdown(
            textwrap.dedent("""\
            <div class="steel">
            <h3>Prima della Cerimonia della Scelta</h3>
            Rispondi con sincerità a 10 situazioni ispirate alla società delle
            cinque fazioni. Non esistono risposte giuste o sbagliate: la vera
            natura viene sempre a galla. Alla fine scoprirai a quale fazione
            apparterresti, con il tuo profilo completo — e potrai scaricare
            la tua card da condividere.
            </div>
            """),
            unsafe_allow_html=True,
        )
        if st.button("🗡️ Affronta la Cerimonia", use_container_width=True):
            st.session_state[f"{prefix}_iniziato"] = True
            st.rerun()

    elif not st.session_state[f"{prefix}_finito"]:
        idx = st.session_state[f"{prefix}_ordine"][st.session_state[f"{prefix}_domanda"]]
        domanda = QUESTIONS_DIV[idx]

        st.markdown(
            f'<div class="qcounter steel">Domanda {st.session_state[f"{prefix}_domanda"] + 1} di {len(QUESTIONS_DIV)}</div>',
            unsafe_allow_html=True,
        )
        st.progress(st.session_state[f"{prefix}_domanda"] / len(QUESTIONS_DIV))
        render_typewriter_question(domanda["domanda"], stile="acciaio")

        opzioni = list(domanda["opzioni"])
        random.Random(idx + 300).shuffle(opzioni)
        for testo_opzione, punti in opzioni:
            if st.button(testo_opzione, key=f"{prefix}_{idx}_{testo_opzione}"):
                rispondi(prefix, QUESTIONS_DIV, punti)
                st.rerun()

    else:
        punteggi = st.session_state[f"{prefix}_punteggi"]
        vincitore = max(punteggi, key=punteggi.get)
        info = DIVERGENT[vincitore]

        st.balloons()

        dettagli_html = "".join(
            f'<div class="fact-item"><span class="fact-label steel">{label}</span><span class="fact-value">{valore}</span></div>'
            for label, valore in info["dettagli"]
        )

        st.markdown(
            textwrap.dedent(f"""\
            <div class="result-card" style="background:{info['gradiente']};">
            <div style="font-size:3.2rem;">{info['emoji']}</div>
            <div class="result-house steel">{vincitore}</div>
            <div class="result-desc steel">{info['descrizione']}</div>
            <div class="fact-grid">{dettagli_html}</div>
            </div>
            """),
            unsafe_allow_html=True,
        )

        st.write("")
        with st.spinner("Sto preparando la tua card da condividere..."):
            buf = genera_immagine_condivisione(
                vincitore, info,
                "LA CERIMONIA DELLA SCELTA MI HA RIVELATO",
                "A QUALE FAZIONE APPARTIENI?",
                titolo_font_key="titolo_div",
            )
        col1, col2 = st.columns([1, 1])
        with col1:
            st.image(buf, use_container_width=True)
        with col2:
            st.write("")
            st.write("Scarica la tua card e condividila dove vuoi.")
            st.download_button(
                "📥 Scarica la card", data=buf,
                file_name=f"fazione_{vincitore.lower()}.png",
                mime="image/png", use_container_width=True,
            )

        st.write("")
        st.markdown('<div class="steel"><h3>Il tuo profilo tra le fazioni</h3></div>', unsafe_allow_html=True)
        fazioni = list(DIVERGENT.keys())
        render_radar(fazioni, [punteggi[f] for f in fazioni])

        for fazione, punti in sorted(punteggi.items(), key=lambda x: -x[1]):
            pct = punti / len(QUESTIONS_DIV)
            st.write(f"{DIVERGENT[fazione]['emoji']} **{fazione}** — {punti:g} punti")
            st.progress(min(pct, 1.0))

        st.write("")
        if st.button("🔄 Rifai la Cerimonia", use_container_width=True):
            reset_quiz(prefix, DIVERGENT, QUESTIONS_DIV)
            st.rerun()


# ============================================================
# QUIZ 4 — A QUALE DISTRETTO APPARTIENI?
# ============================================================
def render_hunger_games():
    prefix = "hg"
    init_state(prefix, DISTRICTS)
    if f"{prefix}_ordine" not in st.session_state:
        st.session_state[f"{prefix}_ordine"] = list(range(len(QUESTIONS_HG)))
        random.shuffle(st.session_state[f"{prefix}_ordine"])

    if st.button("← Torna al menu"):
        st.session_state.pagina = "menu"
        st.rerun()

    render_arena_background()

    st.markdown('<div class="arena-title">A quale Distretto appartieni?</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="arena-subtitle">"Che le probabilità siano sempre a tuo favore... ma chi sei, davvero, quando la sopravvivenza è in gioco?"</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state[f"{prefix}_iniziato"]:
        render_arena_compass()
        st.markdown(
            textwrap.dedent("""\
            <div class="canvas">
            <h3>Prima della Mietitura</h3>
            Rispondi con sincerità a 12 situazioni ispirate all'arena e a Panem.
            Non esistono risposte giuste o sbagliate: la vera natura viene sempre
            a galla quando tutto è in gioco. Alla fine scoprirai a quale distretto
            apparterresti, con il tuo profilo completo — e potrai scaricare la tua
            card da condividere.
            </div>
            """),
            unsafe_allow_html=True,
        )
        if st.button("🔥 Affronta la Mietitura", use_container_width=True):
            st.session_state[f"{prefix}_iniziato"] = True
            st.rerun()

    elif not st.session_state[f"{prefix}_finito"]:
        idx = st.session_state[f"{prefix}_ordine"][st.session_state[f"{prefix}_domanda"]]
        domanda = QUESTIONS_HG[idx]

        st.markdown(
            f'<div class="qcounter arena">Domanda {st.session_state[f"{prefix}_domanda"] + 1} di {len(QUESTIONS_HG)}</div>',
            unsafe_allow_html=True,
        )
        st.progress(st.session_state[f"{prefix}_domanda"] / len(QUESTIONS_HG))
        render_typewriter_question(domanda["domanda"], stile="arena")

        opzioni = list(domanda["opzioni"])
        random.Random(idx + 400).shuffle(opzioni)
        for testo_opzione, punti in opzioni:
            if st.button(testo_opzione, key=f"{prefix}_{idx}_{testo_opzione}"):
                rispondi(prefix, QUESTIONS_HG, punti)
                st.rerun()

    else:
        punteggi = st.session_state[f"{prefix}_punteggi"]
        vincitore = max(punteggi, key=punteggi.get)
        info = DISTRICTS[vincitore]

        st.balloons()

        dettagli_html = "".join(
            f'<div class="fact-item"><span class="fact-label arena">{label}</span><span class="fact-value">{valore}</span></div>'
            for label, valore in info["dettagli"]
        )

        st.markdown(
            textwrap.dedent(f"""\
            <div class="result-card" style="background:{info['gradiente']};">
            <div style="font-size:3.2rem;">{info['emoji']}</div>
            <div class="result-house arena">{vincitore}</div>
            <div class="result-desc arena">{info['descrizione']}</div>
            <div class="fact-grid">{dettagli_html}</div>
            </div>
            """),
            unsafe_allow_html=True,
        )

        st.write("")
        with st.spinner("Sto preparando la tua card da condividere..."):
            buf = genera_immagine_condivisione(
                vincitore, info,
                "LA MIETITURA HA PARLATO: APPARTIENI AL",
                "A QUALE DISTRETTO APPARTIENI?",
                titolo_font_key="titolo_hg",
            )
        col1, col2 = st.columns([1, 1])
        with col1:
            st.image(buf, use_container_width=True)
        with col2:
            st.write("")
            st.write("Scarica la tua card e condividila dove vuoi.")
            st.download_button(
                "📥 Scarica la card", data=buf,
                file_name=f"{vincitore.lower().replace(' ', '_')}.png",
                mime="image/png", use_container_width=True,
            )

        st.write("")
        st.markdown('<div class="canvas"><h3>Il tuo profilo tra i distretti</h3></div>', unsafe_allow_html=True)
        distretti = list(DISTRICTS.keys())
        render_radar(distretti, [punteggi[d] for d in distretti])

        for distretto, punti in sorted(punteggi.items(), key=lambda x: -x[1]):
            pct = punti / len(QUESTIONS_HG)
            st.write(f"{DISTRICTS[distretto]['emoji']} **{distretto}** — {punti:g} punti")
            st.progress(min(pct, 1.0))

        st.write("")
        if st.button("🔄 Rifai la Mietitura", use_container_width=True):
            reset_quiz(prefix, DISTRICTS, QUESTIONS_HG)
            st.rerun()


# ============================================================
# SELETTORE DI MONDO (condiviso da Creatore e Mappe)
# ============================================================
def render_selettore_mondo(session_key):
    opzioni = [
        ("hogwarts", "🎩", "Hogwarts"),
        ("percy", "⚡", "Campo Mezzosangue"),
        ("divergent", "⚖️", "Fazioni"),
        ("hunger", "🔥", "Panem"),
    ]
    col1, col2 = st.columns(2)
    for i, (chiave, emoji, nome) in enumerate(opzioni):
        col = col1 if i % 2 == 0 else col2
        with col:
            if st.button(f"{emoji}  {nome}", key=f"{session_key}_{chiave}", use_container_width=True):
                st.session_state[session_key] = chiave
                st.rerun()


# ============================================================
# GENERAZIONE IMMAGINE — SCHEDA PERSONAGGIO
# ============================================================
def genera_immagine_personaggio(r, dati, info_aff):
    W, H = 1080, 1080
    top, bottom = info_aff["rgb_top"], info_aff["rgb_bottom"]
    img = Image.new("RGB", (W, H), top)
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        col = tuple(int(top[c] + (bottom[c] - top[c]) * t) for c in range(3))
        draw.line([(0, y), (W, y)], fill=col)

    margine = 46
    draw.rectangle([margine, margine, W - margine, H - margine], outline=(243, 217, 139), width=6)
    draw.rectangle(
        [margine + 14, margine + 14, W - margine - 14, H - margine - 14],
        outline=(243, 217, 139, 120), width=1,
    )

    fonts_bytes = carica_font()
    f_eyebrow = _font(fonts_bytes, "corsivo", 30)
    f_titolo = _font(fonts_bytes, dati["font_titolo"], 80)
    f_desc = _font(fonts_bytes, "corpo", 32)
    f_footer = _font(fonts_bytes, "corsivo", 24)

    def testo_centrato(testo, y, font, fill=(255, 255, 255)):
        bbox = draw.textbbox((0, 0), testo, font=font)
        larghezza = bbox[2] - bbox[0]
        draw.text(((W - larghezza) / 2, y), testo, font=font, fill=fill)

    def altezza_testo(testo, font):
        bbox = draw.textbbox((0, 0), testo, font=font)
        return bbox[3] - bbox[1]

    testo_centrato(dati["eyebrow"], 150, f_eyebrow, (255, 255, 255))
    testo_centrato(r["nome"].upper(), 205, f_titolo, (255, 255, 255))
    testo_centrato(f"Affiliazione: {r['affiliazione']}", 320, f_desc, (255, 255, 255))

    dettagli = [
        ("Tratti", ", ".join(r["tratti"])),
        ("Oggetto", r["oggetto"]),
        ("Alleato", r["alleato"]),
    ]
    dettagli_wrap = [(label, textwrap.wrap(valore, width=40) or [""]) for label, valore in dettagli]

    padding_box, gap_label_valore, gap_tra_righe = 22, 6, 14
    altezze_righe = []
    for label, righe_valore in dettagli_wrap:
        h = altezza_testo(label.upper(), f_footer) + gap_label_valore
        h += sum(altezza_testo(r_ or "Ag", f_desc) + 8 for r_ in righe_valore)
        altezze_righe.append(h)

    box_h = padding_box * 2 + sum(altezze_righe) + gap_tra_righe * (len(dettagli_wrap) - 1)
    y_box = 400
    draw.rectangle([120, y_box, W - 120, y_box + box_h], outline=(255, 255, 255, 150), width=2)

    y_cursor = y_box + padding_box
    for i, (label, righe_valore) in enumerate(dettagli_wrap):
        draw.text((150, y_cursor), label.upper(), font=f_footer, fill=(255, 255, 255, 200))
        y_val = y_cursor + altezza_testo(label.upper(), f_footer) + gap_label_valore
        for riga in righe_valore:
            draw.text((150, y_val), riga, font=f_desc, fill=(255, 255, 255))
            y_val += altezza_testo(riga or "Ag", f_desc) + 8
        if i < len(dettagli_wrap) - 1:
            y_line = y_val + gap_tra_righe / 2
            draw.line([(150, y_line), (W - 150, y_line)], fill=(255, 255, 255, 60), width=1)
        y_cursor = y_val + gap_tra_righe

    testo_centrato(dati["titolo"].upper(), H - 110, f_footer, (255, 255, 255))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


# ============================================================
# STRUMENTO 1 — CREATORE DI PERSONAGGIO
# ============================================================
def render_creator():
    if st.button("← Torna al menu"):
        st.session_state.pagina = "menu"
        st.session_state.pop("creator_mondo", None)
        st.session_state.pop("creator_risultato", None)
        st.rerun()

    st.markdown('<div class="hat-title" style="font-size:2.3rem;">🪄 Creatore di Personaggio</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Scegli il mondo in cui vuoi dare vita al tuo personaggio</div>', unsafe_allow_html=True)

    mondo = st.session_state.get("creator_mondo")
    if not mondo:
        render_selettore_mondo("creator_mondo")
        return

    dati = CREATOR_DATA[mondo]

    if "creator_risultato" not in st.session_state:
        st.markdown(f'<div class="parchment"><h3>{dati["titolo"]}</h3></div>', unsafe_allow_html=True)
        nome_pg = st.text_input("Come si chiama il tuo personaggio?", placeholder="Scrivi un nome...")
        tratti_scelti = st.multiselect("Scegli fino a 2 tratti caratteriali", dati["tratti"], max_selections=2)

        if st.button("✨ Genera il personaggio", use_container_width=True):
            if not nome_pg.strip():
                st.warning("Dai un nome al tuo personaggio prima di procedere!")
            elif not tratti_scelti:
                st.warning("Scegli almeno un tratto caratteriale!")
            else:
                st.session_state.creator_risultato = {
                    "nome": html.escape(nome_pg.strip())[:40],
                    "tratti": tratti_scelti,
                    "affiliazione": random.choice(list(dati["entita"].keys())),
                    "oggetto": random.choice(dati["oggetti"]),
                    "alleato": random.choice(dati["alleati"]),
                }
                st.rerun()

        if st.button("🔄 Cambia mondo", use_container_width=True):
            st.session_state.pop("creator_mondo", None)
            st.rerun()

    else:
        r = st.session_state.creator_risultato
        info_aff = dati["entita"][r["affiliazione"]]
        st.balloons()

        dettagli_html = "".join(
            f'<div class="fact-item"><span class="fact-label">Tratto</span><span class="fact-value">{t}</span></div>'
            for t in r["tratti"]
        )
        st.markdown(
            textwrap.dedent(f"""\
            <div class="result-card" style="background:{info_aff['gradiente']};">
            <div style="font-size:2.4rem;">{info_aff['emoji']}</div>
            <div class="result-house">{r['nome']}</div>
            <div class="result-desc">Affiliazione: {r['affiliazione']}</div>
            <div class="fact-grid">
            {dettagli_html}
            <div class="fact-item span2"><span class="fact-label">Oggetto</span><span class="fact-value">{r['oggetto']}</span></div>
            <div class="fact-item span2"><span class="fact-label">Alleato</span><span class="fact-value">{r['alleato']}</span></div>
            </div>
            </div>
            """),
            unsafe_allow_html=True,
        )

        st.write("")
        with st.spinner("Sto preparando la scheda del personaggio..."):
            buf = genera_immagine_personaggio(r, dati, info_aff)
        col1, col2 = st.columns([1, 1])
        with col1:
            st.image(buf, use_container_width=True)
        with col2:
            st.write("")
            st.write("Scarica la scheda del tuo personaggio e condividila dove vuoi.")
            nome_file = re.sub(r"[^a-z0-9]+", "_", r["nome"].lower()).strip("_") or "personaggio"
            st.download_button(
                "📥 Scarica la scheda", data=buf,
                file_name=f"{nome_file}.png", mime="image/png", use_container_width=True,
            )

        st.write("")
        if st.button("🔄 Crea un altro personaggio", use_container_width=True):
            st.session_state.pop("creator_risultato", None)
            st.rerun()


# ============================================================
# STRUMENTO 2 — SOPRAVVIVENZA NELL'ARENA (Hunger Games)
# ============================================================
def render_survival():
    prefix = "surv"

    if st.button("← Torna al menu"):
        st.session_state.pagina = "menu"
        st.rerun()

    render_arena_background()
    st.markdown('<div class="arena-title">Sopravvivenza nell\'Arena</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="arena-subtitle">"Che le probabilità siano sempre a tuo favore... ma quanto durerai davvero?"</div>',
        unsafe_allow_html=True,
    )

    for chiave, default in [
        ("iniziato", False), ("giorno", 0), ("salute", 100),
        ("provviste", 60), ("log", []), ("finito", False), ("esito", None),
    ]:
        if f"{prefix}_{chiave}" not in st.session_state:
            st.session_state[f"{prefix}_{chiave}"] = default

    def reset_survival():
        st.session_state[f"{prefix}_iniziato"] = False
        st.session_state[f"{prefix}_giorno"] = 0
        st.session_state[f"{prefix}_salute"] = 100
        st.session_state[f"{prefix}_provviste"] = 60
        st.session_state[f"{prefix}_log"] = []
        st.session_state[f"{prefix}_finito"] = False
        st.session_state[f"{prefix}_esito"] = None

    if not st.session_state[f"{prefix}_iniziato"]:
        render_arena_compass()
        st.markdown(
            textwrap.dedent("""\
            <div class="canvas">
            <h3>Prima del Gong</h3>
            Affronterai 6 giorni nell'arena. Ogni scelta influisce sulla tua
            salute e sulle tue provviste: se la salute crolla a zero, il tuo
            percorso finisce lì. Sopravvivi fino alla fine e sarai il vincitore
            dei Giochi.
            </div>
            """),
            unsafe_allow_html=True,
        )
        if st.button("🔥 Entra nell'Arena", use_container_width=True):
            st.session_state[f"{prefix}_iniziato"] = True
            st.rerun()

    elif not st.session_state[f"{prefix}_finito"]:
        giorno_idx = st.session_state[f"{prefix}_giorno"]
        giorno = GIORNI_ARENA[giorno_idx]

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f'<div class="qcounter arena">Giorno {giorno_idx + 1} di {len(GIORNI_ARENA)}</div>', unsafe_allow_html=True)
            st.write(f"❤️ Salute: {st.session_state[f'{prefix}_salute']}")
            st.progress(max(st.session_state[f"{prefix}_salute"], 0) / 100)
        with col_b:
            st.write("")
            st.write(f"🎒 Provviste: {st.session_state[f'{prefix}_provviste']}")
            st.progress(max(min(st.session_state[f"{prefix}_provviste"], 100), 0) / 100)

        render_typewriter_question(giorno["situazione"], stile="arena")

        for testo_scelta, effetti in giorno["scelte"]:
            if st.button(testo_scelta, key=f"{prefix}_{giorno_idx}_{testo_scelta}"):
                nuova_salute = max(0, min(100, st.session_state[f"{prefix}_salute"] + effetti["salute"]))
                nuove_provviste = max(0, min(100, st.session_state[f"{prefix}_provviste"] + effetti["provviste"]))
                st.session_state[f"{prefix}_salute"] = nuova_salute
                st.session_state[f"{prefix}_provviste"] = nuove_provviste
                st.session_state[f"{prefix}_log"].append((giorno_idx + 1, testo_scelta))
                if nuova_salute <= 0:
                    st.session_state[f"{prefix}_finito"] = True
                    st.session_state[f"{prefix}_esito"] = "eliminato"
                elif giorno_idx + 1 >= len(GIORNI_ARENA):
                    st.session_state[f"{prefix}_finito"] = True
                    st.session_state[f"{prefix}_esito"] = "vincitore"
                else:
                    st.session_state[f"{prefix}_giorno"] += 1
                st.rerun()

    else:
        esito = st.session_state[f"{prefix}_esito"]
        giorni_sopravvissuti = len(st.session_state[f"{prefix}_log"])

        if esito == "vincitore":
            titolo_esito = "🏆 Sei il Vincitore dei Giochi!"
            desc_esito = (
                f"Hai attraversato tutti i {len(GIORNI_ARENA)} giorni nell'arena e sei tornato a casa. "
                "Il tuo Distretto festeggia il tuo ritorno."
            )
            gradiente_esito = "linear-gradient(135deg, #4a3b00 0%, #b89b1a 50%, #ffdb00 100%)"
            st.balloons()
        else:
            titolo_esito = "💀 Sei stato eliminato"
            desc_esito = (
                f"Sei sopravvissuto per {giorni_sopravvissuti} giorni su {len(GIORNI_ARENA)} "
                "prima che l'arena avesse la meglio su di te."
            )
            gradiente_esito = "linear-gradient(135deg, #280404 0%, #6e0f0f 50%, #961414 100%)"

        st.markdown(
            textwrap.dedent(f"""\
            <div class="result-card" style="background:{gradiente_esito};">
            <div style="font-size:3rem;">{'🏆' if esito == 'vincitore' else '💀'}</div>
            <div class="result-house arena">{titolo_esito}</div>
            <div class="result-desc arena">{desc_esito}</div>
            </div>
            """),
            unsafe_allow_html=True,
        )

        st.write("")
        st.markdown('<div class="canvas"><h3>Il tuo percorso nell\'arena</h3></div>', unsafe_allow_html=True)
        for giorno_n, scelta in st.session_state[f"{prefix}_log"]:
            st.write(f"**Giorno {giorno_n}:** {scelta}")

        st.write("")
        if st.button("🔄 Rientra nell'Arena", use_container_width=True):
            reset_survival()
            st.rerun()


# ============================================================
# STRUMENTO 3 — MAPPE INTERATTIVE
# ============================================================
def render_map_svg(luoghi, stile_card):
    marcatori = "".join(
        f'<a href="?loc={l["slug"]}">'
        f'<circle cx="{l["x"]}" cy="{l["y"]}" r="14" fill="#8a1f1f" stroke="#f3d98b" stroke-width="2"/>'
        f'<circle cx="{l["x"]}" cy="{l["y"]}" r="5" fill="#f3d98b"/>'
        f'<text x="{l["x"]}" y="{l["y"] - 20}" font-size="15" font-weight="700" '
        f'fill="currentColor" text-anchor="middle">{l["nome"]}</text>'
        f'</a>'
        for l in luoghi
    )
    linee = "".join(
        f'<line x1="{luoghi[i]["x"]}" y1="{luoghi[i]["y"]}" x2="{luoghi[i + 1]["x"]}" y2="{luoghi[i + 1]["y"]}" '
        f'stroke="currentColor" stroke-width="1.5" stroke-dasharray="6,6" opacity="0.4"/>'
        for i in range(len(luoghi) - 1)
    )
    svg = textwrap.dedent(f"""\
    <div class="{stile_card}" style="padding:1rem;">
    <svg viewBox="0 0 800 400" xmlns="http://www.w3.org/2000/svg" style="width:100%; height:auto;">
    {linee}
    {marcatori}
    </svg>
    </div>
    """)
    st.markdown(svg, unsafe_allow_html=True)


def render_mappe():
    if st.button("← Torna al menu"):
        st.session_state.pagina = "menu"
        st.session_state.pop("mappa_mondo", None)
        try:
            st.query_params.clear()
        except Exception:
            pass
        st.rerun()

    st.markdown('<div class="nexus-title" style="font-size:2.2rem;">🗺️ Mappe Interattive</div>', unsafe_allow_html=True)
    st.markdown('<div class="nexus-subtitle">Scegli un mondo ed esplora i suoi luoghi</div>', unsafe_allow_html=True)

    mondo = st.session_state.get("mappa_mondo")
    if not mondo:
        render_selettore_mondo("mappa_mondo")
        return

    dati = MAP_POIS[mondo]
    st.markdown(f'<div class="{dati["font_titolo_css"]}" style="font-size:2rem;">{dati["titolo"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="subtitle">{dati["eyebrow"]}</div>', unsafe_allow_html=True)

    render_map_svg(dati["luoghi"], dati["stile_card"])

    try:
        loc = st.query_params.get("loc")
    except Exception:
        loc = None

    luogo_trovato = next((l for l in dati["luoghi"] if l["slug"] == loc), None)
    if luogo_trovato:
        st.markdown(
            f'<div class="{dati["stile_card"]}"><h3>{luogo_trovato["nome"]}</h3>{luogo_trovato["desc"]}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.info("Clicca su un punto della mappa per scoprire cosa nasconde quel luogo.")

    if st.button("🔄 Cambia mondo", use_container_width=True):
        st.session_state.pop("mappa_mondo", None)
        try:
            st.query_params.clear()
        except Exception:
            pass
        st.rerun()


# ============================================================
# MENU INIZIALE
# ============================================================
def render_menu():
    render_nexus_background()
    st.markdown('<div class="nexus-title">FANTASY QUIZ</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="nexus-subtitle">Scegli quale realtà vuoi esplorare</div>',
        unsafe_allow_html=True,
    )
    render_nexus_emblem()

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

    col3, col4 = st.columns(2)

    with col3:
        st.markdown(
            textwrap.dedent("""\
            <div class="menu-card" style="background:linear-gradient(160deg, #2b3238 0%, #1a1f22 100%);">
            <div class="menu-card-icon">⚖️</div>
            <div class="menu-card-title" style="font-family:'Barlow Condensed',sans-serif; letter-spacing:2px; text-transform:uppercase;">A quale fazione appartieni?</div>
            <div class="menu-card-desc">Scopri quale fazione rispecchia davvero la tua natura</div>
            </div>
            """),
            unsafe_allow_html=True,
        )
        if st.button("Affronta la Scelta", key="entra_div", use_container_width=True):
            st.session_state.pagina = "divergent"
            st.rerun()

    with col4:
        st.markdown(
            textwrap.dedent("""\
            <div class="menu-card" style="background:linear-gradient(160deg, #241f16 0%, #2c3322 100%);">
            <div class="menu-card-icon">🔥</div>
            <div class="menu-card-title arena">A quale Distretto appartieni?</div>
            <div class="menu-card-desc">Scopri come sopravviveresti nell'arena di Panem</div>
            </div>
            """),
            unsafe_allow_html=True,
        )
        if st.button("Affronta la Mietitura", key="entra_hg", use_container_width=True):
            st.session_state.pagina = "hunger"
            st.rerun()

    st.write("")
    st.markdown(
        '<div class="nexus-subtitle" style="margin-top:0.4rem;">Altri strumenti</div>',
        unsafe_allow_html=True,
    )

    col5, col6, col7 = st.columns(3)

    with col5:
        st.markdown(
            textwrap.dedent("""\
            <div class="menu-card" style="background:linear-gradient(160deg, #3a2a05 0%, #4a1608 100%);">
            <div class="menu-card-icon">🪄</div>
            <div class="menu-card-title">Creatore di Personaggio</div>
            <div class="menu-card-desc">Dai vita al tuo personaggio in uno dei quattro mondi</div>
            </div>
            """),
            unsafe_allow_html=True,
        )
        if st.button("Crea il tuo personaggio", key="entra_creator", use_container_width=True):
            st.session_state.pagina = "creator"
            st.rerun()

    with col6:
        st.markdown(
            textwrap.dedent("""\
            <div class="menu-card" style="background:linear-gradient(160deg, #0c0f08 0%, #4a1608 100%);">
            <div class="menu-card-icon">🏹</div>
            <div class="menu-card-title arena">Sopravvivenza nell'Arena</div>
            <div class="menu-card-desc">Affronta 6 giorni nell'arena di Hunger Games e scopri se sopravvivi</div>
            </div>
            """),
            unsafe_allow_html=True,
        )
        if st.button("Entra nell'Arena", key="entra_survival", use_container_width=True):
            st.session_state.pagina = "survival"
            st.rerun()

    with col7:
        st.markdown(
            textwrap.dedent("""\
            <div class="menu-card" style="background:linear-gradient(160deg, #0e2233 0%, #1a2f14 100%);">
            <div class="menu-card-icon">🗺️</div>
            <div class="menu-card-title">Mappe Interattive</div>
            <div class="menu-card-desc">Esplora i luoghi più iconici di ciascun mondo</div>
            </div>
            """),
            unsafe_allow_html=True,
        )
        if st.button("Esplora le mappe", key="entra_mappe", use_container_width=True):
            st.session_state.pagina = "mappe"
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
elif st.session_state.pagina == "divergent":
    render_divergent()
elif st.session_state.pagina == "hunger":
    render_hunger_games()
elif st.session_state.pagina == "creator":
    render_creator()
elif st.session_state.pagina == "survival":
    render_survival()
elif st.session_state.pagina == "mappe":
    render_mappe()