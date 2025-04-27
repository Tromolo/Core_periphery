import pandas as pd
import numpy as np
import os
import sys
import traceback

# --- Konfigurácia ---
# Cesta k hlavnému adresáru projektu
project_path = '/home/hruby/PycharmProjects/Core_periphery' # !!! Nastavte podľa potreby !!!
if project_path not in sys.path:
    sys.path.append(project_path)

# Cesta k súhrnnej tabuľke vlastností sietí (výstup z druhého skriptu)
SUMMARY_PROPERTIES_CSV = os.path.join(project_path, "network_properties_summary.csv")

# Adresár s vašimi pôvodnými surovými výsledkami z algoritmov
RAW_RESULTS_DIR = os.path.join(project_path, 'TEST/results', 'optimal_params') # !!! Nastavte správnu cestu k VAŠIM RAW výsledkom !!!

# Cesta k súboru s priemerným shlukovacím koeficientom jadra/periférie (výstup z tretieho skriptu)
CORE_PERIPHERY_CLUSTERING_CSV = os.path.join(project_path, 'results', 'core_periphery_clustering_optimal_run.csv')

# Cesta k súborom so zoznamami core uzlov (na získanie presných parametrov použitých pre extrakciu)
CORE_LISTS_DIR = os.path.join(project_path, 'results', 'optimal_cores')

# Názvy súborov s raw výsledkami pre každý algoritmus
ALGO_RAW_FILES = {
    "BE": "be_optimal_results.csv", # !!! Nastavte správne názvy VAŠICH RAW súborov !!!
    "Rombach": "rombach_optimal_results.csv",
    "LowRankCore": "cucuringu_optimal_results.csv", # Alebo ako sa vola Váš LRC raw súbor
}

# Výstupné súbory pre finálne tabuľky dát
OUTPUT_CORRELATIONS_CSV = os.path.join(project_path, 'results', 'final_correlations.csv')
OUTPUT_STRUCTURE_PROPERTIES_CSV = os.path.join(project_path, 'results', 'final_structure_properties.csv')

ALGO_CORE_FILES = {
    "BE": "be_optimal_cores.csv",
    "Rombach": "rombach_optimal_cores.csv",
    "LowRankCore": "cucuringu_optimal_cores.csv", # Alebo ako sa vola Váš LRC core súbor
}


# --- Načítanie dát ---

print("Načítavam vstupné dáta...")

try:
    df_properties = pd.read_csv(SUMMARY_PROPERTIES_CSV)
    df_properties.set_index('Network', inplace=True)
    print(f"  Načítané vlastnosti sietí: {len(df_properties)} sietí.")
except Exception as e:
    print(f"CHYBA: Nepodarilo sa načítať {SUMMARY_PROPERTIES_CSV}: {e}. Skript končí.")
    sys.exit(1)

try:
    df_cp_clustering = pd.read_csv(CORE_PERIPHERY_CLUSTERING_CSV)
    print(f"  Načítané shlukovanie jadra/periférie: {len(df_cp_clustering)} riadkov.")
except Exception as e:
    print(f"CHYBA: Nepodarilo sa načítať {CORE_PERIPHERY_CLUSTERING_CSV}: {e}. Pokračujem bez dát o shlukovaní.")
    df_cp_clustering = pd.DataFrame() # Ak sa nenacita, vytvorime prazdny DF


# Zoznam na uloženie spriemerovaných metrík algoritmov pri odporúčaných parametroch
averaged_algo_metrics = []

print("\nSpracovávam surové výsledky algoritmov...")

