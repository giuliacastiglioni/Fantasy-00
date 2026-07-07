import streamlit as st
import streamlit.components.v1 as components
import random
import json
import io
import textwrap
import requests
import plotly.graph_objects as go
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="Il Cappello Parlante", page_icon="🎩", layout="centered")

# ============================================================
# DATI CANONICI DELLE QUATTRO CASE
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
        "fondatore": "Godric Grifondoro",
        "animale": "Leone",
        "elemento": "Fuoco",
        "colori": "Rosso porpora e oro",
        "fantasma": "Nick Quasi Senza Testa",
        "sala": "Una torre al settimo piano, dietro il ritratto della Signora Grassa",
        "valori": "Coraggio, audacia, determinazione, spirito cavalleresco",
        "alunni": "Harry Potter, Hermione Granger, Albus Silente",
        "descrizione": "Il coraggio scorre nelle tue vene. Non sei senza paura — nessun vero grifondoro lo è — ma agisci anche quando hai paura, ed è proprio questo a definirti.",
    },
    "Serpeverde": {
        "gradiente": "linear-gradient(135deg, #0d1f13 0%, #1a472a 50%, #3c6e47 100%)",
        "rgb_top": (13, 31, 19),
        "rgb_bottom": (60, 110, 71),
        "emoji": "🐍",
        "fondatore": "Salazar Serpeverde",
        "animale": "Serpente",
        "elemento": "Acqua",
        "colori": "Verde smeraldo e argento",
        "fantasma": "Il Barone Sanguinario",
        "sala": "Nei sotterranei, dietro un muro di pietra nascosto, con vista sul lago",
        "valori": "Ambizione, astuzia, determinazione, leadership",
        "alunni": "Severus Piton, Tom Riddle, Horace Lumacorno",
        "descrizione": "Sai esattamente cosa vuoi e come ottenerlo. La tua mente strategica e la tua ambizione ti spingono sempre un passo più in là degli altri.",
    },
    "Corvonero": {
        "gradiente": "linear-gradient(135deg, #060d24 0%, #0e1a40 50%, #2b4a8c 100%)",
        "rgb_top": (6, 13, 36),
        "rgb_bottom": (43, 74, 140),
        "emoji": "🦅",
        "fondatore": "Priscilla Corvonero",
        "animale": "Aquila",
        "elemento": "Aria",
        "colori": "Blu notte e bronzo",
        "fantasma": "La Signora Grigia",
        "sala": "In cima a una torre; l'accesso richiede di risolvere un enigma, non una parola d'ordine",
        "valori": "Intelligenza, creatività, curiosità, originalità",
        "alunni": "Luna Lovegood, Gilderoy Allock, Filius Vitious",
        "descrizione": "La tua mente non si ferma mai. Curiosità e ingegno ti guidano, e per te il sapere non è un dovere ma una delle più grandi gioie della vita.",
    },
    "Tassorosso": {
        "gradiente": "linear-gradient(135deg, #4a3b00 0%, #b89b1a 50%, #ffdb00 100%)",
        "rgb_top": (74, 59, 0),
        "rgb_bottom": (255, 219, 0),
        "emoji": "🦡",
        "fondatore": "Helga Tassorosso",
        "animale": "Tasso",
        "elemento": "Terra",
        "colori": "Giallo canarino e nero",
        "fantasma": "Il Frate Grasso",
        "sala": "Un seminterrato accogliente vicino alle cucine, l'ingresso è mimetizzato tra i barili",
        "valori": "Lealtà, lavoro duro, pazienza, correttezza",
        "alunni": "Cedric Diggory, Newton Scamander, Pomona Sprite",
        "descrizione": "Non cerchi i riflettori, ma senza di te nessun gruppo reggerebbe. Leale fino in fondo, lavori sodo e tratti tutti con la stessa gentilezza onesta.",
    },
}

