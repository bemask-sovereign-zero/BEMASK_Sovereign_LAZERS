import os
import json
from datetime import datetime
import urllib.request
import streamlit as st
import pandas as pd

# ==============================================================================
# BEMASK // L.A.Z.E.R.S. MONUMENTAL CORE (Modulo 2.1 + 2.2)
# Live Analytics & Zone Econometrics Retention System
# ==============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BRIDGE_FILE = os.path.join(BASE_DIR, "bridge_data.json")
PROFILES_DIR = os.path.join(BASE_DIR, "profiles")
os.makedirs(PROFILES_DIR, exist_ok=True)

CUSTOM_CSS = """
<style>
.stApp { background-color: #050505; color: #E4E4E4; }
.lazers-banner {
    background: linear-gradient(90deg, #0A0A0A 0%, #161616 100%);
    border-left: 4px solid #00FFAA;
    padding: 16px 22px;
    border-radius: 6px;
    margin-bottom: 18px;
}
.lazers-title { font-size: 24px; font-weight: 800; letter-spacing: 1.8px; color: #FFFFFF; margin: 0; }
.lazers-sub { font-size: 12px; color: #00FFAA; text-transform: uppercase; letter-spacing: 1.2px; margin-top: 4px; }
.box-red { background-color: #260707; border: 1px solid #FF3B3B; padding: 14px; border-radius: 6px; color: #FFB3B3; margin-bottom: 12px; }
.box-amber { background-color: #241905; border: 1px solid #FFB020; padding: 14px; border-radius: 6px; color: #FFE2A8; margin-bottom: 12px; }
.box-green { background-color: #062115; border: 1px solid #00FFAA; padding: 14px; border-radius: 6px; color: #A8FFE0; margin-bottom: 12px; }
div[data-testid="stMetric"] { background-color: #0E0E0E; border: 1px solid #242424; padding: 12px; border-radius: 6px; }
</style>
<div class="lazers-banner">
    <p class="lazers-title">BEMASK // L.A.Z.E.R.S.</p>
    <p class="lazers-sub">Live Analytics & Zone Econometrics Retention System — F&B, Economato, Scudo 96h & Ponte Sovereign</p>
</div>
"""

WEATHER_PRESETS = {
    "S0 — LOCK-IN / FORZA MAGGIORE (Grounding & Assedio 96h)": {
        "ret_bb": 1.00, "ret_ro": 1.00, "ext_mult": 0.00, "terrazza_on": False, "lock_in": True,
        "badge": "🔴 LOCK-IN TOTALE (GROUNDING)",
        "action": "CHIUDERE TheFork e portali esterni. Attivare Menu Assedio 96h (Ospiti + Staff In-House) e dirottare budget escursioni saltate su Cantina/Spa."
    },
    "S1 — Temporale / Pioggia Forte / Tormenta": {
        "ret_bb": 0.88, "ret_ro": 0.80, "ext_mult": 0.15, "terrazza_on": False, "lock_in": False,
        "badge": "🌧️ ALLERTA PIOGGIA / RIENTRO MASSICCIO",
        "action": "Terrazza/Dehors CHIUSI. Alta ritenzione interna RO/BB: bloccare sconti portali esterni e proteggere la linea cucina."
    },
    "S2 — Grecale / Maestrale Forte / Freddo Improvviso": {
        "ret_bb": 0.68, "ret_ro": 0.58, "ext_mult": 0.40, "terrazza_on": False, "lock_in": False,
        "badge": "💨 VENTO TESO / ESCURSIONE TERMICA",
        "action": "Servizio concentrato in Sala Climatizzata. Spingere Calici Importanti, Degustazioni Calde e Carta Vini strutturati."
    },
    "S3 — Variabile / Nuvoloso Mite": {
        "ret_bb": 0.48, "ret_ro": 0.38, "ext_mult": 0.75, "terrazza_on": True, "lock_in": False,
        "badge": "⛅ VARIABILE / EQUILIBRIO FLUSSI",
        "action": "Apertura parziale sedute esterne con pre-allerta rientro rapido. Mantenere attivo Google Reserve."
    },
    "S4 — Sereno Standard (Operatività Ottimale)": {
        "ret_bb": 0.32, "ret_ro": 0.25, "ext_mult": 1.00, "terrazza_on": True, "lock_in": False,
        "badge": "☀️ SERENO / PIENA CAPACITÀ",
        "action": "Sala Interna + Terrazza attive al 100%. Rubinetti esterni aperti su Sito Diretto e Google Reserve."
    },
    "S5 — Caldo Perfetto / Alta Pressione (Dispersione Esterna)": {
        "ret_bb": 0.18, "ret_ro": 0.14, "ext_mult": 1.30, "terrazza_on": True, "lock_in": False,
        "badge": "🔥 ALTA DISPERSIONE / FUGA OSPITI",
        "action": "Ospiti RO/BB mangiano fuori: APRIRE TheFork/Google e lanciare Promo Lampo (Calice Benvenuto a costo vivo) per saturare i tavoli vuoti."
    }
}

