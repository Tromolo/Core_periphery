import pandas as pd
import numpy as np
import os
import sys
import traceback

project_path = '/home/hruby/PycharmProjects/Core_periphery'
if project_path not in sys.path:
    sys.path.append(project_path)

centrality_dir = os.path.join(project_path, "results", "node_centralities")
optimal_cores_dir = os.path.join(project_path, "results", "optimal_cores")

output_csv = "centrality_vs_core_analysis.csv"

algorithms = {
    "BE": os.path.join(optimal_cores_dir, "be_optimal_cores.csv"),
    "Rombach": os.path.join(optimal_cores_dir, "rombach_optimal_cores.csv"),
    "Cucuringu": os.path.join(optimal_cores_dir, "cucuringu_optimal_cores.csv"),
}

print("Spúšťam analýzu centrality core vs. periphery uzlov...")

core_dfs = {}
for algo, path in algorithms.items():
    try:
        core_dfs[algo] = pd.read_csv(path)
        print(f"Načítané core uzly pre {algo} z {path}")
    except FileNotFoundError:
        print(f"VAROVANIE: Súbor s core uzlami pre {algo} nebol nájdený ({path}). Tento algoritmus bude preskočený.")
    except Exception as e:
        print(f"CHYBA pri načítaní core uzlov pre {algo} z {path}: {e}")

if not core_dfs:
    print("CHYBA: Nepodarilo sa načítať žiadne dáta o core uzloch. Skript končí.")
    sys.exit(1)

analysis_results = []

available_networks = core_dfs[list(core_dfs.keys())[0]]['Network'].unique()

