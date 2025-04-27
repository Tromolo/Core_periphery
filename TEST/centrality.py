import networkx as nx
import pandas as pd
import os
import time
import sys
import numpy as np # Pridame numpy pre manipulaciu s cislami

project_path = "." 

NETWORK_NAMES = [
    "Karate Club", 
    "Dolphins", 
    "Les Miserables",
    "Football",
    "Facebook Combined", 
    "Power Grid",      
    "Bianconi-0.7",    
    "Bianconi-0.97",
    "YeastL"
]

OUTPUT_SUMMARY_CSV = "network_properties_summary.csv"

OUTPUT_CENTRALITY_DIR = os.path.join(project_path, "results", "node_centralities")


CENTRALITY_NODE_LIMIT = 10000

def load_graph_from_path(path):
    """
    Načíta graf z cesty pomocou networkx.
    Rozpoznáva .gml a .csv (pomocou pandas pre robustnosť).
    """
    _, ext = os.path.splitext(path)
    G = None 

    if ext == '.gml':
        try:
            print(f"  Načítavam GML {path} pomocou nx.read_gml")
            G = nx.read_gml(path, label='id') 
            # Kontrola typu uzlov a pretypovanie na string pre konzistenciu
            if G.number_of_nodes() > 0 and not isinstance(list(G.nodes())[0], str):
                 print(f"  INFO: Uzly GML nie sú string, pretypujem.")
                 G = nx.relabel_nodes(G, {n: str(n) for n in G.nodes()})

        except Exception as load_error:
            print(f"  CHYBA: Zlyhalo načítanie GML {path}: {load_error}")
            # Zatial nezavrhujeme nacitanie, nechavame G=None
            # raise load_error # Nezavadzame pri chybe nacitania

    elif ext == '.csv':
        try:
            print(f"  Načítavam CSV {path} pomocou pandas (delimiter=';')")
            df = pd.read_csv(path, delimiter=';', header=None, usecols=[0, 1], 
                             names=['source', 'target'], 
                             dtype=str, # Nacitame ako string, aby sme sa vyhli problemom s uzlami
                             comment='#') 
            
            # Odstranenie riadkov s chybnymi hodnotami alebo NaN
            df.dropna(subset=['source', 'target'], inplace=True)
            
            # Odstranenie prazdnych stringov, ak by sa tam dostali
            df = df[(df['source'] != '') & (df['target'] != '')]
            
            if df.empty:
                print(f"  Varovanie: CSV {path} je po čistení prázdne.")
                return nx.Graph() # Vrati prazdny graf
            
            G = nx.from_pandas_edgelist(df, source='source', target='target', create_using=nx.Graph)
            print(f"  Graf vytvorený z pandas: {G.number_of_nodes()} uzlov, {G.number_of_edges()} hrán")

        except Exception as load_error:
             print(f"  CHYBA: Zlyhalo načítanie/spracovanie CSV {path} pomocou pandas: {load_error}")
             # Zatial nezavrhujeme nacitanie, nechavame G=None
             # raise load_error # Nezavadzame pri chybe nacitania

    else:
        # Toto by uz malo vyvolat chybu, format by mal byt podporovany
        raise ValueError(f"Nepodporovaný formát súboru: {ext} pre {path}")

    if G is not None: # Ak sa nacitanie podarilo
        if isinstance(G, (nx.MultiGraph, nx.MultiDiGraph)):
             print(f"  Varovanie: Graf načítaný ako MultiGraph/MultiDiGraph. Konvertujem na jednoduchý Graf.")
             G = nx.Graph(G)
        
        # Odstranenie vlastnych sluciek
        G.remove_edges_from(nx.selfloop_edges(G))
        
        # Pretypovanie uzlov na string este raz pre istotu
        if G.number_of_nodes() > 0 and not isinstance(list(G.nodes())[0], str):
             print(f"  INFO: Finalne pretypovanie uzlov na string.")
             try:
                 G = nx.relabel_nodes(G, {n: str(n) for n in G.nodes()})
             except Exception as relabel_error:
                 print(f"  CHYBA pri finalnom pretypovaní uzlov na string: {relabel_error}")
                 # V pripade zlyhania pretypovania, mozeme skusit pokracovat s povodnymi typmi, ak su hashovatelne,
                 # ale lepsie je nahlasit problem.
                 # Alebo vratit None/prazdny graf ak je to kriticke
                 G = None # Znaci chybu, ak sa neda pretypovat

    # Kontrola prazdneho grafu po nacitani a cisteni
    if G is not None and G.number_of_nodes() == 0 and G.number_of_edges() == 0:
         print(f"  Varovanie: Graf pre {path} je po spracovaní prázdny.")
         # Mozeme sa rozhodnut, ci ho vratime alebo None
         # Vratime prazdny graf, nech pocet uzlov a hran bude 0
         return nx.Graph()
         
    if G is None: # Ak nastala chyba pri nacitani alebo pretypovani
         print(f"  CHYBA: Graf pre {path} sa nepodarilo úspešne načítať alebo spracovať.")

    return G