for algorithm, raw_file_name in ALGO_RAW_FILES.items():
    raw_file_path = os.path.join(RAW_RESULTS_DIR, raw_file_name)
    core_list_file_path = os.path.join(CORE_LISTS_DIR, ALGO_CORE_FILES.get(algorithm, ""))

    print(f"Spracovávam raw výsledky pre algoritmus: {algorithm} zo súboru {raw_file_path}")

    if not os.path.exists(raw_file_path):
        print(f"  CHYBA: Súbor {raw_file_path} sa nenašiel. Preskakujem tento algoritmus.")
        continue

    if not os.path.exists(core_list_file_path):
        print(f"  CHYBA: Súbor s core uzlami {core_list_file_path} sa nenašiel. Nebudem vedieť presne určiť parametre. Preskakujem.")
        continue

    try:
        df_raw = pd.read_csv(raw_file_path)
        print(f"  Načítaných {len(df_raw)} riadkov z {raw_file_path}.")
        
        # Načítať súbor s core uzlami, aby sme zistili PRESNÉ PARAMETRE pre každý network/run
        df_core_params = pd.read_csv(core_list_file_path)
        print(f"  Načítaných {len(df_core_params)} riadkov z {core_list_file_path} (na určenie parametrov).")

        # Zistíme stĺpce s parametrami v súbore core uzlov (okrem Network, algorithm, Core_Nodes)
        param_cols_in_core_file = [col for col in df_core_params.columns if col not in ['Network', 'algorithm', 'Core_Nodes']]

        # Pre každú sieť, ktorá je v súbore s core uzlami (tzn. pre ktorú sme spustili extrakciu)
        for index, row_core_params in df_core_params.iterrows():
            network_name = row_core_params['Network']
            
            # Získame presné parametre použité pre túto sieť/algoritmus pri extrakcii core uzlov
            current_params = {param: row_core_params[param] for param in param_cols_in_core_file}
            
            print(f"    Filtrujem pre sieť '{network_name}' s parametrami: {current_params}")

            # Filtrovanie RAW dát na presné parametre
            df_filtered = df_raw[df_raw['network'] == network_name].copy()
            
            for param_col, param_val in current_params.items():
                 if param_col in df_filtered.columns:
                      # Porovnavat floaty s toleranciou ak su to cisla
                      if isinstance(param_val, (int, float)) and param_col in ['parameters.alpha', 'parameters.beta', 'parameters.num_runs']:
                           df_filtered = df_filtered[np.isclose(df_filtered[param_col], param_val, atol=1e-6)]
                      else:
                           df_filtered = df_filtered[df_filtered[param_col] == param_val] # Stringy alebo ine typy presne


            if df_filtered.empty:
                print(f"    Upozornenie: Nenašli sa raw výsledky pre sieť '{network_name}' s presnými parametrami {current_params}. Preskakujem.")
                continue

            # Priemerovanie metrík cez opakovania
            averaged_metrics = df_filtered[[
                'runtime',
                'ideal_pattern_match',
                'core_size',
                'periphery_size',
                'core_percentage',
                'core_density',
                'periphery_density',
                'core_periphery_ratio',
            ]].mean().to_dict() # Priemery ako slovnik

            # Pridanie identifikátorov
            averaged_metrics['Network'] = network_name
            averaged_metrics['Algorithm'] = algorithm
            # Pridanie presných parametrov, pre istotu
            for param_key, param_value in current_params.items():
                 averaged_metrics[f'Param_{param_key}'] = param_value # Prefix, aby sa vyhlo konfliktom

            # Vypočítame priemerný stupeň jadra a periférie z Density a Size
            core_size_avg = averaged_metrics.get('core_size', np.nan)
            periphery_size_avg = averaged_metrics.get('periphery_size', np.nan)
            core_density_avg = averaged_metrics.get('core_density', np.nan)
            periphery_density_avg = averaged_metrics.get('periphery_density', np.nan)

            avg_degree_core = np.nan
            if pd.notna(core_density_avg) and pd.notna(core_size_avg) and core_size_avg > 0:
                 avg_degree_core = core_density_avg * (core_size_avg - 1)

            avg_degree_periphery = np.nan
            if pd.notna(periphery_density_avg) and pd.notna(periphery_size_avg) and periphery_size_avg > 0:
                 avg_degree_periphery = periphery_density_avg * (periphery_size_avg - 1)

            averaged_metrics['Calculated_Avg_Degree_Core'] = avg_degree_core
            averaged_metrics['Calculated_Avg_Degree_Periphery'] = avg_degree_periphery
            
            # Pridanie do zoznamu
            averaged_algo_metrics.append(averaged_metrics)

        print(f"  Dokončené spracovanie raw dát pre {algorithm}.")

    except Exception as e:
        print(f"  FATÁLNA CHYBA pri spracovaní raw dát pre algoritmus {algorithm}: {e}")
        traceback.print_exc()


# Konvertovať spriemerované metriky algoritmov na DataFrame
if not averaged_algo_metrics:
    print("\nCHYBA: Nepodarilo sa získať spriemerované metriky algoritmov. Skript končí.")
    sys.exit(1)

df_averaged_algo = pd.DataFrame(averaged_algo_metrics)

# --- Spojenie všetkých dát do jedného DataFrame ---

print("\nSpájam všetky dáta...")

# Začneme s vlastnosťami sietí
df_final = df_properties.copy()

