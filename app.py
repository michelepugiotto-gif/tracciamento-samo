import streamlit as st
import pandas as pd
import datetime

# --- COLLEGAMENTO DIRETTO AL TUO NUOVO GOOGLE FOGLI ---
LINK_CSV = "https://docs.google.com/spreadsheets/d/1x7MV6YyI6Qc26h70RyuroX87x4OF3R81DJUlcv3DNRo/export?format=csv"

@st.cache_data(ttl=10)
def carica_dati():
    try:
        # Legge il file interpretando automaticamente il separatore (, o ;)
        data = pd.read_csv(LINK_CSV, dtype=str, header=0, sep=None, engine='python')
        
        # Forza il dataset a tenere solo le prime 10 colonne (dalla A alla J)
        # Questo azzera l'errore "Length mismatch: Expected axis has..."
        data = data.iloc[:, :10]
        
        # Rinomina subito le colonne per evitare disallineamenti o problemi di maiuscole/minuscole
        data.columns = [
            'riferimento', 'codice', 'materiale', 'data di spedizione', 'destinatario', 
            'conferma ordine', 'status', 'lista di spedizione', 'ddt', 'fattura'
        ]
        
        # Pulisce gli spazi vuoti all'inizio e alla fine di ogni cella di testo
        for col in data.columns:
            data[col] = data[col].astype(str).str.strip()
            
        # --- FUNZIONE DI EMERGENZA PER LE DATE ---
        # Se Excel ha trasformato le date in numeri seriali, le riconverte in date leggibili
        def sistema_data(valore):
            if not valore or valore.lower() in ['none', 'nan', '']:
                return ""
            try:
                # Se è un numero seriale puro (es. 46136)
                if valore.replace('.', '', 1).isdigit():
                    giorni = int(float(valore))
                    data_vera = datetime.date(1899, 12, 30) + datetime.timedelta(days=giorni)
                    return data_vera.strftime("%d/%m/%Y")
            except:
                pass
            return valore

        data['data di spedizione'] = data['data di spedizione'].apply(sistema_data)
        
        return data
    except Exception as e:
        st.error(f"Errore durante il caricamento dei dati: {e}")
        return pd.DataFrame()

# Esecuzione del caricamento dati
df = carica_dati()

# --- INTERFACCIA GRAFICA STREAMLIT ---
if not df.empty:
    st.title("Sistema Tracciamento Ordini Samo")
    st.markdown("---")

    # Opzioni di ricerca per l'utente
    opzione_ricerca = st.radio(
        "Seleziona modalità di ricerca:", 
        ["Destinatario", "Riferimento", "Conferma Ordine (CO)", "Numero DDT"]
    )

    # Input testuale (la ricerca si attiva appena l'utente scrive qualcosa)
    valore_cercato = st.text_input(f"Inserisci {opzione_ricerca}:").strip().lower()

    if valore_cercato:
        # Mappa la scelta del bottone con il nome esatto della colonna nel database
        colonna_mappa = {
            "Destinatario": "destinatario",
            "Riferimento": "riferimento",
            "Conferma Ordine (CO)": "conferma ordine",
            "Numero DDT": "ddt"
        }
        
        colonna_selezionata = colonna_mappa[opzione_ricerca]
        
        # Esegue una ricerca parziale (trova il testo anche se non è scritto interamente uguale)
        risultati = df[df[colonna_selezionata].str.lower().str.contains(valore_cercato, na=False)]
        
        if not risultati.empty:
            st.success(f"Trovati {len(risultati)} risultati:")
            
            # Mostra la tabella riassuntiva dei risultati
            st.dataframe(risultati)
            
            # Gestione della selezione se ci sono più righe trovate
            riga_selezionata = None
            if len(risultati) > 1:
                scelta_riga = st.selectbox(
                    "Seleziona l'ordine specifico da visualizzare nel dettaglio:", 
                    risultati.index, 
                    format_func=lambda x: f"Rif: {risultati.loc[x, 'riferimento']} - Dest: {risultati.loc[x, 'destinatario']}"
                )
                riga_selezionata = risultati.loc[scelta_riga]
            else:
                riga_selezionata = risultati.iloc[0]
                
            # Mostra la scheda dettagliata dell'ordine selezionato
            if riga_selezionata is not None:
                st.markdown("### 📋 Dettaglio Ordine Selezionato")
                
                # Visualizzazione pulita a elenco di tutte le informazioni
                for col in df.columns:
                    valore_cella = riga_selezionata[col]
                    # Se il valore è un errore di riga vuota lo mostra pulito
                    if valore_cella.lower() in ['nan', 'none']:
                        valore_cella = "-"
                    st.write(f"**{col.title()}:** {valore_cella}")
        else:
            st.warning("Nessun ordine trovato con i criteri inseriti.")
else:
    st.warning("Impossibile leggere il database. Verifica la connessione a Google Drive e che il file sia condiviso pubblicamente.")