for network_name in available_networks:
    print(f"\nSpracúvam sieť: {network_name}")
    
    safe_network_name = network_name.replace(" ", "_").replace("-","_").lower()
    centrality_file = os.path.join(centrality_dir, f"{safe_network_name}_centralities.csv")
    
    try:
        centrality_df = pd.read_csv(centrality_file)
        centrality_df['node_id'] = centrality_df['node_id'].astype(str)
        centrality_df.set_index('node_id', inplace=True)
        print(f"  Načítané centrality pre {network_name} z {centrality_file} ({len(centrality_df)} uzlov)")
    except FileNotFoundError:
        print(f"  CHYBA: Súbor s centralitami pre {network_name} nebol nájdený ({centrality_file}). Sieť bude preskočená.")
        continue
    except Exception as e:
        print(f"  CHYBA pri načítaní centralít pre {network_name}: {e}")
        continue
        
    all_nodes_in_network = set(centrality_df.index)
    if not all_nodes_in_network:
         print("  Varovanie: Sieť nemá žiadne uzly v súbore centralít.")
         continue

    for algo, core_df in core_dfs.items():
        print(f"  Analyzujem algoritmus: {algo}")
        
        network_core_data = core_df[core_df['Network'] == network_name]
        
        if network_core_data.empty:
            print(f"    Varovanie: Žiadne dáta o core uzloch pre {algo} a sieť {network_name}.")
            continue
            
        core_nodes_str = network_core_data.iloc[0]['Core_Nodes']
        
        core_nodes = set()
        if pd.notna(core_nodes_str) and core_nodes_str != "ERROR" and core_nodes_str:
            core_nodes = set(core_nodes_str.split(',')) 
            
            missing_core_nodes = core_nodes - all_nodes_in_network
            if missing_core_nodes:
                print(f"    Varovanie: Nasledujúce core uzly pre {algo} neboli nájdené v súbore centralít: {missing_core_nodes}")
                core_nodes = core_nodes.intersection(all_nodes_in_network) 
                
        elif core_nodes_str == "ERROR":
             print(f"    Varovanie: Pri generovaní core uzlov pre {algo} nastala chyba. Preskakujem.")
             continue
        else:
            print(f"    Varovanie: Zoznam core uzlov pre {algo} je prázdny alebo NaN.")

        periphery_nodes = all_nodes_in_network - core_nodes
        
        print(f"    Rozdelenie: {len(core_nodes)} core, {len(periphery_nodes)} periphery.")

        avg_centralities = {'Core': {}, 'Periphery': {}}
        
        node_groups = {'Core': core_nodes, 'Periphery': periphery_nodes}
        
        for group_name, nodes in node_groups.items():
            if not nodes: 
                avg_centralities[group_name] = {
                    'Avg Degree': np.nan, 
                    'Avg Betweenness': np.nan, 
                    'Avg Closeness': np.nan
                }
                continue

            group_centralities = centrality_df.loc[list(nodes)]
            
            avg_centralities[group_name]['Avg Degree'] = group_centralities['degree_centrality'].mean(skipna=True)
            avg_centralities[group_name]['Avg Betweenness'] = group_centralities['betweenness_centrality'].mean(skipna=True)
            avg_centralities[group_name]['Avg Closeness'] = group_centralities['closeness_centrality'].mean(skipna=True)
            
            print(f"    Priemerné centrality ({group_name}): "
                  f"Degree={avg_centralities[group_name]['Avg Degree']:.4g}, "
                  f"Betweenness={avg_centralities[group_name]['Avg Betweenness']:.4g}, "
                  f"Closeness={avg_centralities[group_name]['Avg Closeness']:.4g}")

        ratios = {'Degree Ratio': np.nan, 'Betweenness Ratio': np.nan, 'Closeness Ratio': np.nan}
        if avg_centralities['Periphery']['Avg Degree'] and pd.notna(avg_centralities['Periphery']['Avg Degree']) and avg_centralities['Periphery']['Avg Degree'] != 0:
            ratios['Degree Ratio'] = avg_centralities['Core']['Avg Degree'] / avg_centralities['Periphery']['Avg Degree']
        if avg_centralities['Periphery']['Avg Betweenness'] and pd.notna(avg_centralities['Periphery']['Avg Betweenness']) and avg_centralities['Periphery']['Avg Betweenness'] != 0:
             ratios['Betweenness Ratio'] = avg_centralities['Core']['Avg Betweenness'] / avg_centralities['Periphery']['Avg Betweenness']
        if avg_centralities['Periphery']['Avg Closeness'] and pd.notna(avg_centralities['Periphery']['Avg Closeness']) and avg_centralities['Periphery']['Avg Closeness'] != 0:
             ratios['Closeness Ratio'] = avg_centralities['Core']['Avg Closeness'] / avg_centralities['Periphery']['Avg Closeness']
             
        print(f"    Pomery (Core/Periphery): "
              f"Degree={ratios['Degree Ratio']:.2f}x, "
              f"Betweenness={ratios['Betweenness Ratio']:.2f}x, "
              f"Closeness={ratios['Closeness Ratio']:.2f}x")

        analysis_results.append({
            "Network": network_name,
            "Algorithm": algo,
            "Num Core Nodes": len(core_nodes),
            "Num Periphery Nodes": len(periphery_nodes),
            "Core Avg Degree": avg_centralities['Core']['Avg Degree'],
            "Periphery Avg Degree": avg_centralities['Periphery']['Avg Degree'],
            "Degree Ratio (C/P)": ratios['Degree Ratio'],
            "Core Avg Betweenness": avg_centralities['Core']['Avg Betweenness'],
            "Periphery Avg Betweenness": avg_centralities['Periphery']['Avg Betweenness'],
            "Betweenness Ratio (C/P)": ratios['Betweenness Ratio'],
            "Core Avg Closeness": avg_centralities['Core']['Avg Closeness'],
            "Periphery Avg Closeness": avg_centralities['Periphery']['Avg Closeness'],
            "Closeness Ratio (C/P)": ratios['Closeness Ratio'],
        })

if analysis_results:
    df_analysis = pd.DataFrame(analysis_results)
    column_order = [
        "Network", "Algorithm", "Num Core Nodes", "Num Periphery Nodes",
        "Core Avg Degree", "Periphery Avg Degree", "Degree Ratio (C/P)",
        "Core Avg Betweenness", "Periphery Avg Betweenness", "Betweenness Ratio (C/P)",
        "Core Avg Closeness", "Periphery Avg Closeness", "Closeness Ratio (C/P)"
    ]
    df_analysis = df_analysis.reindex(columns=column_order)
    
    try:
        df_analysis.to_csv(output_csv, index=False, float_format='%.4f') 
        print(f"\nVýsledky analýzy centrality core vs. periphery uložené do: {output_csv}")
        print("\n--- Súhrnná tabuľka výsledkov ---")
        print(df_analysis.to_string())
    except Exception as e:
        print(f"\nCHYBA pri ukladaní finálnych výsledkov do {output_csv}: {e}")
else:
    print("\nNeboli vygenerované žiadne výsledky analýzy.")

print("\nSkript analyze_centrality_vs_core.py dokončený.")