# ============================================================
# DOMANDE — scenari originali coerenti con il mondo di Harry
# Potter, non citazioni testuali. Ogni risposta assegna punti
# (anche parziali) a una o più case, per un profilo sfumato.
# ============================================================
QUESTIONS = [
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
# CSS — atmosfera "biblioteca incantata / pergamena antica"
# ============================================================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel+Decorative:wght@700;900&family=EB+Garamond:ital,wght@0,400;0,600;1,400&family=IM+Fell+English:ital@0;1&display=swap');

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
    @keyframes flicker {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.88; }
    }

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

    .qcounter {
        font-family: 'IM Fell English', serif;
        font-style: italic;
        color: #cbb989;
        text-align: center;
        font-size: 1rem;
        margin-bottom: 6px;
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
    .result-desc {
        font-family: 'IM Fell English', serif;
        font-style: italic;
        color: rgba(255,255,255,0.92);
        font-size: 1.15rem;
        max-width: 520px;
        margin: 0.6rem auto 0;
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
    .fact-label {
        font-family: 'IM Fell English', serif;
        font-style: italic;
        font-size: 0.85rem;
        opacity: 0.75;
        display: block;
    }
    .fact-value {
        font-size: 1rem;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# STEMMA ANIMATO (SVG originale — quattro quadranti colorati
# con semplici glifi degli elementi, non l'artwork ufficiale)
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


# ============================================================
# EFFETTO MACCHINA DA SCRIVERE per il testo della domanda
# ============================================================
def render_typewriter_question(testo):
    righe = max(2, -(-len(testo) // 50))
    altezza = 70 + righe * 30
    testo_js = json.dumps(testo)
    html_code = f"""
    <html>
    <head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cinzel+Decorative:wght@700&family=EB+Garamond:wght@600&display=swap');
        body {{ margin:0; background:transparent; }}
        .box {{
            background:
                radial-gradient(circle at 15% 20%, rgba(139,110,60,0.18), transparent 40%),
                radial-gradient(circle at 85% 80%, rgba(90,60,20,0.22), transparent 45%),
                linear-gradient(135deg, #ecdcb2 0%, #e2cd9a 50%, #dcc389 100%);
            border: 1px solid #8a6a12;
            outline: 6px solid #120d08;
            outline-offset: -12px;
            border-radius: 4px;
            padding: 1.4rem 1.6rem;
            box-shadow: inset 0 0 60px rgba(120,90,40,0.25);
            box-sizing: border-box;
        }}
        h3 {{
            font-family: 'Cinzel Decorative', serif;
            font-size: 1.15rem;
            color: #4a2f0e;
            font-weight: 700;
            margin: 0;
            border-bottom: 1px solid #8a6a12;
            padding-bottom: 8px;
            line-height: 1.5;
        }}
        .cursor {{
            display: inline-block;
            animation: blink 0.8s step-end infinite;
            color: #4a2f0e;
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
# GENERAZIONE IMMAGINE CONDIVIDIBILE (card risultato in PNG)
# ============================================================
@st.cache_resource(show_spinner=False)
def carica_font():
    fonts = {}
    sorgenti = {
        "titolo": "https://github.com/google/fonts/raw/main/ofl/cinzeldecorative/CinzelDecorative-Bold.ttf",
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


def genera_immagine_condivisione(casa, info):
    W, H = 1080, 1080
    img = Image.new("RGB", (W, H), info["rgb_top"])
    draw = ImageDraw.Draw(img)

    top = info["rgb_top"]
    bottom = info["rgb_bottom"]
    for y in range(H):
        t = y / H
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    margine = 46
    draw.rectangle(
        [margine, margine, W - margine, H - margine],
        outline=(243, 217, 139),
        width=6,
    )
    draw.rectangle(
        [margine + 14, margine + 14, W - margine - 14, H - margine - 14],
        outline=(243, 217, 139, 120),
        width=1,
    )

    fonts_bytes = carica_font()
    f_eyebrow = _font(fonts_bytes, "corsivo", 34)
    f_titolo = _font(fonts_bytes, "titolo", 92)
    f_desc = _font(fonts_bytes, "corpo", 34)
    f_footer = _font(fonts_bytes, "corsivo", 28)

    def testo_centrato(testo, y, font, fill=(255, 255, 255)):
        bbox = draw.textbbox((0, 0), testo, font=font)
        larghezza = bbox[2] - bbox[0]
        draw.text(((W - larghezza) / 2, y), testo, font=font, fill=fill)

    testo_centrato("IL CAPPELLO PARLANTE MI HA SMISTATO A", 165, f_eyebrow, (255, 255, 255))
    testo_centrato(casa.upper(), 230, f_titolo, (255, 255, 255))

    testo_avvolto = textwrap.fill(info["descrizione"], width=42)
    y_desc = 420
    for riga in testo_avvolto.split("\n"):
        testo_centrato(riga, y_desc, f_desc, (255, 255, 255))
        y_desc += 46

    dettagli = [
        ("FONDATORE", info["fondatore"]),
        ("ANIMALE SIMBOLO", info["animale"]),
        ("ELEMENTO", info["elemento"]),
        ("COLORI", info["colori"]),
    ]
    y_box = y_desc + 60
    box_h = 250
    draw.rectangle([120, y_box, W - 120, y_box + box_h], outline=(255, 255, 255, 150), width=2)
    riga_h = box_h / len(dettagli)
    for i, (label, valore) in enumerate(dettagli):
        y_riga = y_box + i * riga_h + riga_h / 2 - 16
        draw.text((150, y_riga - 22), label, font=f_footer, fill=(255, 255, 255, 200))
        draw.text((150, y_riga + 8), valore, font=f_desc, fill=(255, 255, 255))
        if i < len(dettagli) - 1:
            draw.line([(150, y_box + (i + 1) * riga_h), (W - 150, y_box + (i + 1) * riga_h)],
                       fill=(255, 255, 255, 60), width=1)

    testo_centrato("SMISTAMENTO DI HOGWARTS", H - 110, f_footer, (255, 255, 255))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


# ============================================================
# STATO
# ============================================================
if "iniziato" not in st.session_state:
    st.session_state.iniziato = False
if "domanda_corrente" not in st.session_state:
    st.session_state.domanda_corrente = 0
if "punteggi" not in st.session_state:
    st.session_state.punteggi = {casa: 0.0 for casa in HOUSES}
if "ordine_domande" not in st.session_state:
    st.session_state.ordine_domande = list(range(len(QUESTIONS)))
    random.shuffle(st.session_state.ordine_domande)
if "finito" not in st.session_state:
    st.session_state.finito = False


def reset_quiz():
    st.session_state.iniziato = False
    st.session_state.domanda_corrente = 0
    st.session_state.punteggi = {casa: 0.0 for casa in HOUSES}
    st.session_state.ordine_domande = list(range(len(QUESTIONS)))
    random.shuffle(st.session_state.ordine_domande)
    st.session_state.finito = False


def rispondi(punti_assegnati):
    for casa, punti in punti_assegnati.items():
        st.session_state.punteggi[casa] += punti
    st.session_state.domanda_corrente += 1
    if st.session_state.domanda_corrente >= len(QUESTIONS):
        st.session_state.finito = True


# ============================================================
# INTERFACCIA
# ============================================================
st.markdown('<div class="hat-title"> Il Cappello Parlante </div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">"Mmh... difficile, molto difficile. Vediamo cosa nascondi davvero..."</div>', unsafe_allow_html=True)

if not st.session_state.iniziato:
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
        st.session_state.iniziato = True
        st.rerun()

elif not st.session_state.finito:
    idx_domanda = st.session_state.ordine_domande[st.session_state.domanda_corrente]
    domanda = QUESTIONS[idx_domanda]

    st.markdown(
        f'<div class="qcounter">Domanda {st.session_state.domanda_corrente + 1} di {len(QUESTIONS)}</div>',
        unsafe_allow_html=True,
    )
    st.progress((st.session_state.domanda_corrente) / len(QUESTIONS))

    render_typewriter_question(domanda["domanda"])

    opzioni = list(domanda["opzioni"])
    random.Random(idx_domanda + 100).shuffle(opzioni)

    for testo_opzione, punti in opzioni:
        if st.button(testo_opzione, key=f"{idx_domanda}_{testo_opzione}"):
            rispondi(punti)
            st.rerun()

else:
    casa_vincente = max(st.session_state.punteggi, key=st.session_state.punteggi.get)
    info = HOUSES[casa_vincente]

    st.balloons()

    st.markdown(
        textwrap.dedent(f"""\
        <div class="result-card" style="background:{info['gradiente']};">
        <div style="font-size:3.2rem;">{info['emoji']}</div>
        <div class="result-house">{casa_vincente}</div>
        <div class="result-desc">{info['descrizione']}</div>
        <div class="fact-grid">
        <div class="fact-item"><span class="fact-label">Fondatore</span><span class="fact-value">{info['fondatore']}</span></div>
        <div class="fact-item"><span class="fact-label">Animale</span><span class="fact-value">{info['animale']}</span></div>
        <div class="fact-item"><span class="fact-label">Elemento</span><span class="fact-value">{info['elemento']}</span></div>
        <div class="fact-item"><span class="fact-label">Colori</span><span class="fact-value">{info['colori']}</span></div>
        <div class="fact-item"><span class="fact-label">Fantasma</span><span class="fact-value">{info['fantasma']}</span></div>
        <div class="fact-item"><span class="fact-label">Sala comune</span><span class="fact-value">{info['sala']}</span></div>
        <div class="fact-item" style="grid-column: span 2;"><span class="fact-label">Valori</span><span class="fact-value">{info['valori']}</span></div>
        <div class="fact-item" style="grid-column: span 2;"><span class="fact-label">Alunni celebri</span><span class="fact-value">{info['alunni']}</span></div>
        </div>
        </div>
        """),
        unsafe_allow_html=True,
    )

    st.write("")
    with st.spinner("Sto preparando la tua card da condividere..."):
        immagine_buf = genera_immagine_condivisione(casa_vincente, info)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.image(immagine_buf, use_container_width=True)
    with col2:
        st.write("")
        st.write("Scarica la tua card e condividila dove vuoi: gruppi WhatsApp, storie, chat con gli amici.")
        st.download_button(
            label="📥 Scarica la card",
            data=immagine_buf,
            file_name=f"smistamento_{casa_vincente.lower()}.png",
            mime="image/png",
            use_container_width=True,
        )

    st.write("")
    st.markdown(
        '<div class="parchment"><h3>Il tuo profilo tra le quattro case</h3></div>',
        unsafe_allow_html=True,
    )

    case_ordinate = list(HOUSES.keys())
    valori = [st.session_state.punteggi[c] for c in case_ordinate]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=valori + [valori[0]],
        theta=case_ordinate + [case_ordinate[0]],
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

    for casa, punti in sorted(st.session_state.punteggi.items(), key=lambda x: -x[1]):
        pct = punti / len(QUESTIONS)
        st.write(f"{HOUSES[casa]['emoji']} **{casa}** — {punti:g} punti")
        st.progress(min(pct, 1.0))

    st.write("")
    if st.button("🔄 Rifai lo Smistamento", use_container_width=True):
        reset_quiz()
        st.rerun()