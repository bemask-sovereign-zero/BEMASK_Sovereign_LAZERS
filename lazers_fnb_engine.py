import os
import json
from datetime import datetime
import urllib.request
import streamlit as st
import pandas as pd

# ==============================================================================
# SOVEREIGN KINETIC ARCHITECTURE // L.A.Z.E.R.S. PRO
# Live Analytics & Zone Econometrics Retention System — Executive Manager OS
# ==============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BRIDGE_FILE = os.path.join(BASE_DIR, "bridge_data.json")

KINETIC_CSS = """
<style>
.stApp { background-color: #07090B; color: #E2E8F0; font-family: 'Inter', sans-serif; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.5rem; max-width: 96%; }

/* TOP HEADER STILE BOSCHETTO PRO */
.ska-topbar {
    display: flex; justify-content: space-between; align-items: center;
    border-bottom: 1px solid #1E293B; padding-bottom: 10px; margin-bottom: 14px;
}
.ska-brand { font-size: 20px; font-weight: 800; letter-spacing: 2.5px; color: #F8FAFC; }
.ska-brand span { color: #10B981; }
.ska-clock {
    background-color: #0F172A; border: 1px solid #10B981; color: #10B981;
    padding: 5px 14px; border-radius: 4px; font-size: 12px; font-weight: 700; letter-spacing: 1px;
}

/* PIASTRELLE KINETIC 3x3 CON GLOW AL PASSAGGIO DEL MOUSE */
.kinetic-tile {
    background: linear-gradient(145deg, #0F151C 0%, #131B24 100%);
    height: 155px; border-radius: 4px; padding: 18px;
    display: flex; flex-direction: column; justify-content: space-between;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    cursor: pointer; position: relative; overflow: hidden;
    border: 1px solid #1E293B; margin-bottom: 12px;
}
.kinetic-tile:hover {
    transform: translateY(-4px) scale(1.01);
    background: linear-gradient(145deg, #151F2A 0%, #1B2836 100%);
}
.tile-gold { border-left: 4px solid #F59E0B; border-top: 2px solid #F59E0B; }
.tile-gold:hover { box-shadow: 0 0 22px rgba(245, 158, 11, 0.45); border-color: #FBBF24; }

.tile-green { border-left: 4px solid #10B981; border-top: 2px solid #10B981; }
.tile-green:hover { box-shadow: 0 0 22px rgba(16, 185, 129, 0.45); border-color: #34D399; }

.tile-cyan { border-left: 4px solid #06B6D4; border-top: 2px solid #06B6D4; }
.tile-cyan:hover { box-shadow: 0 0 22px rgba(6, 182, 212, 0.45); border-color: #22D3EE; }

.tile-purple { border-left: 4px solid #A855F7; border-top: 2px solid #A855F7; }
.tile-purple:hover { box-shadow: 0 0 22px rgba(168, 85, 247, 0.45); border-color: #C084FC; }

.tile-title { font-size: 16px; font-weight: 800; letter-spacing: 1.5px; color: #FFFFFF; text-transform: uppercase; text-align: center; margin-top: 6px; }
.tile-metric { font-size: 20px; font-weight: 800; color: #E2E8F0; text-align: center; }
.tile-sub { font-size: 11px; color: #94A3B8; text-align: center; letter-spacing: 0.8px; text-transform: uppercase; }

/* QUADRO SINOTTICO LATERALE DESTRO */
.synoptic-panel {
    background-color: #0B1016; border: 1px solid #1E293B; border-top: 3px solid #10B981;
    padding: 16px; border-radius: 4px;
}
.synoptic-header { font-size: 11px; font-weight: 800; color: #10B981; letter-spacing: 1.5px; margin-bottom: 12px; text-transform: uppercase; }
.syn-card {
    background-color: #111822; border: 1px solid #1E293B; border-left: 3px solid #10B981;
    padding: 12px 14px; border-radius: 3px; margin-bottom: 10px;
    transition: all 0.2s ease;
}
.syn-card:hover { border-color: #F59E0B; box-shadow: 0 0 14px rgba(245, 158, 11, 0.25); }
.syn-label { font-size: 10px; color: #94A3B8; text-transform: uppercase; letter-spacing: 1px; }
.syn-val { font-size: 22px; font-weight: 800; color: #FFFFFF; margin: 2px 0; }
.syn-note { font-size: 11px; color: #10B981; }

.legend-box { font-size: 10px; color: #CBD5E1; line-height: 1.8; margin-top: 12px; padding-top: 10px; border-top: 1px solid #1E293B; letter-spacing: 0.8px; }
</style>
"""