# Pripojíme spriemerované metriky algoritmov (rozdelíme podľa algoritmu a pripojíme)
for algorithm in ALGO_RAW_FILES.keys():
    df_algo_subset = df_averaged_algo[df_averaged_algo['Algorithm'] == algorithm].copy()
    # Zahodíme stĺpce Network a Algorithm z DataFrame subsetu pred spájaním, lebo Network je index
    df_algo_subset = df_algo_subset.copy()  # Create a copy to avoid modifying the original
    
    # Najprv premenujeme stĺpce metrík, aby obsahovali názov algoritmu
    metric_cols = [col for col in df_algo_subset.columns if col not in ['Network', 'Algorithm'] + [f'Param_{p}' for p in param_cols_in_core_file]]
    rename_dict = {col: f"{algorithm}_{col}" for col in metric_cols}
    df_algo_subset.rename(columns=rename_dict, inplace=True)
    
    # Teraz upravíme metric_cols, aby obsahovali prefixy algoritmu
    prefixed_metric_cols = [f"{algorithm}_{col}" for col in metric_cols]
    
    # Pripojíme parametre použité pre tento algoritmus (ak sa majú zobraziť vo finálnej tabulke)
    param_cols_for_merge = [f'Param_{p}' for p in param_cols_in_core_file if f'Param_{p}' in df_algo_subset.columns]
    prefixed_param_cols = []
    
    if param_cols_for_merge:
        rename_param_dict = {col: f"{algorithm}_{col.replace('Param_', '')}" for col in param_cols_for_merge}
        df_algo_subset.rename(columns=rename_param_dict, inplace=True)
        prefixed_param_cols = list(rename_param_dict.values())
    
    # Nastavíme index až po premenovaní stĺpcov
    df_algo_subset.set_index('Network', inplace=True)
    
    # Použijeme prefixované názvy stĺpcov pre spojenie
    cols_to_merge = prefixed_metric_cols + prefixed_param_cols
    
    # Spojiť s hlavným DataFrame, overime že všetky stĺpce existujú
    existing_cols = [col for col in cols_to_merge if col in df_algo_subset.columns]
    df_final = df_final.merge(df_algo_subset[existing_cols], left_index=True, right_index=True, how='left')


# Pripojíme dáta o shlukovaní jadra/periférie
if not df_cp_clustering.empty:
    # Podobne premenovať stĺpce shlukovania
    df_cp_clustering.set_index(['Network', 'Algorithm'], inplace=True)
    
    # Vytvoríme plochú tabuľku pre spojenie
    df_cp_clustering_pivot = df_cp_clustering.unstack(level='Algorithm') # Pivotuje algoritmy na stĺpce
    
    # Preusporiadame stĺpce po pivotovaní a premenujeme ich (napr. ('Core Avg Clustering', 'BE') -> 'BE_Core Avg Clustering')
    new_cols = {}
    for col_tuple in df_cp_clustering_pivot.columns:
        metric_name = col_tuple[0]
        algo_name = col_tuple[1]
        new_cols[col_tuple] = f"{algo_name}_{metric_name}"
    
    # Premenujeme stĺpce a úplne resetujeme index
    df_cp_clustering_pivot.columns = [new_cols[col] for col in df_cp_clustering_pivot.columns]
    df_cp_clustering_pivot = df_cp_clustering_pivot.reset_index()
    
    # Teraz explicitne nastavíme 'Network' ako index
    df_cp_clustering_pivot.set_index('Network', inplace=True)
    
    # Spojiť s hlavným DataFrame
    df_final = df_final.merge(df_cp_clustering_pivot, left_index=True, right_index=True, how='left')


# --- Výpočet Korelácií ---

print("\nVypočítavam korelácie...")

# Definovanie stĺpcov s vlastnosťami sietí a metrikami algoritmov
network_properties_cols = [
    'Nodes (N)', 'Edges (E)', 'Density', 'Average Degree',
    'Assortativity', 'Average Clustering Coefficient', 'Modularity',
    'Num Communities', 'Average Betweenness Centrality (Network)', 'Average Closeness Centrality (Network)'
]

# Uistíme sa, že tieto stĺpce naozaj existujú v df_final
network_properties_cols = [col for col in network_properties_cols if col in df_final.columns]


# Získanie názvov stĺpcov metrík pre každý algoritmus z finálneho DataFrame
algo_metric_cols = {
    algorithm: [
        f'{algorithm}_runtime',
        f'{algorithm}_ideal_pattern_match',
        f'{algorithm}_core_percentage',
        f'{algorithm}_core_density',
        f'{algorithm}_periphery_density',
        f'{algorithm}_core_periphery_ratio',
        # Pridajte ďalšie spriemerované metriky ak ste ich extrahovali/potrebujete
        # f'{algorithm}_Calculated_Avg_Degree_Core', # Toto bude v sumarizacii struktury
        # f'{algorithm}_Calculated_Avg_Degree_Periphery', # Toto bude v sumarizacii struktury
    ] for algorithm in ALGO_RAW_FILES.keys()
}

# Filtrovať len tie, ktoré reálne existujú vo finálnom DF
for algo, cols in algo_metric_cols.items():
    algo_metric_cols[algo] = [col for col in cols if col in df_final.columns]


# Vypočítať korelačnú maticu pre relevantné stĺpce
correlation_matrix = df_final[network_properties_cols + [col for sublist in algo_metric_cols.values() for col in sublist]].corr(method='pearson')

