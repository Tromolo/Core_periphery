import pandas as pd
import numpy as np
import os
import sys

# --- Konfigurácia ---
# Cesta k hlavnému adresáru projektu
project_path = '/home/hruby/PycharmProjects/Core_periphery' # !!! Nastavte podľa potreby !!!
if project_path not in sys.path:
    sys.path.append(project_path)

# Adresár, kde sú uložené súbory so zoznamami core uzlov (výstup z extract_optimal_*.py skriptov)
CORE_LISTS_DIR = os.path.join(project_path, 'results', 'optimal_cores')

# Adresár, kde sú uložené detailné súbory centralít uzlov (výstup z calculate_network_properties.py skriptu)
NODE_CENTRALITIES_DIR = os.path.join(project_path, "results", "node_centralities")

# Názvy vstupných súborov so zoznamami core uzlov pre každý algoritmus
ALGO_CORE_FILES = {
    "BE": "be_optimal_cores.csv",
    "Rombach": "rombach_optimal_cores.csv",
    "LowRankCore": "cucuringu_optimal_cores.csv",
}

# Názov výstupného CSV súboru pre výsledky shlukovania jadra/periférie
OUTPUT_CLUSTERING_CSV = os.path.join(project_path, 'results', 'core_periphery_clustering_optimal_run.csv')

# Názov stĺpca s lokálnym shlukovacím koeficientom v súboroch centralít
LOCAL_CLUSTERING_COL = 'local_clustering_coefficient'
# Názov stĺpca s ID uzla v súboroch centralít
NODE_ID_COL = 'node_id'

# --- Skript ---

all_clustering_results = []

print("Spúšťam výpočet priemerného shlukovacieho koeficientu jadra a periférie...")

for algorithm, core_file_name in ALGO_CORE_FILES.items():
    core_file_path = os.path.join(CORE_LISTS_DIR, core_file_name)
    
    print(f"\nSpracovávam algoritmus: {algorithm} zo súboru {core_file_name}")

    if not os.path.exists(core_file_path):
        print(f"Upozornenie: Súbor {core_file_path} sa nenašiel. Preskakujem tento algoritmus.")
        continue

    try:
        df_cores = pd.read_csv(core_file_path)
        print(f"  Načítaných {len(df_cores)} riadkov z {core_file_name}.")
    except Exception as e:
        print(f"  CHYBA: Nepodarilo sa načítať súbor {core_file_path}: {e}. Preskakujem.")
        continue

    # Spracovanie každého riadku (každá sieť) v súbore core uzlov
    for index, row in df_cores.iterrows():
        network_name = row['Network']
        core_nodes_str = row['Core_Nodes']
        
        # Pokus o zistenie parametrov z riadku (môžu sa líšiť medzi algoritmami)
        params_dict = {col: row[col] for col in row.index if col not in ['Network', 'Core_Nodes', 'algorithm']}

        print(f"  Spracovávam sieť '{network_name}'...")

        # Načítanie detailných centralít pre danú sieť
        safe_network_name = network_name.replace(" ", "_").replace("-","_").lower()
        centrality_file_name = f"{safe_network_name}_centralities.csv"
        centrality_file_path = os.path.join(NODE_CENTRALITIES_DIR, centrality_file_name)

        if not os.path.exists(centrality_file_path):
            print(f"    Upozornenie: Súbor centralít '{centrality_file_name}' pre sieť '{network_name}' sa nenašiel. Preskakujem túto sieť.")
            # Pridať riadok s NaN hodnotami pre shlukovanie
            result_row = {
                "Network": network_name,
                "Algorithm": algorithm,
                "Core Avg Clustering": np.nan,
                "Periphery Avg Clustering": np.nan,
                "Clustering Ratio (C/P)": np.nan,
            }
            # Pridáme aj parametre, ak existujú
            for param_key, param_value in params_dict.items():
                 result_row[param_key] = param_value
            all_clustering_results.append(result_row)

            continue

        try:
            df_centrality = pd.read_csv(centrality_file_path)
            # Zabezpečiť, že stĺpce, ktoré potrebujeme, existujú
            if NODE_ID_COL not in df_centrality.columns or LOCAL_CLUSTERING_COL not in df_centrality.columns:
                 print(f"    CHYBA: Súbor centralít '{centrality_file_name}' neobsahuje požadované stĺpce ('{NODE_ID_COL}' alebo '{LOCAL_CLUSTERING_COL}'). Preskakujem túto sieť.")
                 result_row = {
                     "Network": network_name,
                     "Algorithm": algorithm,
                     "Core Avg Clustering": np.nan,
                     "Periphery Avg Clustering": np.nan,
                     "Clustering Ratio (C/P)": np.nan,
                 }
                 for param_key, param_value in params_dict.items():
                      result_row[param_key] = param_value
                 all_clustering_results.append(result_row)
                 continue

        except Exception as e:
            print(f"    CHYBA pri načítaní súboru centralít {centrality_file_path}: {e}. Preskakujem túto sieť.")
            result_row = {
                "Network": network_name,
                "Algorithm": algorithm,
                "Core Avg Clustering": np.nan,
                "Periphery Avg Clustering": np.nan,
                "Clustering Ratio (C/P)": np.nan,
            }
            for param_key, param_value in params_dict.items():
                 result_row[param_key] = param_value
            all_clustering_results.append(result_row)
            continue

        # --- Výpočet shlukovania pre jadro a perifériu ---
        core_avg_clustering = np.nan
        periphery_avg_clustering = np.nan
        clustering_ratio = np.nan

        # Získanie všetkých ID uzlov zo siete (z centralít)
        all_nodes = set(df_centrality[NODE_ID_COL].astype(str).tolist()) # Konvertovať na str pre bezpečné porovnanie

        # Parsujeme zoznam core uzlov zo stringu
        if core_nodes_str == "ERROR":
             print(f"    CHYBA: Zoznam core uzlov pre {network_name} je 'ERROR'. Výsledky shlukovania budú NaN.")
             core_nodes_set = set() # Prazdna mnozina
        elif pd.isna(core_nodes_str) or core_nodes_str == "":
             # Prazdny retazec alebo NaN znamena 0 core uzlov
             core_nodes_set = set()
        else:
             # Rozdelit string a konvertovat na set stringov
             core_nodes_set = set(core_nodes_str.split(','))
             # Odstranit uzly, ktore nahodou nie su v sieti (ak by sa vyskytli)
             core_nodes_set = core_nodes_set.intersection(all_nodes)


        # Určenie uzlov periférie
        periphery_nodes_set = all_nodes - core_nodes_set

        # Získanie lokálnych shlukovacích koeficientov pre uzly v jadre
        if core_nodes_set: # Ak jadro nie je prázdne
            df_core_centrality = df_centrality[df_centrality[NODE_ID_COL].astype(str).isin(core_nodes_set)]
            if not df_core_centrality.empty:
                core_avg_clustering = df_core_centrality[LOCAL_CLUSTERING_COL].mean()
            else:
                print(f"    Varovanie: Core set pre {network_name} nie je prázdny, ale nenašli sa zodpovedajúce uzly v centralitách. Core Avg Clustering bude NaN.")


        # Získanie lokálnych shlukovacích koeficientov pre uzly v periférii
        if periphery_nodes_set: # Ak periféria nie je prázdna
             df_periphery_centrality = df_centrality[df_centrality[NODE_ID_COL].astype(str).isin(periphery_nodes_set)]
             if not df_periphery_centrality.empty:
                 periphery_avg_clustering = df_periphery_centrality[LOCAL_CLUSTERING_COL].mean()
             else:
                 print(f"    Varovanie: Periphery set pre {network_name} nie je prázdny, ale nenašli sa zodpovedajúce uzly v centralitách. Periphery Avg Clustering bude NaN.")


        # Výpočet pomeru C/P
        # Ošetrenie delenia nulou alebo NaN
        if pd.notna(core_avg_clustering) and pd.notna(periphery_avg_clustering):
             if periphery_avg_clustering != 0:
                  clustering_ratio = core_avg_clustering / periphery_avg_clustering
             elif core_avg_clustering == 0:
                  # Ak je jadro aj periferia s avg shlukovanim 0
                  clustering_ratio = 1.0 # Pomer 1:1
             else:
                  # Ak periferia je 0 a jadro > 0
                  clustering_ratio = np.inf # Nekonecny pomer


        # --- Pridanie výsledkov do zoznamu ---
        result_row = {
            "Network": network_name,
            "Algorithm": algorithm,
            "Core Avg Clustering": core_avg_clustering,
            "Periphery Avg Clustering": periphery_avg_clustering,
            "Clustering Ratio (C/P)": clustering_ratio,
        }
        # Pridáme aj parametre použité pri extrakcii core uzlov
        for param_key, param_value in params_dict.items():
             result_row[param_key] = param_value

        all_clustering_results.append(result_row)

        print(f"    Výsledky pre {network_name}: Core Avg Clustering={core_avg_clustering:.4f}, Periphery Avg Clustering={periphery_avg_clustering:.4f}, Ratio={clustering_ratio:.4f}")