WEATHER_PRESETS = {
    "S0 — LOCK-IN / FORZA MAGGIORE (Assedio 96h)": {"ret_bb": 1.00, "ret_ro": 1.00, "ext_mult": 0.00, "terrazza_on": False, "lock_in": True, "short": "S0 LOCK-IN"},
    "S1 — Temporale / Pioggia Forte": {"ret_bb": 0.88, "ret_ro": 0.80, "ext_mult": 0.15, "terrazza_on": False, "lock_in": False, "short": "S1 PIOGGIA"},
    "S2 — Grecale / Maestrale Forte": {"ret_bb": 0.68, "ret_ro": 0.58, "ext_mult": 0.40, "terrazza_on": False, "lock_in": False, "short": "S2 VENTO"},
    "S3 — Variabile / Nuvoloso Mite": {"ret_bb": 0.48, "ret_ro": 0.38, "ext_mult": 0.75, "terrazza_on": True, "lock_in": False, "short": "S3 VARIABILE"},
    "S4 — Sereno Standard (Ottimale)": {"ret_bb": 0.32, "ret_ro": 0.25, "ext_mult": 1.00, "terrazza_on": True, "lock_in": False, "short": "S4 SERENO"},
    "S5 — Caldo Perfetto (Fuga Esterna)": {"ret_bb": 0.18, "ret_ro": 0.14, "ext_mult": 1.30, "terrazza_on": True, "lock_in": False, "short": "S5 CALDO MAX"},
}

def save_bridge_data(payload):
    try:
        with open(BRIDGE_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4, ensure_ascii=False)
        return True
    except Exception:
        return False