def classify_day_scenario(am_rain, pm_rain, am_code, pm_code, max_wind):
    if max_wind >= 48 or pm_rain >= 25.0:
        return "S0 — LOCK-IN / FORZA MAGGIORE (Grounding & Assedio 96h)"
    am_bad = (am_rain >= 3.0) or (am_code in [61, 63, 65, 71, 73, 75, 80, 81, 82, 95, 96, 99])
    pm_bad = (pm_rain >= 3.0) or (pm_code in [61, 63, 65, 71, 73, 75, 80, 81, 82, 95, 96, 99])
    if pm_bad and am_bad:
        return "S1 — Temporale / Pioggia Forte / Tormenta"
    if max_wind >= 28 or pm_bad:
        return "S2 — Grecale / Maestrale Forte / Freddo Improvviso"
    am_uncertain = (am_rain >= 0.8) or (am_code in [2, 3, 45, 48, 51, 53, 55])
    pm_uncertain = (pm_rain >= 0.8) or (pm_code in [2, 3, 45, 48, 51, 53, 55])
    if am_uncertain or pm_uncertain:
        return "S3 — Variabile / Nuvoloso Mite"
    if max_wind <= 15 and am_rain == 0 and pm_rain == 0 and pm_code in [0, 1]:
        return "S5 — Caldo Perfetto / Alta Pressione (Dispersione Esterna)"
    return "S4 — Sereno Standard (Operatività Ottimale)"

