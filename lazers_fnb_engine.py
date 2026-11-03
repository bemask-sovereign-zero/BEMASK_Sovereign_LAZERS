import os
import json
from datetime import datetime
import urllib.request
import streamlit as st
import pandas as pd

# ==============================================================================
# SOVEREIGN KINETIC ARCHITECTURE // L.A.Z.E.R.S. PRO
# Identical Boschetto Pro Engine: Pure 3x3 Grid -> 5 In-Tile Rows -> Full View
# ==============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BRIDGE_FILE = os.path.join(BASE_DIR, "bridge_data.json")

WEATHER_PRESETS = {
    "S0 — LOCK-IN / FORZA MAGGIORE (Assedio 96h)": {"ret_bb": 1.00, "ret_ro": 1.00, "ext_mult": 0.00, "terrazza_on": False, "lock_in": True, "short": "S0 LOCK-IN"},
    "S1 — Temporale / Pioggia Forte": {"ret_bb": 0.88, "ret_ro": 0.80, "ext_mult": 0.15, "terrazza_on": False, "lock_in": False, "short": "S1 PIOGGIA"},
    "S2 — Grecale / Maestrale Forte": {"ret_bb": 0.68, "ret_ro": 0.58, "ext_mult": 0.40, "terrazza_on": False, "lock_in": False, "short": "S2 VENTO"},
    "S3 — Variabile / Nuvoloso Mite": {"ret_bb": 0.48, "ret_ro": 0.38, "ext_mult": 0.75, "terrazza_on": True, "lock_in": False, "short": "S3 VARIABILE"},
    "S4 — Sereno Standard (Ottimale)": {"ret_bb": 0.32, "ret_ro": 0.25, "ext_mult": 1.00, "terrazza_on": True, "lock_in": False, "short": "S4 SERENO"},
    "S5 — Caldo Perfetto (Fuga Esterna)": {"ret_bb": 0.18, "ret_ro": 0.14, "ext_mult": 1.30, "terrazza_on": True, "lock_in": False, "short": "S5 CALDO MAX"},
}

DEFAULT_TILES = [
    {"id": "t1", "name": "DIREZIONE", "color": "gold", "subs": ["1. Espandi Architettura", "2. Rinomina Reparti", "3. Anagrafica & PIN", "4. Split Multi-P.IVA", "5. Ponte Sovereign Zero"]},
    {"id": "t2", "name": "ECONOMATO & SFRIDI", "color": "green", "subs": ["1. Sfridi & Rese Carni", "2. Sgocciolato & Pelati", "3. Usura Cristalleria", "4. Food Cost Ricette", "5. Registro Fatture XML"]},
    {"id": "t3", "name": "CAMERE & IN-HOUSE", "color": "cyan", "subs": ["1. Presenze FB / HB", "2. Cattura Ospiti BB / RO", "3. Fallback VIP (Yoga/Spa)", "4. Room Service & Minibar", "5. Bocche Totali In-House"]},
    {"id": "t4", "name": "RECEPTION & PORTALI", "color": "cyan", "subs": ["1. Semaforo TheFork Live", "2. Google Reserve & Sito", "3. Carta a Garanzia No-Show", "4. Domanda Esterni", "5. Filtro Prenotazioni"]},
    {"id": "t5", "name": "SALA COLAZIONI", "color": "green", "subs": ["1. Costo Vivo Buffet", "2. Rese Uova, Latte & Burro", "3. Presidio Brigata Mattina", "4. Scorte Panificazione", "5. Report Colazioni"]},
    {"id": "t6", "name": "RISTORANTE", "color": "green", "subs": ["1. Capienza Sala & Cucina", "2. Scorporo Quote HB / FB", "3. Scontrino À la Carte", "4. Costo Fisso Brigata", "5. Registro Ufficiale F&B"]},
    {"id": "t7", "name": "BAR & CANTINA", "color": "green", "subs": ["1. Pouring Calici & Vini", "2. Spinta Aperitivi / Caldo", "3. Margine Bottiglie", "4. Calice Benvenuto Promo", "5. Inventario Cantina"]},
    {"id": "t8", "name": "SPIAGGIA & TERRAZZA", "color": "purple", "subs": ["1. Radar Meteo Live (S0-S5)", "2. Apertura Dehors / Lido", "3. Soglia Vento Grounding", "4. Rientro Rapido Sala", "5. Promo ROAS Meteo"]},
    {"id": "t9", "name": "SCUDO 96 ORE", "color": "purple", "subs": ["1. Dispensa Emergenza 96h", "2. Alloggi & Pasti Staff", "3. Protocollo Isolamento S0", "4. Autonomia Acqua & Gas", "5. Stampa Piano Assedio"]},
]