def load_network(network_name):
    G = None
    print(f"\nNačítavam sieť: {network_name}")
    
    try:
        if network_name == 'Karate Club':
            G = nx.karate_club_graph()
            G = nx.relabel_nodes(G, {i: str(i) for i in G.nodes()}) 
            print(f"  Sieť Karate Club načítaná z networkx (uzly pretypované na string)")
        
        elif network_name == 'Dolphins':
            path = os.path.join(project_path, 'data/male_site/dolphins.gml')
            G = load_graph_from_path(path)
            print(f"  Sieť Dolphins načítaná z {path}")
                
        elif network_name == 'Les Miserables':
            path = os.path.join(project_path, 'data/male_site/lesmis.gml')
            G = load_graph_from_path(path)
            print(f"  Sieť Les Miserables načítaná z {path}")
                
        elif network_name == 'Football':
            path = os.path.join(project_path, 'data/male_site/football.gml')
            G = load_graph_from_path(path)
            print(f"  Sieť Football načítaná z {path}")
                
        elif network_name == 'Facebook Combined':
            path = os.path.join(project_path, 'data/male_site/facebook_combined.csv') 
            G = load_graph_from_path(path) 
            print(f"  Sieť Facebook Combined načítaná z {path}")
                
        elif network_name == 'Power Grid':
            path = os.path.join(project_path, 'data/male_site/USpowergrid_n4941.csv') 
            G = load_graph_from_path(path)
            print(f"  Sieť Power Grid načítaná z {path}")
                
        elif network_name == 'Bianconi-0.7':
            path = os.path.join(project_path, 'data/site_pro_modely/Bianconi-Triadic-Closure 0.7 3.csv')
            G = load_graph_from_path(path)
            print(f"  Sieť Bianconi-0.7 načítaná z {path}")
                
        elif network_name == 'Bianconi-0.97':
            path = os.path.join(project_path, 'data/site_pro_modely/Bianconi-Triadic-Closure 0.97 3.csv')
            G = load_graph_from_path(path)
            print(f"  Sieť Bianconi-0.97 načítaná z {path}")
            
        elif network_name == 'YeastL':
            path = os.path.join(project_path, 'data/male_site/YeastL.csv')
            G = load_graph_from_path(path)
            print(f"  Sieť YeastL načítaná z {path}")
            
        else:
            # Nezname siete by uz nemali byt v NETWORK_NAMES, ale ako poistka
            print(f"  CHYBA: Neznáma sieť v zozname: {network_name}")
            return None # Explicitne vratime None pre neznamu siet

    except Exception as e:
        print(f"FATÁLNA CHYBA pri načítavaní siete {network_name}: {e}")
        return None 

    # Finalna kontrola a cistenie po nacitani z akehokolvek zdroja
    if G is not None:
         # Odstranenie vlastnych sluciek este raz pre istotu
         G.remove_edges_from(nx.selfloop_edges(G)) 
         
         # Pretypovanie uzlov na string ako finalny krok
         if G.number_of_nodes() > 0 and not isinstance(list(G.nodes())[0], str):
              print(f"  INFO: Finalne pretypovanie uzlov na string.")
              try:
                  G = nx.relabel_nodes(G, {n: str(n) for n in G.nodes()})
              except Exception as relabel_error:
                  print(f"  CHYBA pri finalnom pretypovaní uzlov na string: {relabel_error}")
                  G = None # Ak zlyha pretypovanie, graf je pravdepodobne nepouzitelny
         
         # Kontrola prazdneho grafu
         if G is not None and G.number_of_nodes() == 0:
             print(f"  Varovanie: Sieť {network_name} je prázdna po čistení (0 uzlov).")


    if G is None or G.number_of_nodes() == 0:
         print(f"  Varovanie: Nepodarilo sa načítať alebo sieť {network_name} je prázdna. Preskakujem.")
         return None

    print(f"  Úspešne načítaná a pripravená sieť: {G.number_of_nodes()} uzlov, {G.number_of_edges()} hrán")
    return G


