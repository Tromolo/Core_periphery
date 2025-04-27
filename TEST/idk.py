import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys
import traceback

# --- Konfigurácia ---
# Cesta k hlavnému adresáru projektu
# !!! Nastavte túto cestu podľa potreby na koreňový adresár Vášho projektu !!!
project_path = '/home/hruby/PycharmProjects/Core_periphery'
if project_path not in sys.path:
    sys.path.append(project_path)

# Cesta k súboru s vlastnosťami nájdenej štruktúry (výstup z final_analysis_script.py)
STRUCTURE_PROPERTIES_CSV = os.path.join(project_path, 'results', 'final_structure_properties.csv')

# Adresár pre uloženie výstupných grafov
OUTPUT_PLOTS_DIR = os.path.join(project_path, 'results', 'structure_plots')
os.makedirs(OUTPUT_PLOTS_DIR, exist_ok=True)

# Definícia kategórií sietí a sietí, ktoré do nich patria
# !!! SKONTROLUJTE, ČI TOTO ZODPOVEDÁ VAŠIM SKUTOČNÝM KATEGÓRIÁM A SIETIAM !!!
network_categories = {
    'Malé (<100 uzlov)': ['Karate Club', 'Dolphins', 'Les Miserables'],
    'Stredné (100-1000 uzlov)': ['Football', 'YeastL'],
    'Veľké (>1000 uzlov)': ['Facebook Combined', 'Power Grid', 'Bianconi-0.7', 'Bianconi-0.97']
}

# Zoznam metrík vlastností štruktúry, pre ktoré chceme vygenerovať grafy
# Názvy MUSIA PRESNE zodpovedať názvom stĺpcov v final_structure_properties.csv
structure_metrics = [
    'core_percentage',
    'core_density',
    'periphery_density',
    'Calculated_Avg_Degree_Core',
    'Calculated_Avg_Degree_Periphery',
    'Core Avg Clustering',
    'Periphery Avg Clustering',
    'Clustering Ratio (C/P)',
    # Pridajte sem ďalšie stĺpce, ak chcete vizualizovať aj Centrality C/P,
    # napr. 'Core Avg Betweenness', 'Periphery Avg Betweenness', 'Betweenness Ratio (C/P)', atd.
]

# Zoznam algoritmov v požadovanom poradí pre grafy
algorithms_order = ['BE', 'Rombach', 'LowRankCore']

# --- Skript ---

print(f"Načítavam vlastnosti nájdenej štruktúry zo súboru: {STRUCTURE_PROPERTIES_CSV}")
try:
    df_structure = pd.read_csv(STRUCTURE_PROPERTIES_CSV)
    print(f"Úspešne načítaných {len(df_structure)} riadkov.")
except FileNotFoundError:
    print(f"CHYBA: Súbor {STRUCTURE_PROPERTIES_CSV} sa nenašiel.")
    exit(1)
except Exception as e:
    print(f"CHYBA pri načítaní súboru {STRUCTURE_PROPERTIES_CSV}: {e}")
    traceback.print_exc()
    exit(1)

# Pridanie stĺpca s kategóriou siete
def assign_category(network_name):
    for category, networks in network_categories.items():
        if network_name in networks:
            return category
    return 'Neznáma' # Pre prípad, že sieť nie je v zozname

df_structure['Network_Category'] = df_structure['Network'].apply(assign_category)

# Odfiltrovať riadky, kde sa nepodarilo priradiť kategóriu (ak nejaké sú)
df_structure = df_structure[df_structure['Network_Category'] != 'Neznáma'].copy()

# Zoskupiť dáta podľa kategórie siete a algoritmu a vypočítať priemery pre metriky
print("\nZoskupujem dáta a počítam priemery...")
averaged_structure_properties = df_structure.groupby(['Network_Category', 'Algorithm'])[structure_metrics].mean().reset_index()

# Zabezpečiť správne poradie kategórií a algoritmov pre grafy
# Zoraďte kategórie v DataFrámoch na základe poradia v network_categories
category_order_list = list(network_categories.keys())
averaged_structure_properties['Network_Category'] = pd.Categorical(averaged_structure_properties['Network_Category'], categories=category_order_list, ordered=True)
averaged_structure_properties.sort_values(by=['Network_Category', 'Algorithm'], inplace=True)

# Vytvorenie a uloženie grafov pre každú metriku
print("\nGenerujem grafy...")

for metric in structure_metrics:
    if metric not in averaged_structure_properties.columns:
        print(f"Upozornenie: Metrika '{metric}' sa nenašla v spriemerovaných dátach. Preskakujem graf.")
        continue

    plt.figure(figsize=(12, 7)) # Nastavenie veľkosti grafu
    
    # Vytvorenie skupinového stĺpcového grafu
    # x='Network_Category' - na X osi sú kategórie sietí
    # y=metric - na Y osi je hodnota metriky
    # hue='Algorithm' - stĺpce sú zoskupené podľa algoritmu
    sns.barplot(
        x='Network_Category',
        y=metric,
        hue='Algorithm',
        data=averaged_structure_properties,
        palette='viridis', # Farebná paleta
        order=category_order_list, # Zabezpečiť poradie kategórií
        hue_order=algorithms_order # Zabezpečiť poradie algoritmov
    )

    # Nastavenie titulkov a popisov osí
    plt.title(f'Priemerná hodnota: {metric.replace("_", " ")} (podľa typu siete a algoritmu)', fontsize=14)
    plt.xlabel('Typ siete', fontsize=12)
    plt.ylabel(metric.replace("_", " "), fontsize=12)

    # Umiestnenie legendy
    plt.legend(title='Algoritmus')

    # Upraviť layout
    plt.tight_layout()

    # Uloženie grafu
    # Názov súboru založený na názve metriky
    safe_metric_name = metric.replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "")
    output_plot_path = os.path.join(OUTPUT_PLOTS_DIR, f'{safe_metric_name}_by_category_and_algorithm.png')

    try:
        plt.savefig(output_plot_path, dpi=300)
        print(f"  Graf pre metriku '{metric}' uložený do: {output_plot_path}")
    except Exception as e:
        print(f"  CHYBA pri ukladaní grafu pre metriku '{metric}': {e}")
        traceback.print_exc()

    plt.close() # Zavrieť graf, aby sa neprekrývali


print("\nGenerovanie grafov vlastností nájdenej štruktúry dokončené.")