def fetch_live_weather(lat=42.92, lon=10.75):
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            "&hourly=precipitation,weathercode,windspeed_10m&forecast_days=1&timezone=Europe%2FRome"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "BEMASK-LAZERS/2.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        h = data.get("hourly", {})
        rain = h.get("precipitation", [0]*24)
        codes = h.get("weathercode", [0]*24)
        winds = h.get("windspeed_10m", [0]*24)
        am_rain = sum(rain[8:14])
        pm_rain = sum(rain[17:23])
        am_code = max(codes[8:14]) if codes[8:14] else 0
        pm_code = max(codes[17:23]) if codes[17:23] else 0
        max_wind = max(winds) if winds else 10.0
        scen = classify_day_scenario(am_rain, pm_rain, am_code, pm_code, max_wind)
        return {"ok": True, "scenario": scen, "am_rain": round(am_rain, 1), "pm_rain": round(pm_rain, 1), "max_wind": round(max_wind, 1)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def save_bridge_data(payload):
    try:
        with open(BRIDGE_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4, ensure_ascii=False)
        return True
    except Exception:
        return False

def render_fnb_module():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    if "active_scenario" not in st.session_state:
        st.session_state["active_scenario"] = "S4 — Sereno Standard (Operatività Ottimale)"

    col_w1, col_w2, col_w3 = st.columns([1.2, 1.2, 2.6])
    with col_w1:
        lat_in = st.number_input("Latitudine Struttura", value=42.920, format="%.3f")
        lon_in = st.number_input("Longitudine Struttura", value=10.750, format="%.3f")
    with col_w2:
        st.write("")
        if st.button("📡 SINCRONIZZA RADAR METEO LIVE", width="stretch"):
            res_w = fetch_live_weather(lat_in, lon_in)
            if res_w["ok"]:
                st.session_state["active_scenario"] = res_w["scenario"]
                st.toast(f"Meteo Live: Vento max {res_w['max_wind']} km/h | Pioggia PM {res_w['pm_rain']} mm")
            else:
                st.warning("Radar offline, mantenuto controllo manuale.")
        soglia_nodi_vento = st.number_input("Soglia Grounding Vento (km/h)", value=45, step=5)
    with col_w3:
        scenario_list = list(WEATHER_PRESETS.keys())
        idx_scen = scenario_list.index(st.session_state["active_scenario"]) if st.session_state["active_scenario"] in scenario_list else 4
        selected_scen = st.selectbox("⚡ Scenario Operativo Attivo (S0 - S5)", scenario_list, index=idx_scen)
        st.session_state["active_scenario"] = selected_scen
        sc_data = WEATHER_PRESETS[selected_scen]
        st.caption(f"**{sc_data['badge']}** ➔ {sc_data['action']}")

    st.markdown("---")

    p_col1, p_col2, p_col3, p_col4 = st.columns(4)
    with p_col1:
        st.markdown("##### 👥 1. Presenze In-House")
        pax_fb = st.number_input("Ospiti in Pensione Completa (FB)", min_value=0, value=20, step=2)
        pax_hb = st.number_input("Ospiti in Mezza Pensione (HB)", min_value=0, value=35, step=2)
        pax_bb = st.number_input("Ospiti in B&B (Liberi a Cena)", min_value=0, value=45, step=2)
        pax_ro = st.number_input("Ospiti in Solo Camera (RO)", min_value=0, value=15, step=2)
        staff_in_house = st.number_input("Staff Alloggiato in Struttura (Bocche)", min_value=0, value=22, step=1)

    with p_col2:
        st.markdown("##### 🏛️ 2. DNA Zone & Capienze")
        cap_interna = st.number_input("Sedute Sala Interna Climatizzata", min_value=10, value=80, step=5)
        cap_terrazza = st.number_input("Sedute Terrazza / Dehors / Spiaggia", min_value=0, value=50, step=5)
        cap_max_cucina = st.number_input("Collo di Bottiglia Cucina (Max Coperti)", min_value=10, value=105, step=5)
        domanda_esterni_base = st.number_input("Richiesta Media Clienti Esterni", min_value=0, value=35, step=5)
        soglia_carta_garanzia = st.number_input("Soglia Pax Carta a Garanzia (Anti No-Show)", min_value=2, value=4, step=1)

    with p_col3:
        st.markdown("##### 💶 3. Scorpori & Costi Fissi")
        quota_pasto_hb = st.number_input("Scorporo Netto Pasto HB (€)", min_value=10.0, value=28.0, step=1.0)
        quota_pasto_fb = st.number_input("Scorporo Netto Pasti FB (€)", min_value=20.0, value=48.0, step=1.0)
        scontrino_alacarte = st.number_input("Scontrino Medio À la Carte / Esterni (€)", min_value=15.0, value=52.0, step=2.0)
        cf_brigata = st.number_input("Costo Fisso Giornaliero Brigata Sala+Cucina (€)", min_value=100.0, value=850.0, step=50.0)
        food_cost_pct = st.slider("Food & Beverage Cost Medio Target (%)", 15, 55, 29)

    with p_col4:
        st.markdown("##### 🏛️ 4. Split Multi-P.IVA & Portali")
        iva_media_fnb = st.selectbox("Aliquota IVA Prevalente F&B (%)", [10, 22], index=0)
        fee_gestore_fnb = st.slider("Quota Spettante a P.IVA Ristorazione (%)", 10, 100, 100)
        comm_thefork = st.number_input("Costo Commissione TheFork (€/coperto)", min_value=0.0, value=2.50, step=0.10)
        quota_thefork_pct = st.slider("% Esterni provenienti da TheFork", 0, 100, 35)

    catturati_bb = round(pax_bb * sc_data["ret_bb"])
    catturati_ro = round(pax_ro * sc_data["ret_ro"])
    catturati_extra_hotel = catturati_bb + catturati_ro
    coperti_garantiti_hotel = pax_fb + pax_hb
    coperti_totali_hotel = coperti_garantiti_hotel + catturati_extra_hotel

    sedute_disponibili_oggi = cap_interna + (cap_terrazza if sc_data["terrazza_on"] else 0)
    tetto_reale_servizio = min(sedute_disponibili_oggi, cap_max_cucina)
    slot_liberi_per_esterni = max(0, tetto_reale_servizio - coperti_totali_hotel)

    domanda_ext_meteo = 0 if sc_data["lock_in"] else round(domanda_esterni_base * sc_data["ext_mult"])
    esterni_accettati = min(slot_liberi_per_esterni, domanda_ext_meteo)
    coperti_totali = coperti_totali_hotel + esterni_accettati
    bocche_totali_assedio = pax_fb + pax_hb + pax_bb + pax_ro + staff_in_house

    ricavo_lordo_hb_fb = (pax_hb * quota_pasto_hb) + (pax_fb * quota_pasto_fb)
    ricavo_lordo_extra_catturati = catturati_extra_hotel * scontrino_alacarte
    ricavo_lordo_esterni = esterni_accettati * scontrino_alacarte
    fatturato_lordo_tot = ricavo_lordo_hb_fb + ricavo_lordo_extra_catturati + ricavo_lordo_esterni

    fatturato_netto_iva = fatturato_lordo_tot / (1.0 + (iva_media_fnb / 100.0))
    coperti_da_thefork = round(esterni_accettati * (quota_thefork_pct / 100.0)) if slot_liberi_per_esterni > 12 else 0
    costo_comm_portali = coperti_da_thefork * comm_thefork
    costo_materie_prime = fatturato_netto_iva * (food_cost_pct / 100.0)
    costo_pasti_staff = staff_in_house * 4.50

    margine_operativo_netto = fatturato_netto_iva - costo_materie_prime - cf_brigata - costo_comm_portali - costo_pasti_staff
    quota_societa_fnb = margine_operativo_netto * (fee_gestore_fnb / 100.0)
    quota_casa_madre = margine_operativo_netto - quota_societa_fnb

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Sedute Attive Oggi", f"{sedute_disponibili_oggi} posti", "Terrazza ON" if sc_data["terrazza_on"] else "Solo Interno")
    k2.metric("Ospiti BB/RO Catturati", f"+{catturati_extra_hotel} pax", f"su {pax_bb + pax_ro} liberi")
    k3.metric("Coperti Totali Serviti", f"{coperti_totali} / {tetto_reale_servizio}", f"Esterni: {esterni_accettati}")
    k4.metric("Ricavo Netto (ex IVA)", f"€ {fatturato_netto_iva:,.0f}", f"Lordo: € {fatturato_lordo_tot:,.0f}")
    k5.metric("MOL F&B Pulito Oggi", f"€ {margine_operativo_netto:,.0f}", f"Staff: -€ {costo_pasti_staff:,.0f}")
    k6.metric("Bocche Totali (96h)", f"{bocche_totali_assedio} bocche", f"Include {staff_in_house} Staff")

    if sc_data["lock_in"]:
        st.markdown(f'<div class="box-red"><b>🔴 PROTOCOLLO ISOLAMENTO / FORZA MAGGIORE ATTIVO:</b> Chiudere istantaneamente <b>TheFork, OpenTable e Google Reserve</b> agli esterni. Priorità assoluta alle <b>{bocche_totali_assedio} bocche presenti nell\'edificio</b> ({pax_fb+pax_hb+pax_bb+pax_ro} Ospiti + {staff_in_house} Staff Residente).</div>', unsafe_allow_html=True)
    elif slot_liberi_per_esterni <= 12:
        st.markdown(f'<div class="box-amber"><b>🟠 SATURAZIONE INTERNA ELEVATA ({coperti_totali_hotel}/{tetto_reale_servizio} coperti già in casa):</b> <b>CHIUDERE SUBITO THEFORK</b> (risparmio € {comm_thefork:.2f}/coperto). Lasciare aperti solo <b>{slot_liberi_per_esterni} posti</b> su <b>Google Reserve / Canale Diretto</b> con carta a garanzia sopra i {soglia_carta_garanzia} ospiti.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="box-green"><b>🟢 CAPACITÀ ESTERNA DISPONIBILE ({slot_liberi_per_esterni} sedute libere):</b> Mantenere aperti <b>Google Reserve, Sito Diretto e TheFork</b>. Garanzia carta anti no-show per tavoli da {soglia_carta_garanzia}+ pax.</div>', unsafe_allow_html=True)

    t1, t2, t3, t4, t5 = st.tabs([
        "🔬 1. ECONOMATO & SFRIDI VIVI",
        "🛡️ 2. SCUDO 96 ORE & FALLBACK VIP",
        "🎯 3. PROMO ENGINE & ROAS NETTO",
        "🏛️ 4. SPLIT MULTI-P.IVA & XML",
        "🌉 5. PONTE SOVEREIGN ZERO"
    ])

    with t1:
        st.subheader("Calcolatore Chirurgico Sfridi, Sgocciolato, Selvaggina, Pouring & Usura Calici")
        ec1, ec2, ec3 = st.columns(3)
        with ec1:
            ref_nome = st.text_input("Referenza (Piatto / Calice / Bottiglia)", value="Tagliata di Cervo / Calice Franciacorta")
            prezzo_menu_lordo = st.number_input("Prezzo Vendita Menu IVA Incl. (€)", value=26.0, step=1.0)
            iva_ref = st.selectbox("IVA Referenza (%)", [10, 22], index=0)
        with ec2:
            costo_acq_kg_lt = st.number_input("Costo Acquisto Fattura Netto (€/Kg o €/Bottiglia)", value=24.0, step=0.5)
            grammatura_porzione = st.number_input("Dose Servita nel Piatto/Calice (Kg o frazione)", value=0.200, step=0.020, format="%.3f")
            resa_effettiva_pct = st.slider("Resa Reale Post-Sfrido / Sgocciolato / Ossa (%)", 35, 100, 72)
        with ec3:
            quota_rottura_vetri = st.number_input("Quota Usura/Rottura Cristalleria + Tovagliato (€)", value=0.45, step=0.05)
            costo_guarnizione = st.number_input("Costo Contorno / Guarnizione / Pane & Coperto (€)", value=1.10, step=0.10)

        prezzo_ref_netto = prezzo_menu_lordo / (1.0 + iva_ref / 100.0)
        costo_mp_teorico = costo_acq_kg_lt * grammatura_porzione
        costo_mp_reale_sfrido = costo_mp_teorico / (resa_effettiva_pct / 100.0)
        costo_vivo_totale_piatto = costo_mp_reale_sfrido + quota_rottura_vetri + costo_guarnizione
        margine_netto_piatto = prezzo_ref_netto - costo_vivo_totale_piatto
        incidenza_reale_pct = (costo_vivo_totale_piatto / prezzo_ref_netto * 100.0) if prezzo_ref_netto > 0 else 0.0

        m_a, m_b, m_c, m_d = st.columns(4)
        m_a.metric("Ricavo Netto Referenza", f"€ {prezzo_ref_netto:.2f}", f"Teorico senza scarto: € {costo_mp_teorico:.2f}")
        m_b.metric("Costo Vivo Reale (con Sfrido+Vetri)", f"€ {costo_vivo_totale_piatto:.2f}", f"+€ {costo_mp_reale_sfrido - costo_mp_teorico:.2f} di sfrido occulto")
        m_c.metric("Margine Netto Unitario", f"€ {margine_netto_piatto:.2f}")
        m_d.metric("Food Cost Reale Referenza", f"{incidenza_reale_pct:.1f}%", "In Target" if incidenza_reale_pct <= 30 else "Rivedere Prezzo/Porzione")

    with t2:
        st.subheader(f"Autonomia Dispensa 96 Ore ({bocche_totali_assedio} Bocche: Ospiti + Staff) & Piano Continuità VIP")
        col_s1, col_s2 = st.columns([1.3, 1])
        with col_s1:
            fabbisogno_96h = bocche_totali_assedio * 4
            df_assedio = pd.DataFrame([
                {"Dispensa Critica": "Farina, Lievito Secco & Basi Panificazione", "Porzioni in Casa": 520, "Target 96h": fabbisogno_96h},
                {"Dispensa Critica": "Latte UHT, Uova, Burro & Colazione", "Porzioni in Casa": 380, "Target 96h": fabbisogno_96h},
                {"Dispensa Critica": "Proteine Nobili / Selvaggina (-18°C)", "Porzioni in Casa": 490, "Target 96h": fabbisogno_96h},
                {"Dispensa Critica": "Pasta, Riso Carnaroli & Pelati Sgocciolati", "Porzioni in Casa": 640, "Target 96h": fabbisogno_96h},
                {"Dispensa Critica": "Acqua Minerale, Vino & Gas Cucina", "Porzioni in Casa": 700, "Target 96h": fabbisogno_96h},
            ])
            df_assedio["Autonomia (Giorni)"] = (df_assedio["Porzioni in Casa"] / max(1, bocche_totali_assedio)).round(1)
            df_assedio["Stato Scudo"] = df_assedio["Autonomia (Giorni)"].apply(
                lambda d: "🟢 AUTONOMO (>4gg)" if d >= 4.0 else "🔴 REINTEGRO IMMEDIATO (<4gg)"
            )
            st.dataframe(df_assedio, width="stretch", hide_index=True)

        with col_s2:
            df_staff_vip = pd.DataFrame([
                {"Servizio VIP": "Lezione Yoga / Pilates", "Operatore": "Esterno (Pendolare da Valle)", "Fallback in Caso Blocco": "Diretta Live 4K in Suite + Tisana Detox & Operatrice Spa In-House"},
                {"Servizio VIP": "Degustazione Sommelier", "Operatore": "Residente (Staff House)", "Fallback in Caso Blocco": "Garantito al 100% in Cantina Storica"},
                {"Servizio VIP": "Escursione Yacht / Elicottero", "Operatore": "Soggetto a Grounding Meteo", "Fallback in Caso Blocco": "Conversione immediata in Voucher Private Spa + Champagne Cuvée"},
            ])
            st.dataframe(df_staff_vip, width="stretch", hide_index=True)

    with t3:
        st.subheader("Calcolatore Spinta Pubblicitaria (Google Ads / Meta / QR Interno) su Margine Vivo")
        pr1, pr2, pr3 = st.columns(3)
        sedute_target_promo = pr1.number_input("Sedute Vuote da Colmare con Promo", min_value=1, value=max(8, slot_liberi_per_esterni), step=2)
        scontrino_promo = pr2.number_input("Scontrino Lordo Previsto Promo (€)", min_value=20.0, value=scontrino_alacarte, step=5.0)
        costo_vivo_omaggio = pr3.number_input("Costo Vivo Benefit Omaggio (es. Calice €3,10)", min_value=0.0, value=3.10, step=0.50)

        incasso_netto_promo = (scontrino_promo / (1.0 + iva_media_fnb / 100.0)) * sedute_target_promo
        costo_mp_promo = incasso_netto_promo * (food_cost_pct / 100.0)
        costo_tot_omaggi = costo_vivo_omaggio * sedute_target_promo
        utile_netto_promo = incasso_netto_promo - costo_mp_promo - costo_tot_omaggi
        budget_ads_consigliato = max(0.0, utile_netto_promo * 0.15)

        pm1, pm2, pm3 = st.columns(3)
        pm1.metric("Ricavo Netto Aggiuntivo", f"€ {incasso_netto_promo:,.0f}")
        pm2.metric("Utile Vivo Pulito (dopo MP e Calice Omaggio)", f"€ {utile_netto_promo:,.0f}")
        pm3.metric("Budget Max Ads Giornaliero (15% del Netto)", f"€ {budget_ads_consigliato:,.0f}", "Zero erosione margine")

    with t4:
        st.subheader("Rendicontazione Separata Casa Madre vs P.IVA Ristorazione / Lido")
        sp1, sp2, sp3 = st.columns(3)
        sp1.metric("MOL Totale Generato Oggi", f"€ {margine_operativo_netto:,.2f}")
        sp2.metric(f"Quota P.IVA Ristorazione ({fee_gestore_fnb}%)", f"€ {quota_societa_fnb:,.2f}")
        sp3.metric(f"Royalty / Quota Casa Madre ({100 - fee_gestore_fnb}%)", f"€ {quota_casa_madre:,.2f}")

    with t5:
        st.markdown("#### 🔗 4. PONTE VERSO SOVEREIGN ZERO (`bridge_data.json`)")
        floor_min_hb = round((cf_brigata / max(coperti_totali, 15)) + (quota_pasto_hb * (food_cost_pct / 100.0)), 2)
        st.write(f"Scenario attivo inviato al banco: **{st.session_state['active_scenario']}**")
        st.write(f"Costo vivo industriale stimato per pasto (Floor HB): **{floor_min_hb:.2f} €**")

        if st.button("💾 CONSOLIDA SCENARIO E FLOOR PER SOVEREIGN ZERO", width="stretch"):
            ok = save_bridge_data({
                "updated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "system": "BEMASK // L.A.Z.E.R.S.",
                "active_weather_scenario": st.session_state["active_scenario"],
                "floor_hb": quota_pasto_hb,
                "floor_fb": quota_pasto_fb,
                "floor_industriale_pasto": floor_min_hb,
                "food_cost_pct": food_cost_pct,
                "cf_brigata_default": cf_brigata,
                "pax_hb": pax_hb,
                "pax_fb": pax_fb,
                "pax_bb": pax_bb,
                "pax_ro": pax_ro,
                "staff_in_house": staff_in_house,
                "bocche_assedio_96h": bocche_totali_assedio,
                "slot_esterni_aperti": slot_liberi_per_esterni,
                "mol_fnb_giornaliero": round(margine_operativo_netto, 2)
            })
            if ok:
                st.success("✅ Scenario, Econometria e Vincoli L.A.Z.E.R.S. salvati in 'bridge_data.json'!")
            else:
                st.error("Impossibile salvare il file ponte.")

if __name__ == "__main__":
    st.set_page_config(page_title="BEMASK // L.A.Z.E.R.S.", layout="wide")
    render_fnb_module()