# Extrahovať korelácie medzi vlastnosťami sietí a metrikami algoritmov
correlation_results = []

for net_prop in network_properties_cols:
    for algorithm, metrics in algo_metric_cols.items():
        for metric in metrics:
            # Korelacia medzi vlastnostou siete a metrikou algoritmu
            correlation_value = correlation_matrix.loc[net_prop, metric]
            
            correlation_results.append({
                "Network Property": net_prop,
                "Algorithm": algorithm,
                "Algorithm Metric": metric,
                "Correlation (r)": correlation_value,
            })

df_correlations = pd.DataFrame(correlation_results)


# --- Príprava Tabuliek Vlastností Nájdenej Štruktúry ---

print("\nPripravujem tabuľky vlastností nájdenej štruktúry...")

# Definovanie stĺpcov vlastností nájdených štruktúr
structure_properties_cols = [
    'core_size', # Spriemerované z raw dát
    'periphery_size', # Spriemerované z raw dát
    'core_percentage', # Spriemerované z raw dát
    'core_density', # Spriemerované z raw dát
    'periphery_density', # Spriemerované z raw dát
    'core_periphery_ratio', # Spriemerované z raw dát
    'Calculated_Avg_Degree_Core', # Vypocitane z density/size
    'Calculated_Avg_Degree_Periphery', # Vypocitane z density/size
    # Priemerné centrality jadra/periférie - ak máte tie dáta v inej tabuľke, sem ich treba načítať a spojiť
    # Zatial pouzijem len tie co sa daju vypocitat/su z LRC/BE suborov shlukovania
    'Core Avg Clustering', # Zo suboru shlukovania
    'Periphery Avg Clustering', # Zo suboru shlukovania
    'Clustering Ratio (C/P)', # Zo suboru shlukovania
]

# Získať tieto stĺpce pre každý algoritmus z df_final
structure_data = []
for algorithm in ALGO_RAW_FILES.keys():
    # Stĺpce metrík relevantné pre štruktúru s prefixom algoritmu
    algo_struct_cols = [f'{algorithm}_{col}' for col in structure_properties_cols if col in df_final.columns.str.replace(f'{algorithm}_', '')]
    
    # Pridat stlpce shlukovania z LRC suboru, ktore uz maju prefix algoritmou
    algo_struct_cols.extend([f'{algorithm}_Core Avg Clustering', f'{algorithm}_Periphery Avg Clustering', f'{algorithm}_Clustering Ratio (C/P)'])
    
    # Filtrovať len tie, ktoré reálne existujú vo finálnom DF
    algo_struct_cols = [col for col in algo_struct_cols if col in df_final.columns]

    # Vybrať relevantné stĺpce z df_final a pridať stĺpce Network a Algorithm
    df_algo_struct = df_final[['Network']].copy() # Získať index ako stĺpec
    df_algo_struct['Algorithm'] = algorithm
    
    # Pripojiť stĺpce vlastností štruktúry
    df_algo_struct = df_algo_struct.merge(df_final[algo_struct_cols], left_on='Network', right_index=True, how='left')

    structure_data.append(df_algo_struct)

df_structure_properties = pd.concat(structure_data, ignore_index=True)


# Voliteľné: Vypočítať priemery vlastností štruktúry podľa kategórie sietí (Malé, Stredné, Veľké)
# Potrebujeme na to vedieť, ktorá sieť patrí do ktorej kategórie.
# Môžeme si to zadefinovať priamo tu alebo načítať z iného súboru, ak ho máte.
# Zatiaľ to vynechám, ale ak chcete, dajte vedieť a dorobíme priemery podľa kategórií.


# --- Uloženie finálnych výsledkov ---

print("\nUkladám finálne výsledky...")

# Uloženie korelácií
try:
    df_correlations.to_csv(OUTPUT_CORRELATIONS_CSV, index=False, float_format='%.6f')
    print(f"Úspešne uložené korelácie do: {OUTPUT_CORRELATIONS_CSV}")
except Exception as e:
    print(f"CHYBA pri ukladaní korelácií: {e}")
    traceback.print_exc()

# Uloženie vlastností nájdenej štruktúry (na úrovni jednotlivých sietí)
try:
    df_structure_properties.to_csv(OUTPUT_STRUCTURE_PROPERTIES_CSV, index=False, float_format='%.6f')
    print(f"Úspešne uložené vlastnosti nájdenej štruktúry do: {OUTPUT_STRUCTURE_PROPERTIES_CSV}")
except Exception as e:
    print(f"CHYBA pri ukladaní vlastností nájdenej štruktúry: {e}")
    traceback.print_exc()


print("\nFinálny skript analýzy dokončený.")