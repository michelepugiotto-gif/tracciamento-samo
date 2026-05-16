import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configurazione della pagina stile Mobile-First
st.set_page_config(page_title="SAMO Express - Stato Ordine", page_icon="🚚", layout="centered")

# --- CSS PERSONALIZZATO PER IL DESIGN ---
st.markdown("""
<style>
    /* Sfondo e font generali */
    .stApp {
        background-color: #f8f9fa;
    }
    h1 {
        color: #1e3a8a !important;
        font-weight: 800 !important;
        text-align: center;
        margin-bottom: 5px !important;
    }
    .subtitle {
        color: #4b5563;
        text-align: center;
        font-size: 1.1rem;
        margin-bottom: 30px;
    }
    
    /* Box dell'ordine */
    .order-box {
        background-color: white;
        padding: 25px;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border-left: 5px solid #1e3a8a;
        margin-top: 20px;
    }
    
    /* Barra dei progressi stile Amazon */
    .progress-track {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 30px 0;
        position: relative;
    }
    .progress-track::before {
        content: "";
        position: absolute;
        top: 15px;
        left: 10px;
        right: 10px;
        height: 4px;
        background-color: #e5e7eb;
        z-index: 1;
    }
    .step {
        text-align: center;
        position: relative;
        z-index: 2;
        flex: 1;
    }
    .step-icon {
        width: 34px;
        height: 34px;
        border-radius: 50%;
        background-color: #e5e7eb;
        color: #9ca3af;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        margin-bottom: 5px;
        border: 3px solid white;
    }
    .step.active .step-icon {
        background-color: #1e3a8a;
        color: white;
        box-shadow: 0 0 0 3px rgba(30, 58, 138, 0.2);
    }
    .step.completed .step-icon {
        background-color: #10b981;
        color: white;
    }
    .step-text {
        font-size: 0.75rem;
        font-weight: 600;
        color: #6b7280;
    }
    .step.active .step-text, .step.completed .step-text {
        color: #111827;
    }
    
    /* Messaggio di allarme personalizzato */
    .alert-ritardo {
        background-color: #fef2f2;
        border: 1px solid #fca5a5;
        padding: 15px;
        border-radius: 10px;
        color: #991b1b;
        font-weight: 500;
        margin-top: 15px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURAZIONI UTENTE MODIFICATE ---
SPREADSHEET_ID = "1LJsprtS71Zfmhw1fK8BO1qDdpkvZsm2v" 
RANGE_NAME = "Foglio1!A:K"

EMAIL_UFFICIO = "info@freelance-torino.eu"
EMAIL_MITTENTE = "info@freelance-torino.eu" 
PASSWORD_EMAIL = "la_tua_password_app_google"  # Sostituisci questa con la tua chiave a 16 lettere di Google

# Funzione per inviare la mail di sollecito interno all'ufficio
def invia_mail_sollecito_interno(nome_utente, azienda_utente, co):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_MITTENTE
        msg['To'] = EMAIL_UFFICIO
        msg['Subject'] = f"⚠️ SOLLECITO AUTOMATICO: {azienda_utente} ({nome_utente})"
        
        corpo = f"{nome_utente} ha bisogno di sapere quando ricevere il materiale della conferma ordine {co}"
        msg.attach(MIMEText(corpo, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_MITTENTE, PASSWORD_EMAIL)
        server.sendmail(EMAIL_MITTENTE, EMAIL_UFFICIO, msg.as_string())
        server.quit()
        return True
    except Exception:
        return False

# Caricamento dati da Google Drive con cache di 10 secondi
@st.cache_data(ttl=10)
def load_data():
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict)
    service = build('sheets', 'v4', credentials=creds)
    result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get('values', [])
    if not values:
        return pd.DataFrame()
    headers = values[0]
    rows = values[1:]
    max_len = len(headers)
    cleaned_rows = [row + [''] * (max_len - len(row)) for row in rows]
    return pd.DataFrame(cleaned_rows, columns=headers)

# --- INTERFACCIA UTENTE ---
st.markdown("<h1>🚚 SAMO EXPRESS</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Tracciamento trasparente e rapido delle tue consegne</p>", unsafe_allow_html=True)

# Box di inserimento dati ben impacchettato
with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        nome_utente = st.text_input("Il tuo Nome:", placeholder="Es. Andrea")
    with col2:
        azienda_utente = st.text_input("La tua Azienda:", placeholder="Es. Idrocentro Caselle")
        
    ricerca = st.text_input("Inserisci Riferimento o Numero di Conferma Ordine (CO):", placeholder="Es. Rossi oppure 26019345")
    pulsante_invia = st.button("Verifica Stato Spedizione 🔍", use_container_width=True)

if pulsante_invia:
    if not nome_utente or not azienda_utente or not ricerca:
        st.warning("⚠️ Per favore, compila tutti i campi richiesti.")
    else:
        with st.spinner("Connessione ai server SAMO..."):
            df = load_data()
            
        if not df.empty:
            df.columns = df.columns.str.strip()
            ricerca_clean = ricerca.strip().lower()
            
            col_rif = 'Riferimento'
            col_co = 'CO' 
            
            df_risultato = df[(df[col_rif].str.strip().str.lower() == ricerca_clean) | (df[col_co].str.strip().str.lower() == ricerca_clean)].copy()
            
            if df_risultato.empty:
                st.error("❌ Nessun ordine trovato. Verifica il codice o contatta l'assistenza.")
            else:
                ordine = df_risultato.iloc[0]
                rif_trovato = ordine.get('Riferimento', 'N/D')
                co_trovato = ordine.get('CO', 'N/D')
                materiale = ordine.get('Materiale', 'N/D')
                status_drive = str(ordine.get('Status', '')).strip().upper()
                lista_consegna = str(ordine.get('Lista', '')).strip()
                ddt_numero = str(ordine.get('DDT', '')).strip()
                data_evasione_str = str(ordine.get('Data Spedizione', '')).strip()
                
                oggi = datetime.now().date()
                data_scaduta = False
                try:
                    data_evasione_dt = datetime.strptime(data_evasione_str, "%d/%m/%Y").date()
                    if data_evasione_dt < oggi:
                        data_scaduta = True
                except ValueError:
                    data_scaduta = True 

                # --- COSTRUZIONE DELLA GRAFICA AMAZON STYLE ---
                step1_class = "step completed"
                step2_class = "step"
                step3_class = "step"
                
                stato_dettaglio = ""
                mostra_allarme = False
                
                if ddt_numero:
                    step2_class = "step completed"
                    step3_class = "step active"
                    stato_dettaglio = f"Spedito con successo. DDT nr. <b>{ddt_numero}</b>"
                elif lista_consegna:
                    step2_class = "step active"
                    stato_dettaglio = f"In preparazione presso il magazzino. Inserito nella lista di carico nr. <b>{lista_consegna}</b>"
                elif "ROSSO" in status_drive or data_scaduta:
                    step1_class = "step active"
                    stato_dettaglio = f"In lavorazione - Data prevista: {data_evasione_str}"
                    mostra_allarme = True
                else:
                    step1_class = "step active"
                    stato_dettaglio = f"Ordine ricevuto e preso in carico. Evasione stimata: {data_evasione_str}"

                # Render HTML della scheda ordine personalizzata
                st.markdown(f"""
                <div class="order-box">
                    <h3 style='color:#1e3a8a; margin-top:0;'>📦 Ordine {rif_trovato}</h3>
                    <p style='margin:4px 0;'><b>Conferma Ordine (CO):</b> {co_trovato}</p>
                    <p style='margin:4px 0;'><b>Modello/Materiale:</b> {materiale}</p>
                    <hr style='margin:15px 0; border:0; border-top:1px solid #eee;'>
                    
                    <div class="progress-track">
                        <div class="{step1_class}">
                            <div class="step-icon">1</div>
                            <div class="step-text">Ricevuto</div>
                        </div>
                        <div class="{step2_class}">
                            <div class="step-icon">2</div>
                            <div class="step-text">In Preparazione</div>
                        </div>
                        <div class="{step3_class}">
                            <div class="step-icon">3</div>
                            <div class="step-text">Spedito</div>
                        </div>
                    </div>
                    
                    <p style='text-align:center; font-size:1rem; color:#374151; margin-top:10px;'>
                        ℹ️ <b>Stato attuale:</b> {stato_dettaglio}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Se l'ordine è in ritardo (Rosso), spariamo il blocco visivo e la mail
                if mostra_allarme:
                    st.markdown(f"""
                    <div class="alert-ritardo">
                        🛑 Materiale in ritardo: ho appena sollecitato l'operatore. Riceverai aggiornamenti a breve.
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.spinner("Invio segnalazione prioritaria in ufficio..."):
                        invia_mail_sollecito_interno(nome_utente, azienda_utente, co_trovato)
                
                st.write("")
                # Tasto WhatsApp coordinato con lo stile della pagina (Ricordati di inserire il tuo numero se necessario)
                testo_wa = f"Ciao SAMO, sono {nome_utente} di {azienda_utente}. Vorrei aggiornamenti sul codice {rif_trovato} CO {co_trovato}."
                link_wa = f"https://wa.me/39XXXXXXXXXX?text={testo_wa.replace(' ', '%20')}"
                st.link_button("💬 Richiedi assistenza diretta su WhatsApp", link_wa, use_container_width=True)