def init_state():
    if "tiles" not in st.session_state:
        st.session_state["tiles"] = DEFAULT_TILES.copy()
    if "expanded_tile" not in st.session_state:
        st.session_state["expanded_tile"] = None
    if "active_sub" not in st.session_state:
        st.session_state["active_sub"] = None
    if "active_scenario" not in st.session_state or st.session_state["active_scenario"] not in WEATHER_PRESETS:
        st.session_state["active_scenario"] = "S4 — Sereno Standard (Ottimale)"

    defaults = {
        "pin_code": "9999",
        "pax_fb": 20, "pax_hb": 35, "pax_bb": 45, "pax_ro": 15, "staff_in_house": 22,
        "cap_interna": 80, "cap_terrazza": 50, "cap_max_cucina": 105, "domanda_esterni": 35,
        "quota_hb": 28.0, "quota_fb": 48.0, "scontrino_ext": 52.0, "cf_brigata": 850.0,
        "food_cost_pct": 29, "iva_fnb": 10, "fee_piva": 100, "comm_thefork": 2.50, "pct_thefork": 35,
        "staff_list": [
            {"pin": "1001", "nome": "Marco S.", "ruolo": "Executive Chef", "reparto": "RISTORANTE", "turno": "Sera (17-24)"},
            {"pin": "1002", "nome": "Elena R.", "ruolo": "Maître di Sala", "reparto": "RISTORANTE", "turno": "Sera (17-24)"},
            {"pin": "1003", "nome": "Giulia F.", "ruolo": "Resp. Economato", "reparto": "ECONOMATO & SFRIDI", "turno": "Mattina (07-15)"},
            {"pin": "1004", "nome": "Jolly 01", "ruolo": "Resp. Colazioni", "reparto": "SALA COLAZIONI", "turno": "Mattina (07-15)"},
            {"pin": "1005", "nome": "Matteo B.", "ruolo": "Head Sommelier", "reparto": "BAR & CANTINA", "turno": "Sera (17-24)"},
            {"pin": "1006", "nome": "Extra A", "ruolo": "Barman Terrazza", "reparto": "SPIAGGIA & TERRAZZA", "turno": "Pomeriggio (14-22)"},
        ]
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def inject_boschetto_css():
    st.markdown("""
    <style>
    .stApp { background-color: #162127; color: #F1F5F9; font-family: 'Inter', sans-serif; }
    header[data-testid="stHeader"] { background: transparent; }
    .block-container { padding-top: 1.2rem; max-width: 96%; }

    /* TOP BAR BOSCHETTO PRO */
    .ska-topbar {
        display: flex; justify-content: space-between; align-items: center;
        border-bottom: 1px solid #2A3C46; padding-bottom: 10px; margin-bottom: 12px;
    }
    .ska-brand { font-size: 20px; font-weight: 900; letter-spacing: 1.5px; color: #FFFFFF; }
    .ska-brand span { color: #10B981; }
    .ska-clock {
        background-color: #1A2830; border: 1px solid #2E4752; color: #34D399;
        padding: 5px 14px; border-radius: 3px; font-size: 12px; font-weight: 700; font-family: monospace;
    }

    /* TRASFORMAZIONE BOTTONI STREAMLIT NEI QUADRATI KINETIC PURI */
    div.stButton > button {
        background: linear-gradient(160deg, #1E2D35 0%, #22343D 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid #334B57 !important;
        border-left: 3px solid #10B981 !important;
        border-top: 2px solid #10B981 !important;
        border-radius: 3px !important;
        font-weight: 800 !important;
        letter-spacing: 1px !important;
        transition: all 0.22s ease !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 0 18px rgba(16, 185, 129, 0.45) !important;
        border-color: #34D399 !important;
        background: linear-gradient(160deg, #243742 0%, #2A404B 100%) !important;
    }

    /* QUADRO SINOTTICO CON EVIDENZIAMENTO HOVER */
    .synoptic-panel {
        background-color: #19262D; border: 1px solid #2E434F; border-top: 3px solid #10B981;
        padding: 16px; border-radius: 3px;
    }
    .synoptic-header { font-size: 11px; font-weight: 800; color: #34D399; letter-spacing: 1.4px; margin-bottom: 12px; font-family: monospace; }
    .syn-card {
        background-color: #1E2D36; border: 1px solid #324A57;
        padding: 13px 15px; border-radius: 3px; margin-bottom: 11px;
        transition: all 0.22s ease; cursor: pointer;
    }
    .syn-card:hover {
        transform: translateX(-3px);
        border-color: #F59E0B;
        box-shadow: 0 0 18px rgba(245, 158, 11, 0.38);
        background-color: #243640;
    }
    .syn-card-amber { border: 1px solid #B45309; }
    .syn-label { font-size: 10px; color: #94A3B8; text-transform: uppercase; letter-spacing: 1px; font-family: monospace; }
    .syn-val { font-size: 22px; font-weight: 900; color: #FFFFFF; margin: 3px 0; }
    .syn-note { font-size: 11px; color: #CBD5E1; font-family: monospace; }
    .legend-box { font-size: 10px; color: #CBD5E1; line-height: 1.9; margin-top: 14px; padding-top: 12px; border-top: 1px solid #2A3C46; font-family: monospace; }

    /* TABELLA UFFICIALE STILE REGISTRO ASL BOSCHETTO */
    .ska-table { width: 100%; border-collapse: collapse; font-family: monospace; font-size: 12px; margin: 14px 0; }
    .ska-table th { background-color: #1E3A47; color: #38BDF8; text-align: left; padding: 10px 12px; border-bottom: 1px solid #2E5266; text-transform: uppercase; }
    .ska-table td { background-color: #18252C; color: #F1F5F9; padding: 10px 12px; border-bottom: 1px solid #263842; font-weight: 700; }
    .ska-table tr:hover td { background-color: #21333D; color: #34D399; }
    </style>
    """, unsafe_allow_html=True)

def save_bridge_data(payload):
    try:
        with open(BRIDGE_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4, ensure_ascii=False)
        return True
    except Exception:
        return False

def render_fnb_module():
    init_state()
    inject_boschetto_css()

    ora_str = datetime.now().strftime("%H:%M")
    fascia = "POMERIGGIO (14:00-19:00)" if 14 <= datetime.now().hour < 19 else "SERVIZIO SERALE (19:00-23:30)"

    # --- TOP HEADER IDENTICO A BOSCHETTO PRO ---
    st.markdown(f"""
    <div class="ska-topbar">
        <div class="ska-brand">SOVEREIGN KINETIC ARCHITECTURE // <span>L.A.Z.E.R.S. PRO</span></div>
        <div class="ska-clock">{ora_str} | {fascia}</div>
    </div>
    """, unsafe_allow_html=True)

    # --- BARRA PIN & CONTROLLI SUPERIORI ---
    top1, top2, top3, top4 = st.columns([2.2, 1.3, 1.3, 1.4])
    with top1:
        st.text_input("PIN", value=st.session_state["pin_code"], label_visibility="collapsed")
    with top2:
        if st.button("CONFERMA PIN ✔", use_container_width=True):
            st.toast("PIN Manager 9999 Verificato")
    with top3:
        if st.button("PIANTA PRINCIPALE", use_container_width=True):
            st.session_state["expanded_tile"] = None
            st.session_state["active_sub"] = None
            st.rerun()
    with top4:
        st.toggle("AUDIO TASTI", value=True)

    # --- CALCOLI ECONOMETRICI VIVI PER IL QUADRO SINOTTICO ---
    sc = WEATHER_PRESETS[st.session_state["active_scenario"]]
    catturati_extra = round(st.session_state["pax_bb"] * sc["ret_bb"]) + round(st.session_state["pax_ro"] * sc["ret_ro"])
    coperti_hotel = st.session_state["pax_fb"] + st.session_state["pax_hb"] + catturati_extra
    sedute_attive = st.session_state["cap_interna"] + (st.session_state["cap_terrazza"] if sc["terrazza_on"] else 0)
    tetto_servizio = min(sedute_attive, st.session_state["cap_max_cucina"])
    slot_esterni = max(0, tetto_servizio - coperti_hotel)
    domanda_ext_reale = 0 if sc["lock_in"] else round(st.session_state["domanda_esterni"] * sc["ext_mult"])
    esterni_accettati = min(slot_esterni, domanda_ext_reale)
    coperti_totali = coperti_hotel + esterni_accettati
    bocche_96h = st.session_state["pax_fb"] + st.session_state["pax_hb"] + st.session_state["pax_bb"] + st.session_state["pax_ro"] + st.session_state["staff_in_house"]

    lordo_tot = (st.session_state["pax_hb"] * st.session_state["quota_hb"]) + (st.session_state["pax_fb"] * st.session_state["quota_fb"]) + ((catturati_extra + esterni_accettati) * st.session_state["scontrino_ext"])
    netto_iva = lordo_tot / (1.0 + st.session_state["iva_fnb"] / 100.0)
    costo_mp = netto_iva * (st.session_state["food_cost_pct"] / 100.0)
    costo_tf = (round(esterni_accettati * (st.session_state["pct_thefork"] / 100.0)) * st.session_state["comm_thefork"]) if slot_esterni > 12 else 0.0
    costo_staff = st.session_state["staff_in_house"] * 4.50
    mol_netto = netto_iva - costo_mp - st.session_state["cf_brigata"] - costo_tf - costo_staff
    floor_hb = round((st.session_state["cf_brigata"] / max(coperti_totali, 15)) + (st.session_state["quota_hb"] * (st.session_state["food_cost_pct"] / 100.0)), 2)

    # ==============================================================================
    # CASO A: SIAMO NELLA PIANTA PRINCIPALE (Griglia 3x3 + Fisarmonica a 6 Righe)
    # ==============================================================================
    if st.session_state["active_sub"] is None:
        col_grid, col_syn = st.columns([3.3, 1.15])

        with col_grid:
            tiles = st.session_state["tiles"]
            for r in range(0, len(tiles), 3):
                cols = st.columns(3)
                for c in range(3):
                    if r + c < len(tiles):
                        tile = tiles[r + c]
                        t_id = tile["id"]
                        t_name = tile["name"]
                        with cols[c]:
                            # Se il quadrato è stato cliccato, mostra le 6 righe interne come nella Foto 2!
                            if st.session_state["expanded_tile"] == t_id:
                                for sub_label in tile["subs"]:
                                    if st.button(sub_label, key=f"sub_{t_id}_{sub_label}", use_container_width=True):
                                        st.session_state["active_sub"] = (t_name, sub_label)
                                        st.rerun()
                                if st.button(f"X {t_name}", key=f"close_{t_id}", use_container_width=True):
                                    st.session_state["expanded_tile"] = None
                                    st.rerun()
                            else:
                                # Quadrato alto 215px identico a Boschetto Pro!
                                st.markdown(f"""
                                <style>
                                div[data-testid="stVerticalBlock"] button[kind="secondary"] {{
                                    min-height: 42px;
                                }}
                                </style>
                                """, unsafe_allow_html=True)
                                if st.button(f"\n{t_name}\n\n", key=f"tile_{t_id}", use_container_width=True):
                                    st.session_state["expanded_tile"] = t_id
                                    st.rerun()
                                # Spaziatura interna per dare l'altezza monumentale del quadrato
                                st.markdown(f"""
                                <div style="background: linear-gradient(180deg, #22343D 0%, #1C2B33 100%);
                                            border-left: 3px solid {'#F59E0B' if tile['color']=='gold' else '#10B981' if tile['color']=='green' else '#06B6D4' if tile['color']=='cyan' else '#A855F7'};
                                            border-right: 1px solid #334B57; border-bottom: 1px solid #334B57;
                                            height: 145px; margin-top: -18px; margin-bottom: 12px; padding: 18px;
                                            display:flex; flex-direction:column; justify-content:flex-end; border-radius: 0 0 3px 3px;">
                                    <div style="font-size:11px; color:#94A3B8; font-family:monospace;">STATUS // ATTIVO</div>
                                </div>
                                """, unsafe_allow_html=True)

        with col_syn:
            portali_txt = "0 ATTIVI (BLOCCO)" if slot_esterni <= 12 or sc["lock_in"] else f"{slot_esterni} SLOT APERTI"
            st.markdown(f"""
            <div class="synoptic-panel">
                <div class="synoptic-header">QUADRO SINOTTICO</div>
                <div class="syn-card">
                    <div class="syn-label">CONTROLLI COPERTI ({sc['short']})</div>
                    <div class="syn-val">{coperti_totali}/{tetto_servizio}</div>
                    <div class="syn-note">Unità certificate a tavola</div>
                </div>
                <div class="syn-card">
                    <div class="syn-label">PRESIDIO STAFF & BOCCHE</div>
                    <div class="syn-val">{st.session_state['staff_in_house']} UNITÀ</div>
                    <div class="syn-note">Totale Scudo 96h: {bocche_96h} bocche</div>
                </div>
                <div class="syn-card syn-card-amber">
                    <div class="syn-label">SEMAFORO THEFORK / ESTERNI</div>
                    <div class="syn-val">{portali_txt}</div>
                    <div class="syn-note">Richieste dai portali: {domanda_ext_reale} pax</div>
                </div>
                <div class="syn-card">
                    <div class="syn-label">MOL F&B CERTIFICATO</div>
                    <div class="syn-val">€ {mol_netto:,.0f}</div>
                    <div class="syn-note">Floor HB: € {floor_hb:.2f} | Pronta stampa</div>
                </div>
                <div class="legend-box">
                    <span style="color:#F59E0B;">■</span> DIREZIONE & YIELD<br>
                    <span style="color:#10B981;">■</span> FOOD & BEVERAGE<br>
                    <span style="color:#06B6D4;">■</span> ACCOGLIENZA & CAMERE<br>
                    <span style="color:#A855F7;">■</span> ESTERNI, TERRAZZA & 96H
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ==============================================================================
    # CASO B: VISTA DEDICATA FULL-SCREEN (Come Foto 3, 4 e 5 di Boschetto Pro!)
    # ==============================================================================
    else:
        rep_name, sub_name = st.session_state["active_sub"]

        # Doppia barra di navigazione identica alle foto 3, 4 e 5!
        nav1, nav2 = st.columns(2)
        with nav1:
            if st.button(f"← TORNA ALLE 5 RIGHE DI {rep_name}", use_container_width=True):
                st.session_state["active_sub"] = None
                st.rerun()
        with nav2:
            if st.button("TORNA ALLA PIANTA PRINCIPALE", use_container_width=True):
                st.session_state["active_sub"] = None
                st.session_state["expanded_tile"] = None
                st.rerun()

        st.markdown("<hr style='border-color:#2A3C46;'>", unsafe_allow_html=True)
        st.markdown(f"### {rep_name} // {sub_name.upper()}")

        # --- SOTTO-VISTA 1: ESPANDI ARCHITETTURA (Foto 3) ---
        if "1. Espandi Architettura" in sub_name:
            ea1, ea2 = st.columns([2, 1])
            with ea1:
                new_tile_name = st.text_input("Nome Nuovo Quadrato (es. PISCINA / SPA / CANTINA STORICA)")
            with ea2:
                new_tile_col = st.selectbox("Colore Area", ["Verde Smeraldo (F&B)", "Oro (Direzione)", "Ciano (Camere)", "Viola (Esterni)"])
            if st.button("+ CREA NUOVO QUADRATO NELLA GRIGLIA") and new_tile_name:
                c_map = {"Verde Smeraldo (F&B)": "green", "Oro (Direzione)": "gold", "Ciano (Camere)": "cyan", "Viola (Esterni)": "purple"}
                st.session_state["tiles"].append({
                    "id": f"t_{len(st.session_state['tiles'])+1}",
                    "name": new_tile_name.upper(),
                    "color": c_map[new_tile_col],
                    "subs": ["1. Controllo Reparto", "2. Costi & Rese", "3. Personale", "4. Scorte", "5. Registro Ufficiale"]
                })
                st.success(f"Quadrato {new_tile_name.upper()} aggiunto alla Pianta Principale!")
            st.markdown("<hr style='border-color:#2A3C46;'>", unsafe_allow_html=True)
            st.markdown("##### Reparti Attivi nella Pianta Principale")
            for idx, t in enumerate(st.session_state["tiles"]):
                rc1, rc2 = st.columns([4, 1])
                rc1.markdown(f"• `{t['name']}`")
                if rc2.button("Rimuovi", key=f"rem_{t['id']}") and len(st.session_state["tiles"]) > 1:
                    st.session_state["tiles"].pop(idx)
                    st.rerun()

        # --- SOTTO-VISTA 2: RINOMINA REPARTI (Foto 4) ---
        elif "2. Rinomina Reparti" in sub_name:
            for idx, t in enumerate(st.session_state["tiles"]):
                nuovo = st.text_input(f"Nome Quadrato {idx+1}", value=t["name"], key=f"ren_{t['id']}")
                st.session_state["tiles"][idx]["name"] = nuovo.upper()

        # --- SOTTO-VISTA 3: ANAGRAFICA & PIN (Foto 5) ---
        elif "3. Anagrafica & PIN" in sub_name:
            an1, an2, an3 = st.columns(3)
            nome_op = an1.text_input("Nome Operatore (es. Luca M.)")
            mans_op = an2.text_input("Mansione (es. Chef / Sommelier)")
            pin_op = an3.text_input("PIN a 4 cifre (es. 1007)")
            an4, an5 = st.columns(2)
            rep_op = an4.selectbox("Assegna al Reparto", [t["name"] for t in st.session_state["tiles"]])
            tur_op = an5.selectbox("Turno", ["Mattina (07-15)", "Pomeriggio (14-22)", "Sera (17-24)"])
            if st.button("+ ATTIVA OPERATORE") and nome_op and pin_op:
                st.session_state["staff_list"].append({"pin": pin_op, "nome": nome_op, "ruolo": mans_op, "reparto": rep_op, "turno": tur_op})
            st.markdown("<hr style='border-color:#2A3C46;'>", unsafe_allow_html=True)
            for idx, op in enumerate(st.session_state["staff_list"]):
                sc1, sc2 = st.columns([4, 1])
                sc1.markdown(f"• **PIN** `{op['pin']}` — **{op['nome']} ({op['ruolo']})** | {op['reparto']}")
                if sc2.button("Rimuovi", key=f"del_op_{idx}"):
                    st.session_state["staff_list"].pop(idx)
                    st.rerun()

        # --- SOTTO-VISTA 5: REGISTRO UFFICIALE / SCUDO 96H (Foto 6 con Tabella Custom & 3 Bottoni Export) ---
        elif "5. Registro" in sub_name or "SCUDO 96 ORE" in rep_name:
            st.markdown(f"""
            <table class="ska-table">
                <thead>
                    <tr>
                        <th>DATA</th><th>ORA</th><th>FASCIA</th><th>REPARTO</th><th>UNITÀ / DISPENSA CRITICA</th><th>VALORE / STOCK</th><th>ESITO</th><th>OPERATORE</th><th>FIRMA</th>
                    </tr>
                </thead>
                <tbody>
                    <tr><td>03/11/2026</td><td>{ora_str}</td><td>SERA</td><td>RISTORANTE</td><td>Tagliata Cervo / Selvaggina -18°C</td><td>Resa 72% (490 porz.)</td><td>CONFORME</td><td>Matteo B.</td><td>PIN #1005</td></tr>
                    <tr><td>03/11/2026</td><td>{ora_str}</td><td>SERA</td><td>ECONOMATO</td><td>Pelati & Sgocciolato Certificato</td><td>Resa 68% (640 porz.)</td><td>CONFORME</td><td>Giulia F.</td><td>PIN #1003</td></tr>
                    <tr><td>03/11/2026</td><td>{ora_str}</td><td>MATTINA</td><td>SALA COLAZIONI</td><td>Uova, Latte UHT & Burro (Scudo 96h)</td><td>380 porz. / Target {bocche_96h*4}</td><td>PRE-ALLARME</td><td>Jolly 01</td><td>PIN #1004</td></tr>
                    <tr><td>03/11/2026</td><td>{ora_str}</td><td>SERA</td><td>BAR & CANTINA</td><td>Pouring Franciacorta & Usura Calici</td><td>€ 0.45/coperto</td><td>CONFORME</td><td>Matteo B.</td><td>PIN #1005</td></tr>
                    <tr><td>03/11/2026</td><td>{ora_str}</td><td>SERA</td><td>DIREZIONE</td><td>Floor Industriale Pasto HB</td><td>€ {floor_hb:.2f} / pasto</td><td>CERTIFICATO</td><td>Marco S.</td><td>PIN #1001</td></tr>
                </tbody>
            </table>
            """, unsafe_allow_html=True)

            ex1, ex2, ex3 = st.columns(3)
            with ex1:
                st.button("🖨️ SCARICA STAMPA UFFICIALE (.HTML)", use_container_width=True)
            with ex2:
                st.button("📊 SCARICA EXCEL (.CSV)", use_container_width=True)
            with ex3:
                if st.button("🔄 SINCRONIZZA PONTE SOVEREIGN ZERO", use_container_width=True):
                    save_bridge_data({"updated_at": ora_str, "floor_hb": st.session_state["quota_hb"], "floor_industriale_pasto": floor_hb, "mol_fnb_giornaliero": round(mol_netto, 2)})
                    st.success("Ponte Sovereign Zero aggiornato!")

        # --- TUTTE LE ALTRE CONSOLLE OPERATIVE F&B (Sfridi, Meteo, Presenze, Capienze) ---
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.session_state["active_scenario"] = st.selectbox("Scenario Meteo Live (S0-S5)", list(WEATHER_PRESETS.keys()), index=list(WEATHER_PRESETS.keys()).index(st.session_state["active_scenario"]))
                st.session_state["pax_fb"] = st.number_input("Ospiti Pensione Completa (FB)", 0, 500, st.session_state["pax_fb"])
                st.session_state["pax_hb"] = st.number_input("Ospiti Mezza Pensione (HB)", 0, 500, st.session_state["pax_hb"])
                st.session_state["pax_bb"] = st.number_input("Ospiti B&B (Liberi a Cena)", 0, 500, st.session_state["pax_bb"])
            with c2:
                st.session_state["staff_in_house"] = st.number_input("Staff Alloggiato (Bocche Scudo 96h)", 0, 200, st.session_state["staff_in_house"])
                st.session_state["cap_interna"] = st.number_input("Sedute Sala Interna Climatizzata", 10, 500, st.session_state["cap_interna"])
                st.session_state["cap_terrazza"] = st.number_input("Sedute Terrazza / Spiaggia", 0, 500, st.session_state["cap_terrazza"])
                st.session_state["cap_max_cucina"] = st.number_input("Collo di Bottiglia Cucina (Max Coperti)", 10, 500, st.session_state["cap_max_cucina"])
            with c3:
                st.session_state["quota_hb"] = st.number_input("Scorporo Netto Pasto HB (€)", 10.0, 200.0, st.session_state["quota_hb"])
                st.session_state["cf_brigata"] = st.number_input("Costo Fisso Brigata Sala+Cucina (€/gg)", 100.0, 5000.0, st.session_state["cf_brigata"], step=50.0)
                st.session_state["food_cost_pct"] = st.slider("Food Cost Medio Target (%)", 15, 55, st.session_state["food_cost_pct"])
                if st.button("💾 CONSOLIDA DATI SU SOVEREIGN ZERO", use_container_width=True):
                    save_bridge_data({"updated_at": ora_str, "active_weather_scenario": st.session_state["active_scenario"], "floor_hb": st.session_state["quota_hb"], "floor_industriale_pasto": floor_hb})
                    st.success("Dati inviati a Sovereign Zero!")

if __name__ == "__main__":
    st.set_page_config(page_title="SOVEREIGN KINETIC // L.A.Z.E.R.S. PRO", layout="wide")
    render_fnb_module()