def init_state():
    defaults = {
        "pin_code": "9999",
        "active_view": "PIANTA PRINCIPALE",
        "active_scenario": "S4 — Sereno Standard (Ottimale)",
        "pax_fb": 20, "pax_hb": 35, "pax_bb": 45, "pax_ro": 15, "staff_in_house": 22,
        "cap_interna": 80, "cap_terrazza": 50, "cap_max_cucina": 105, "domanda_esterni": 35,
        "quota_hb": 28.0, "quota_fb": 48.0, "scontrino_ext": 52.0, "cf_brigata": 850.0,
        "food_cost_pct": 29, "iva_fnb": 10, "fee_piva": 100, "comm_thefork": 2.50, "pct_thefork": 35
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def render_fnb_module():
    init_state()
    st.markdown(KINETIC_CSS, unsafe_allow_html=True)

    ora_str = datetime.now().strftime("%H:%M")
    fascia = "SERVIZIO SERALE (18:00-23:00)" if datetime.now().hour >= 18 else "POMERIGGIO / PREP (14:00-18:00)"

    # --- TOP BAR IDENTICA A BOSCHETTO PRO ---
    st.markdown(f"""
    <div class="ska-topbar">
        <div class="ska-brand">SOVEREIGN KINETIC ARCHITECTURE // <span>L.A.Z.E.R.S. PRO</span></div>
        <div class="ska-clock">{ora_str} | {fascia}</div>
    </div>
    """, unsafe_allow_html=True)

    # --- BARRA COMANDI RAPIDI (PIN, CONFERMA, PIANTA PRINCIPALE, SELETTORE) ---
    b1, b2, b3, b4 = st.columns([2.2, 1.3, 1.3, 1.4])
    with b1:
        st.text_input("PIN Manager", value=st.session_state["pin_code"], label_visibility="collapsed")
    with b2:
        if st.button("CONFERMA PIN ✔", use_container_width=True):
            st.toast("Accesso Manager L.A.Z.E.R.S. Autorizzato")
    with b3:
        if st.button("PIANTA PRINCIPALE", use_container_width=True):
            st.session_state["active_view"] = "PIANTA PRINCIPALE"
            st.rerun()
    with b4:
        audio_on = st.toggle("AUDIO TASTI / LIVE", value=True)

    # --- MOTORE DI CALCOLO IN TEMPO REALE ---
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
    # LAYOUT CENTRALE: GRIGLIA 3x3 A SINISTRA + QUADRO SINOTTICO A DESTRA
    # ==============================================================================
    col_matrix, col_synoptic = st.columns([3.3, 1.15])

    with col_matrix:
        tiles = [
            # RIGA 1
            ("DIREZIONE F&B", f"€ {mol_netto:,.0f}", f"MOL Netto Oggi | P.IVA {st.session_state['fee_piva']}%", "tile-gold"),
            ("ECONOMATO & SFRIDI", f"{st.session_state['food_cost_pct']}% TARGET", "Rese Carni, Sgocciolato & Calici", "tile-green"),
            ("PRESENZE IN-HOUSE", f"{coperti_hotel} PAX", f"HB/FB: {st.session_state['pax_hb']+st.session_state['pax_fb']} | Catturati: +{catturati_extra}", "tile-cyan"),
            # RIGA 2
            ("RADAR METEO", sc["short"], "Retention & Apertura Zone", "tile-gold"),
            ("SALA & CUCINA", f"{coperti_totali}/{tetto_servizio}", f"Sedute Attive: {sedute_attive} posti", "tile-green"),
            ("SCUDO 96 ORE", f"{bocche_96h} BOCCHE", f"Ospiti + {st.session_state['staff_in_house']} Staff Residente", "tile-cyan"),
            # RIGA 3
            ("BAR & CANTINA", "POURING LIVE", f"Scontrino À la Carte: € {st.session_state['scontrino_ext']:.0f}", "tile-green"),
            ("TERRAZZA & PORTALI", f"{slot_esterni} SLOT", "CHIUDERE THEFORK" if slot_esterni <= 12 else "THEFORK & GOOGLE ON", "tile-purple"),
            ("PONTE SOVEREIGN", f"€ {floor_hb:.2f}", "Floor Industriale Pasto HB", "tile-purple"),
        ]

        for row_idx in range(0, 9, 3):
            cols = st.columns(3)
            for col_idx in range(3):
                t_name, t_metric, t_sub, t_class = tiles[row_idx + col_idx]
                with cols[col_idx]:
                    st.markdown(f"""
                    <div class="kinetic-tile {t_class}">
                        <div class="tile-title">{t_name}</div>
                        <div class="tile-metric">{t_metric}</div>
                        <div class="tile-sub">{t_sub}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"APRI {t_name}", key=f"btn_{t_name}", use_container_width=True):
                        st.session_state["active_view"] = t_name

    with col_synoptic:
        stato_portali = "0 COMMISSIONI (CHIUSO)" if slot_esterni <= 12 or sc["lock_in"] else f"{slot_esterni} POSTI APERTI"
        st.markdown(f"""
        <div class="synoptic-panel">
            <div class="synoptic-header">QUADRO SINOTTICO</div>
            <div class="syn-card">
                <div class="syn-label">CARICO LINEA CUCINA</div>
                <div class="syn-val">{coperti_totali}/{tetto_servizio}</div>
                <div class="syn-note">Coperti totali certificati</div>
            </div>
            <div class="syn-card">
                <div class="syn-label">PRESIDIO BRIGATA & STAFF</div>
                <div class="syn-val">{st.session_state['staff_in_house']} UNITÀ</div>
                <div class="syn-note">Costo fisso: € {st.session_state['cf_brigata']:,.0f}/gg</div>
            </div>
            <div class="syn-card">
                <div class="syn-label">SEMAFORO PORTALI ESTERNI</div>
                <div class="syn-val">{stato_portali}</div>
                <div class="syn-note">Richiesta sul territorio: {domanda_ext_reale} pax</div>
            </div>
            <div class="syn-card">
                <div class="syn-label">SCUDO AUTONOMIA 96H</div>
                <div class="syn-val">{bocche_96h * 4} PASTI</div>
                <div class="syn-note">Pronto per isolamento/grounding</div>
            </div>
            <div class="legend-box">
                <span style="color:#F59E0B;">■</span> DIREZIONE & YIELD<br>
                <span style="color:#10B981;">■</span> FOOD, CUCINA & CANTINA<br>
                <span style="color:#06B6D4;">■</span> IN-HOUSE & SCUDO 96H<br>
                <span style="color:#A855F7;">■</span> ESTERNE, PORTALI & PONTE
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ==============================================================================
    # CONSOLLE DI DETTAGLIO DEL REPARTO SELEZIONATO (SOTTO LA PIANTA)
    # ==============================================================================
    st.markdown("---")
    vista = st.session_state["active_view"]
    st.markdown(f"#### ⚡ CONSOLLE OPERATIVA ATTIVA: `{vista}` *(Clicca su una delle 9 piastrelle sopra per cambiare reparto)*")

    if vista in ["PIANTA PRINCIPALE", "RADAR METEO", "PRESENZE IN-HOUSE", "SALA & CUCINA"]:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.session_state["active_scenario"] = st.selectbox("Scenario Meteo (S0-S5)", list(WEATHER_PRESETS.keys()), index=list(WEATHER_PRESETS.keys()).index(st.session_state["active_scenario"]))
            st.session_state["pax_fb"] = st.number_input("Ospiti FB", 0, 500, st.session_state["pax_fb"])
            st.session_state["pax_hb"] = st.number_input("Ospiti HB", 0, 500, st.session_state["pax_hb"])
        with c2:
            st.session_state["pax_bb"] = st.number_input("Ospiti BB (Liberi)", 0, 500, st.session_state["pax_bb"])
            st.session_state["pax_ro"] = st.number_input("Ospiti RO (Liberi)", 0, 500, st.session_state["pax_ro"])
            st.session_state["staff_in_house"] = st.number_input("Staff Alloggiato (Bocche)", 0, 200, st.session_state["staff_in_house"])
        with c3:
            st.session_state["cap_interna"] = st.number_input("Sedute Sala Interna", 10, 500, st.session_state["cap_interna"])
            st.session_state["cap_terrazza"] = st.number_input("Sedute Terrazza/Spiaggia", 0, 500, st.session_state["cap_terrazza"])
            st.session_state["cap_max_cucina"] = st.number_input("Collo Bottiglia Cucina", 10, 500, st.session_state["cap_max_cucina"])

    elif vista in ["ECONOMATO & SFRIDI", "BAR & CANTINA"]:
        ec1, ec2, ec3 = st.columns(3)
        with ec1:
            ref = st.text_input("Referenza Piatto / Calice", value="Tagliata di Cervo / Franciacorta")
            p_lordo = st.number_input("Prezzo Vendita Lordo (€)", value=26.0, step=1.0)
        with ec2:
            c_kg = st.number_input("Costo Fattura Netto (€/Kg o Bott.)", value=24.0, step=0.5)
            dose = st.number_input("Dose Servita (Kg o frazione)", value=0.200, step=0.02, format="%.3f")
        with ec3:
            resa = st.slider("Resa Reale Post-Sfrido (%)", 35, 100, 72)
            vetri = st.number_input("Quota Rottura Calici + Guarnizione (€)", value=1.55, step=0.10)
        p_net = p_lordo / 1.10
        c_vivo = ((c_kg * dose) / (resa / 100.0)) + vetri
        st.success(f"**{ref}** ➔ Ricavo Netto: **€ {p_net:.2f}** | Costo Vivo Reale (con sfrido): **€ {c_vivo:.2f}** | Margine Netto: **€ {p_net - c_vivo:.2f}** ({(c_vivo/p_net*100):.1f}% Food Cost)")

    elif vista == "SCUDO 96 ORE":
        df_scudo = pd.DataFrame([
            {"Dispensa Critica": "Farine, Lievito & Panificazione", "Stock (Porzioni)": 520, "Target 96h": bocche_96h * 4},
            {"Dispensa Critica": "Uova, Latte UHT & Burro Colazione", "Stock (Porzioni)": 380, "Target 96h": bocche_96h * 4},
            {"Dispensa Critica": "Proteine Nobili / Selvaggina (-18°C)", "Stock (Porzioni)": 490, "Target 96h": bocche_96h * 4},
            {"Dispensa Critica": "Pasta, Riso Carnaroli & Pelati", "Stock (Porzioni)": 640, "Target 96h": bocche_96h * 4},
        ])
        df_scudo["Giorni Autonomia"] = (df_scudo["Stock (Porzioni)"] / max(1, bocche_96h)).round(1)
        st.dataframe(df_scudo, use_container_width=True, hide_index=True)

    elif vista in ["DIREZIONE F&B", "TERRAZZA & PORTALI", "PONTE SOVEREIGN"]:
        d1, d2, d3 = st.columns(3)
        with d1:
            st.session_state["quota_hb"] = st.number_input("Scorporo HB (€)", 10.0, 200.0, st.session_state["quota_hb"])
            st.session_state["cf_brigata"] = st.number_input("Costo Fisso Brigata (€/gg)", 100.0, 5000.0, st.session_state["cf_brigata"], step=50.0)
        with d2:
            st.session_state["food_cost_pct"] = st.slider("Food Cost Medio (%)", 15, 55, st.session_state["food_cost_pct"])
            st.session_state["fee_piva"] = st.slider("Quota P.IVA Ristorazione (%)", 10, 100, st.session_state["fee_piva"])
        with d3:
            st.write(f"Floor Industriale Pasto HB: **€ {floor_hb:.2f}**")
            if st.button("💾 CONSOLIDA BRIDGE PER SOVEREIGN ZERO", use_container_width=True):
                save_bridge_data({
                    "updated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "active_weather_scenario": st.session_state["active_scenario"],
                    "floor_hb": st.session_state["quota_hb"],
                    "floor_industriale_pasto": floor_hb,
                    "mol_fnb_giornaliero": round(mol_netto, 2)
                })
                st.success("✅ Ponte sincronizzato con Sovereign Zero!")

if __name__ == "__main__":
    st.set_page_config(page_title="SOVEREIGN KINETIC // L.A.Z.E.R.S. PRO", layout="wide")
    render_fnb_module()
