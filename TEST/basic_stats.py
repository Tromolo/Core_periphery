import pandas as pd
import os
import numpy as np
import sys

# --- Konfigurácia ---
# Cesta k hlavnému adresáru projektu
project_path = "." 

# Názov súhrnného CSV súboru s vlastnosťami sietí (vygenerovaný predchádzajúcim skriptom)
SUMMARY_PROPERTIES_CSV = os.path.join(project_path, "network_properties_summary.csv")

# Adresár, kde sú uložené detailné súbory centralít uzlov (vygenerované predchádzajúcim skriptom)
NODE_CENTRALITIES_DIR = os.path.join(project_path, "results", "node_centralities")

# Názvy stĺpcov v detailných súboroch centralít, z ktorých chceme spriemerovať
BETWEENNESS_COL = 'betweenness_centrality'
CLOSENESS_COL = 'closeness_centrality'

# Názvy nových stĺpcov, ktoré pridáme do súhrnnej tabuľky
AVG_BETWEENNESS_COL_SUMMARY = 'Average Betweenness Centrality (Network)'
AVG_CLOSENESS_COL_SUMMARY = 'Average Closeness Centrality (Network)'

# --- Skript ---

print(f"Načítavam súhrnné vlastnosti sietí zo súboru: {SUMMARY_PROPERTIES_CSV}")
try:
    df_summary = pd.read_csv(SUMMARY_PROPERTIES_CSV)
    print(f"Úspešne načítaných {len(df_summary)} riadkov zo súhrnnej tabuľky.")
    
    # Skontrolujeme, či stĺpec 'Network' existuje a použijeme ho na indexovanie
    if 'Network' not in df_summary.columns:
        raise ValueError(f"Súbor {SUMMARY_PROPERTIES_CSV} neobsahuje stĺpec 'Network'.")
        
    df_summary.set_index('Network', inplace=True)

except FileNotFoundError:
    print(f"CHYBA: Súbor {SUMMARY_PROPERTIES_CSV} sa nenašiel.")
    sys.exit(1) # Ukončí skript, ak súbor neexistuje
except Exception as e:
    print(f"CHYBA pri načítaní súboru {SUMMARY_PROPERTIES_CSV}: {e}")
    sys.exit(1)


# Pripravíme nové stĺpce v súhrnnej tabuľke, inicializované na NaN
df_summary[AVG_BETWEENNESS_COL_SUMMARY] = np.nan
df_summary[AVG_CLOSENESS_COL_SUMMARY] = np.nan

print(f"\nPrechádzam detailné súbory centralít v adresári: {NODE_CENTRALITIES_DIR}")

# Prejdeme cez siete, ktoré sú uvedené v súhrnnej tabuľke
for network_name in df_summary.index:
    # Vytvoríme bezpečný názov súboru pre danú sieť
    safe_network_name = network_name.replace(" ", "_").replace("-","_").lower()
    centrality_file_name = f"{safe_network_name}_centralities.csv"
    centrality_file_path = os.path.join(NODE_CENTRALITIES_DIR, centrality_file_name)

    print(f"Spracovávam sieť '{network_name}': Hľadám súbor '{centrality_file_name}'")

    if os.path.exists(centrality_file_path):
        try:
            # Načítame detailné centrality pre danú sieť
            df_centrality = pd.read_csv(centrality_file_path)
            
            # Vypočítame priemery pre Betweenness a Closeness Centrality
            # .mean() automaticky ignoruje NaN hodnoty
            avg_betweenness = np.nan # Inicializacia pre pripad, ze stlpec chyba/je prazdny
            if BETWEENNESS_COL in df_centrality.columns:
                avg_betweenness = df_centrality[BETWEENNESS_COL].mean()
                
            avg_closeness = np.nan # Inicializacia pre pripad, ze stlpec chyba/je prazdny
            if CLOSENESS_COL in df_centrality.columns:
                 avg_closeness = df_centrality[CLOSENESS_COL].mean()

            # Ak sieť mala 0 uzlov alebo sa nepodarilo načítať centralitu, priemer bude NaN
            if not pd.isna(avg_betweenness) or not pd.isna(avg_closeness):
                 print(f"  Vypočítané priemery: Betweenness={avg_betweenness:.6f}, Closeness={avg_closeness:.6f}")
                 
                 # Pridáme vypočítané priemery do príslušného riadku v súhrnnej tabuľke
                 df_summary.loc[network_name, AVG_BETWEENNESS_COL_SUMMARY] = avg_betweenness
                 df_summary.loc[network_name, AVG_CLOSENESS_COL_SUMMARY] = avg_closeness
            else:
                 print(f"  Varovanie: Priemery Betweenness/Closeness pre {network_name} sú NaN (možno pre veľké siete alebo chybu).")


        except Exception as e:
            print(f"  CHYBA pri spracovaní súboru {centrality_file_path}: {e}")
            # V prípade chyby zostanú hodnoty NaN, čo je v poriadku

    else:
        print(f"  Upozornenie: Súbor '{centrality_file_name}' pre sieť '{network_name}' sa nenašiel. Priemery budú NaN.")
        # Hodnoty už sú NaN, netreba nič robiť, ale print je uzitocny


print("\nUkladám aktualizovanú súhrnnú tabuľku vlastností sietí...")

# Uložíme aktualizovaný DataFrame späť do CSV súboru
try:
    # Resetujeme index, aby sa stĺpec 'Network' uložil späť ako stĺpec
    df_summary.reset_index(inplace=True) 
    
    # Zabezpecime, ze NaN hodnoty sa zapisu spravne
    df_summary.replace([np.inf, -np.inf], np.nan, inplace=True) 

    # Pouzijeme float_format pre konzistentne desatinne miesta pre float stlpce
    df_summary.to_csv(SUMMARY_PROPERTIES_CSV, index=False, float_format='%.6f') 
    print(f"Úspešne uložená aktualizovaná súhrnná tabuľka do: {SUMMARY_PROPERTIES_CSV}")

except Exception as e:
    print(f"FATÁLNA CHYBA pri ukladaní súhrnnej tabuľky do {SUMMARY_PROPERTIES_CSV}: {e}")


print("\nSkript na pridanie priemerných centralít do súhrnnej tabuľky dokončený.")