# --- Uloženie výsledkov do CSV ---
if all_clustering_results:
    df_clustering = pd.DataFrame(all_clustering_results)
    
    # Zoradiť stĺpce pre lepší prehľad (voliteľné)
    # Pôvodné parametre + Vypočítané metriky
    calculated_cols = ["Core Avg Clustering", "Periphery Avg Clustering", "Clustering Ratio (C/P)"]
    
    # Získame všetky stĺpce okrem Network, Algorithm, Core_Nodes, a vypočítaných
    param_cols = [col for col in df_clustering.columns if col not in ['Network', 'Algorithm', 'Core_Nodes'] + calculated_cols]
    
    # Určíme finálne poradie stĺpcov
    final_column_order = ['Network', 'Algorithm'] + sorted(param_cols) + calculated_cols
    
    # Zabezpečiť, že všetky stĺpce existujú v DF pred preusporiadaním
    final_column_order = [col for col in final_column_order if col in df_clustering.columns]
    
    df_clustering = df_clustering[final_column_order]

    # Zabezpečiť, že NaN a Inf hodnoty sa zapíšu správne
    df_clustering.replace([np.inf, -np.inf], np.nan, inplace=True) 

    try:
        df_clustering.to_csv(OUTPUT_CLUSTERING_CSV, index=False, float_format='%.6f')
        print(f"\nVýsledky shlukovania jadra/periférie uložené do: {OUTPUT_CLUSTERING_CSV}")
    except Exception as e:
        print(f"\nCHYBA pri ukladaní výsledkov shlukovania: {e}")

else:
    print("\nNeboli vygenerované žiadne výsledky shlukovania jadra/periférie.")

print("\nSkript na výpočet shlukovania jadra/periférie dokončený.")