os.makedirs(OUTPUT_CENTRALITY_DIR, exist_ok=True)
print(f"\nVýstupné súbory centralít budú uložené do: {OUTPUT_CENTRALITY_DIR}")


summary_results = []
print("\nStarting network property calculation...")

for network_name in NETWORK_NAMES:
    
    start_time = time.time()
    centrality_data_list = [] 
    
    # Inicializacia metrik pre suhrn pre pripad chyby
    N, E, density, avg_degree, assortativity, avg_clustering, modularity_score, num_communities = [np.nan] * 8


    try:
        G = load_network(network_name)
        
        if G is None:
            print(f"Preskakujem výpočty pre {network_name}, keďže sa ju nepodarilo načítať alebo je prázdna.")
            summary_results.append({
                "Network": network_name, 
                "Nodes (N)": 0, # 0 uzlov pre prazdny/nenacitany graf
                "Edges (E)": 0, # 0 hran
                "Density": 0, # Hustota 0
                "Average Degree": 0, # Priemerny stupen 0
                "Assortativity": np.nan, # Nedefinovane
                "Average Clustering Coefficient": np.nan, # Nedefinovane
                "Modularity": np.nan, # Nedefinovane
                "Num Communities": np.nan, # Nedefinovane
                })
            continue

        N = G.number_of_nodes()
        E = G.number_of_edges()
        
        density = 0
        if N > 1: 
            density = nx.density(G)

        avg_degree = 0
        if N > 0: # Priemerny stupen je definovany ak je aspon 1 uzol (aj ked pre 1 uzol je stupen 0)
            avg_degree = 2 * E / N

        assortativity = np.nan # Inicializacia na NaN
        if N > 1 and E > 0: # Assortativity vyzaduje aspon 2 uzly a aspon 1 hranu
             try:
                 # Vypocet assortativity. V GraphX je degree_assortativity_coefficient
                 # Treba osetrit neprepojene komponenty alebo specificke struktury, ktore mozu sposobit chyby
                 if nx.is_directed(G):
                      print("  INFO: Graph je orientovany, assortativita stupna mozem mat iny vyznam.")
                      # Mozete vybrat, ci pocitat in/out assortativitu alebo konvertovat na neorientovany
                      # Pre jednoduchost skusime neorientovany
                      assortativity = nx.degree_assortativity_coefficient(nx.Graph(G))
                 else:
                      assortativity = nx.degree_assortativity_coefficient(G)
                 print(f"  Assortativity calculated: {assortativity:.4f}")
             except Exception as e:
                  print(f"  WARNING: Could not calculate assortativity for {network_name}: {e}")
                  assortativity = np.nan # Zaznamenat ako NaN v pripade chyby


        avg_clustering = np.nan # Inicializacia na NaN
        if N > 0 and E > 0: # Priemerny shlukovaci koeficient vyzaduje aspon 1 uzol a 1 hranu pre aspon 1 uzol
             try:
                 # average_clustering(G) automaticky ignoruje izolovane uzly
                 avg_clustering = nx.average_clustering(G)
                 print(f"  Average Clustering Coefficient: {avg_clustering:.4f}")
             except Exception as e:
                  print(f"  WARNING: Could not calculate average clustering for {network_name}: {e}")
                  avg_clustering = np.nan # Zaznamenat ako NaN v pripade chyby

        modularity_score = np.nan # Inicializacia na NaN
        num_communities = np.nan # Inicializacia na NaN
        if E > 0 and N > 1: # Modularita a komunity vyzaduju aspon 2 uzly a aspon 1 hranu
            print("  Calculating communities (Louvain)...")
            try:
                # Ensure determinism by setting a seed if available in community function
                # Older networkx might not have seed in louvain_communities
                if 'seed' in nx.community.louvain_communities.__code__.co_varnames:
                     communities = nx.community.louvain_communities(G, seed=42) 
                else:
                     print("  INFO: networkx.community.louvain_communities does not support seed.")
                     communities = nx.community.louvain_communities(G)

                if communities: # Uisti sa, ze komunity boli najdene (moze vratit prazdny zoznam pre zvlastne pripady)
                    modularity_score = nx.community.modularity(G, communities)
                    num_communities = len(communities)
                    print(f"  Modularity: {modularity_score:.4f}, Num Communities: {num_communities}")
                else:
                    print(f"  WARNING: Community detection did not find any communities for {network_name}.")
                    modularity_score = np.nan # Nedefinovane ak sa nenajdu komunity
                    num_communities = 0 # 0 komunit ak sa ziadna nenajde

            except Exception as e:
                print(f"  WARNING: Could not calculate communities/modularity for {network_name}: {e}")
                modularity_score = np.nan # Zaznamenat ako NaN v pripade chyby
                num_communities = np.nan # Zaznamenat ako NaN v pripade chyby
        else:
             print("  Skipping community detection (no edges or only 1 node).")


        deg_cen = {}
        bet_cen = {}
        clo_cen = {}
        local_clustering_dict = {} # Novy slovnik pre lokalny shlukovaci koeficient

        if N > 0:
            try:
                print("  Calculating Degree Centrality...")
                deg_cen = nx.degree_centrality(G)
                print(f"  Degree Centrality calculated for {len(deg_cen)} nodes.")
            except Exception as e:
                 print(f"  WARNING: Could not calculate Degree Centrality for {network_name}: {e}")

            try:
                print("  Calculating Local Clustering Coefficient...")
                # nx.clustering vrati slovnik {uzol: koeficient}
                local_clustering_dict = nx.clustering(G)
                print(f"  Local Clustering Coefficient calculated for {len(local_clustering_dict)} nodes.")
            except Exception as e:
                 print(f"  WARNING: Could not calculate Local Clustering Coefficient for {network_name}: {e}")


            if N <= CENTRALITY_NODE_LIMIT: 
                try:
                    print(f"  Calculating Betweenness Centrality (N={N} <= limit={CENTRALITY_NODE_LIMIT})...")
                    bet_cen = nx.betweenness_centrality(G, normalized=True, k=None) # k=None pre presný výpočet
                    print(f"  Betweenness Centrality calculated for {len(bet_cen)} nodes.")
                except Exception as e:
                     print(f"  WARNING: Could not calculate Betweenness Centrality for {network_name}: {e}")
                     
                try:
                    print(f"  Calculating Closeness Centrality (N={N} <= limit={CENTRALITY_NODE_LIMIT})...")
                    # Closeness vyzaduje prepojeny graf. Ak nie je, NetworkX pocita len v ramci komponentu a vrati 0 pre uzly mimo.
                    # Alebo mozeme explicitne pocitat len pre najvacsi komponent.
                    # networkx.closeness_centrality(G) - toto je bezpecnejsie, vrati 0 pre nedosiahnutelne uzly.
                    clo_cen = nx.closeness_centrality(G)
                    print(f"  Closeness Centrality calculated for {len(clo_cen)} nodes (all).")
                         
                except Exception as e:
                     print(f"  WARNING: Could not calculate Closeness Centrality for {network_name}: {e}")
            else:
                print(f"  Skipping Betweenness/Closeness calculation for large network (N={N} > limit={CENTRALITY_NODE_LIMIT}).")

            print("  Preparing detailed node data...")
            node_list = list(G.nodes())
            for node in node_list:
                 centrality_data_list.append({
                     'node_id': node,
                     'degree_centrality': deg_cen.get(node, np.nan), # Pouzit .get s defaultom np.nan
                     'betweenness_centrality': bet_cen.get(node, np.nan),
                     'closeness_centrality': clo_cen.get(node, np.nan),
                     'local_clustering_coefficient': local_clustering_dict.get(node, np.nan) # Pridane
                 })
        else:
             print("  Skipping node data generation (no nodes).")

        if centrality_data_list:
            centrality_df = pd.DataFrame(centrality_data_list)
            safe_network_name = network_name.replace(" ", "_").replace("-","_").lower()
            centrality_output_path = os.path.join(OUTPUT_CENTRALITY_DIR, f"{safe_network_name}_centralities.csv")
            try:
                # Pouzit float_format pre konzistentne desatinne miesta pre float stlpce
                centrality_df.to_csv(centrality_output_path, index=False, float_format='%.8g') 
                print(f"  Detailed node data saved to: {centrality_output_path}")
            except Exception as e:
                print(f"  ERROR saving detailed node data for {network_name} to {centrality_output_path}: {e}")
        else:
            print(f"  No detailed node data generated for {network_name}.")

        # Pridanie vypocitanych metrik do suhrnnych vysledkov
        summary_results.append({
            "Network": network_name,
            "Nodes (N)": N,
            "Edges (E)": E,
            "Density": density,
            "Average Degree": avg_degree, # Pridane
            "Assortativity": assortativity, # Pridane
            "Average Clustering Coefficient": avg_clustering, # Pridane
            "Modularity": modularity_score, 
            "Num Communities": num_communities,
        })
        
        end_time = time.time()
        print(f"  Processing time for {network_name}: {end_time - start_time:.2f} seconds")

    except Exception as e:
        print(f"  GENERAL ERROR processing {network_name}: {e}")
        summary_results.append({
             "Network": network_name, 
             "Nodes (N)": 0, # 0 uzlov pri chybe spracovania
             "Edges (E)": 0, # 0 hran
             "Density": np.nan, # Nedefinovane
             "Average Degree": np.nan, # Nedefinovane
             "Assortativity": np.nan, # Nedefinovane
             "Average Clustering Coefficient": np.nan, # Nedefinovane
             "Modularity": np.nan, # Nedefinovane
             "Num Communities": np.nan, # Nedefinovane
             # Mozete pridat aj chybovu spravu ak chcete
             # "Error": str(e)
             })


if summary_results:
    df_summary = pd.DataFrame(summary_results)
    # Aktualizovat poradie stlpcov
    summary_column_order = [
        "Network", "Nodes (N)", "Edges (E)", "Density", 
        "Average Degree", "Assortativity", "Average Clustering Coefficient", # Pridane/aktualizovane
        "Modularity", "Num Communities", 
    ]
    # Preusporiadat stlpce a zabezpecit, ze NaN hodnoty sa spravne zapisu do CSV
    df_summary = df_summary.reindex(columns=summary_column_order) 
    df_summary.replace([np.inf, -np.inf], np.nan, inplace=True) # Nahradit inf hodnoty za NaN, ak by sa niekde objavili

    try:
        # Pouzit float_format pre konzistentne desatinne miesta pre float stlpce
        df_summary.to_csv(OUTPUT_SUMMARY_CSV, index=False, float_format='%.6f') 
        print(f"\nSummary results saved to {OUTPUT_SUMMARY_CSV}")
    except Exception as e:
        print(f"\nERROR saving summary results to {OUTPUT_SUMMARY_CSV}: {e}")
else:
    print("\nNo summary results generated.")

print("\nScript finished.")