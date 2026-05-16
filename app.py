import streamlit as st
import pandas as pd
import datetime
import smtplib
from email.mime.text import MIMEText

# --- COLLEGAMENTO DIRETTO AL TUO GOOGLE DRIVE ---
LINK_CSV = "https://docs.google.com/spreadsheets/d/1LJsprtS71Zfmhw1fK8BO1qDdpkvZsm2v/export?format=csv"

@st.cache_data(ttl=10)
def carica_dati():
    try:
        # IMPOSTATO HEADER=0: Ora prende la riga corretta delle intestazioni
        data = pd.read_csv(LINK_CSV, dtype=str, header=0)
        # Pulizia base delle colonne
        data.columns = data.columns.str.strip().str.lower()
        return data
    except Exception as e:
        st.error("Rilevato problema di accesso a Google Drive. Verifica che il file sia condiviso con 'Chiunque abbia il link'.")
        return pd.DataFrame()

df = carica_dati()

if not df.empty:
    st.title("Sistema Tracciamento Ordini Samo")
    st.markdown("---")

    # Mappiamo le colonne in base alla posizione esatta dei tuoi dati per non avere dubbi di battitura
    # 0: riferimento, 1: codice, 2: materiale, 3: data spedizione, 4: destinatario, 5: conferma ordine, 6: status, 7: lista spedizione, 8: ddt, 9: fattura
    colonne_reali = df.columns.tolist()
    
    if len(colonne_reali) < 10:
        st.error("Il file non contiene il numero minimo di colonne richiesto (10 colonne).")
    else:
        # Assegniamo i nomi corretti alle colonne in base alla loro posizione fisica nel file
        df.columns = [
            'riferimento', 'codice', 'materiale', 'data di spedizione', 'destinatario', 
            'conferma ordine', 'status', 'lista di spedizione', 'ddt', 'fattura'
        ]

        # Le 4 opzioni di ricerca richieste
        opzione_ricerca = st.radio("Seleziona modalità di ricerca:", ["Destinatario", "Riferimento", "Conferma Ordine (CO)", "Numero DDT"])

        riga_selezionata = None

        if opzione_ricerca == "Destinatario":
            lista_destinatari = sorted(df['destinatario'].dropna().unique())
            scelta_destinatario = st.selectbox("Scegli il Destinatario:", lista_destinatari)
            riga_selezionata = df[df['destinatario'] == scelta_destinatario]

        elif opzione_ricerca == "Riferimento":
            lista_riferimenti = sorted(df['riferimento'].dropna().unique())
            scelta_rif = st.selectbox("Scegli il Riferimento:", lista_riferimenti)
            riga_selezionata = df[df['riferimento'] == scelta_rif]

        elif opzione_ricerca == "Conferma Ordine (CO)":
            input_co = st.text_input("Digita il numero di Conferma Ordine (CO):")
            if input_co:
                riga_selezionata = df[df['conferma ordine'].astype(str).str.strip() == input_co.strip()]

        elif opzione_ricerca == "Numero DDT":
            input_ddt = st.text_input("Digita il numero DDT:")
            if input_ddt:
                riga_selezionata = df[df['ddt'].astype(str).str.strip() == input_ddt.strip()]

        # Visualizzazione della maschera Input/Output
        if riga_selezionata is not None and not riga_selezionata.empty:
            ordine = riga_selezionata.iloc[0]
            
            st.write("### Scheda Ordine")
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Riferimento", value=str(ordine['riferimento']), disabled=True)
                st.text_input("Destinatario", value=str(ordine['destinatario']), disabled=True)
                st.text_input("Codice Articolo", value=str(ordine['codice']), disabled=True)
                st.text_input("Materiale", value=str(ordine['materiale']), disabled=True)
                st.text_input("Conferma Ordine (CO)", value=str(ordine['conferma ordine']), disabled=True)
            with col2:
                st.text_input("Status", value=str(ordine['status']), disabled=True)
                st.text_input("Data di Spedizione", value=str(ordine['data di spedizione']), disabled=True)
                st.text_input("Lista di Spedizione", value=str(ordine['lista di spedizione']), disabled=True)
                st.text_input("DDT", value=str(ordine['ddt']), disabled=True)
                st.text_input("Fattura", value=str(ordine['fattura']), disabled=True)

            # --- ALGORITMO DI CONTROLLO RITARDO ---
            try:
                # Gestiamo i formati data comuni (es. 12.05.2026 oppure 12/05/2026)
                data_pulita = str(ordine['data di spedizione']).replace('.', '/')
                data_spedizione = pd.to_datetime(data_pulita, dayfirst=True).date()
                oggi = datetime.date.today()
                
                # Verifica se il campo lista di spedizione è vuoto
                valore_lista = str(ordine['lista di spedizione']).strip().lower()
                lista_vuota = pd.isna(ordine['lista di spedizione']) or valore_lista == "" or valore_lista == "nan" or valore_lista == "#"

                if lista_vuota and data_spedizione < oggi:
                    # 1. Messaggio Visivo in ROSSO
                    st.markdown("<br><h3 style='color: red; text-align: center; font-weight: bold;'>⚠️ ordine in ritardo, consultare l'azienda per aggiornamenti</h3>", unsafe_allow_html=True)
                    
                    # 2. Configurazione Mail Automatica
                    mittente = "tuamail@esempio.com" 
                    destinatario_mail = "info@freelance-torino.eu"
                    
                    oggetto_mail = f"richiesta verfica data corretta di consegna - Rif: {ordine['riferimento']} - Destinatario: {ordine['destinatario']}"
                    corpo_mail = f"{ordine['conferma ordine']} : Francesco, per cortesia, puoi dirmi se vedi quando va in evasione?"
                    
                    msg = MIMEText(corpo_mail)
                    msg['Subject'] = objeto_mail = oggetto_mail
                    msg['From'] = mittente
                    msg['To'] = destinatario_mail
                    
                    st.info(f"📧 Sistema pronto all'invio del sollecito automatico a: {destinatario_mail}")
            except Exception as e:
                # Se la data ha un formato non riconosciuto, non bloccare il programma
                pass