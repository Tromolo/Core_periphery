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

# Cesta k súboru s koreláciami (výstup z final_analysis_script.py)
CORRELATIONS_CSV = os.path.join(project_path, 'results', 'final_correlations.csv')

# Cesta a názov výstupného súboru s heatmapou
OUTPUT_HEATMAP_PNG = os.path.join(project_path, 'results', 'correlation_heatmap.png')

# --- Skript ---

print(f"Načítavam korelačné dáta zo súboru: {CORRELATIONS_CSV}")
try:
    df_correlations = pd.read_csv(CORRELATIONS_CSV)
    print(f"Úspešne načítaných {len(df_correlations)} riadkov korelácií.")
except FileNotFoundError:
    print(f"CHYBA: Súbor {CORRELATIONS_CSV} sa nenašiel.")
    #sys.exit(1) # Nezastavujeme skript pri chybe nacitania, len hlasime problem
    exit(1) # Pouzijeme exit() namiesto sys.exit()

except Exception as e:
    print(f"CHYBA pri načítaní súboru {CORRELATIONS_CSV}: {e}")
    traceback.print_exc()
    #sys.exit(1)
    exit(1)

# Skontrolujeme, či má DataFrame očakávaný formát
expected_cols = ['Network Property', 'Algorithm', 'Algorithm Metric', 'Correlation (r)']
if not all(col in df_correlations.columns for col in expected_cols):
    missing = [col for col in expected_cols if col not in df_correlations.columns]
    print(f"CHYBA: Súbor s koreláciami nemá očakávané stĺpce. Chýbajúce: {missing}")
    print(f"Nájdené stĺpce: {list(df_correlations.columns)}")
    #sys.exit(1)
    exit(1)


print("Pripravujem dáta pre heatmapu (pivotovanie)...")

try:
    # Pivotujeme DataFrame do formátu pre heatmapu
    # Index: Network Property
    # Stĺpce: Multi-level (Algorithm, Algorithm Metric)
    # Hodnoty: Correlation (r)
    heatmap_data = df_correlations.pivot_table(
        index='Network Property',
        columns=['Algorithm', 'Algorithm Metric'],
        values='Correlation (r)'
    )
    print("  Dáta úspešne pivotované.")

    # Voliteľné: Zoradiť metriky algoritmov pre lepší prehľad (napr. Runtime, Pattern Match, Core Size, ...)
    # Toto si mozno budete musiet upravit podla toho, v akom poradi chcete mat metriky v Heatmape
    # Definuje PORADIE metrík (kratšie názvy, ako sú v stĺpci 'Algorithm Metric')
    metric_order = [
        'runtime',
        'ideal_pattern_match',
        'core_percentage',
        'core_size', # Pridane, ak je vo vasich datach
        'periphery_size', # Pridane
        'core_density',
        'periphery_density',
        'core_periphery_ratio',
        # Ak ste zahrnuli korelácie Calculated_Avg_Degree_Core/Periphery alebo Clustering C/P
        # a chcete ich sem pridat, MUSIA mat presne nazvy ako su v stlpci 'Algorithm Metric'
        # Napr: 'Calculated_Avg_Degree_Core', 'Core Avg Clustering' atd.
        # Ak nie su, ignoruju sa.
        # Pridajte ich sem do zoznamu v pozadovanom poradi:
        'Calculated_Avg_Degree_Core', # Pridajte ak je v datach a chcete zobrazit
        'Calculated_Avg_Degree_Periphery', # Pridajte ak je v datach a chcete zobrazit
        'Core Avg Clustering', # Pridajte ak je v datach a chcete zobrazit
        'Periphery Avg Clustering', # Pridajte ak je v datach a chcete zobrazit
        'Clustering Ratio (C/P)', # Pridajte ak je v datach a chcete zobrazit
    ]
    
    # Získajte existujúce multi-level stĺpce po pivotovaní
    existing_cols_multiindex = list(heatmap_data.columns)
    
    # Vytvorte nový zoznam multi-level stĺpcov v požadovanom poradí
    ordered_cols_multiindex = []
    
    # Ziskajte unikatne nazvy algoritmov a zoradte ich (volitelne)
    algorithm_names = sorted(df_correlations['Algorithm'].unique())

    for algo in algorithm_names:
        # Ziskajte multi-level stlpce pre aktualny algoritmus
        cols_for_current_algo = [(alg, metric) for alg, metric in existing_cols_multiindex if alg == algo]
        
        # Zoradte tieto stlpce podla naseho definovaneho poradia metrik
        # Pouzijeme key, ktory vrati index metriky v metric_order, alebo velke cislo ak metrika nie je v zozname (aby boli nezaradene na konci)
        sorted_cols_for_current_algo = sorted(
            cols_for_current_algo,
            key=lambda x: metric_order.index(x[1]) if x[1] in metric_order else len(metric_order)
        )
        ordered_cols_multiindex.extend(sorted_cols_for_current_algo)

    # Ak niektoré stĺpce zostali (neboli v algorithm_names alebo v metric_order), pridajte ich na koniec (len ako poistka)
    remaining_cols_multiindex = [col for col in existing_cols_multiindex if col not in ordered_cols_multiindex]
    ordered_cols_multiindex.extend(remaining_cols_multiindex)
    
    # Preusporiadať stĺpce v heatmap_data
    heatmap_data = heatmap_data[ordered_cols_multiindex]

    # Voliteľné: Preusporiadať riadky (Network Property) ak chcete mať určité vlastnosti na začiatku
    # Napr. network_property_order = ['Nodes (N)', 'Edges (E)', 'Density', ...]
    # heatmap_data = heatmap_data.reindex(index=network_property_order)

except Exception as e:
    print(f"CHYBA pri príprave dát pre heatmapu: {e}")
    traceback.print_exc()
    #sys.exit(1)
    exit(1)


print("Generujem heatmapu...")

# Nastavenie VEĽKEJ veľkosti obrázku pre lepšiu čitateľnosť
# Tieto hodnoty (šírka, výška) môžete ďalej upravovať, ak to stále nebude dobre vidno
fig_width = 35 # Zvýšenie šírky (pre 33+ stĺpcov to bude mozno chciet este viac)
fig_height = 12 # Výšku môžete upraviť, ak sú riadky príliš blízko

plt.figure(figsize=(fig_width, fig_height))

# Nastavenie veľkosti písma pre anotácie vo vnútri heatmapy
annot_font_size = 7 # Možno bude potrebné ešte menšie písmo (napr. 6 alebo 5)

# Vytvorenie heatmapy
# annot=True zobrazi hodnoty v bunkach (mozete vypnut ak je prilis vela cisiel)
# cmap='coolwarm' je vhodny pre korelácie (modra=pozitivna, cervena=negativna, biela=blizko 0)
# center=0 zabezpeci, ze biela farba bude pri korelacii 0
sns.heatmap(
    heatmap_data,
    annot=True, # Zobraziť hodnoty
    fmt=".2f",  # Formátovanie na 2 desatinne miesta
    cmap='coolwarm', # Farby
    center=0,   # Stred farieb pri 0
    linewidths=.5, # Medzi bunkami
    cbar_kws={'label': 'Pearsonova korelácia (r)'}, # Popis legendy
    annot_kws={"size": annot_font_size} # Nastavenie veľkosti písma pre anotácie
)

# Nastavenie titulkov a popisov osi
plt.title('Heatmapa korelácií medzi vlastnosťami sietí a metrikami algoritmov', fontsize=16) # Väčší titulok
plt.xlabel('Algoritmus a Metrika', fontsize=14) # Väčší popis osi
plt.ylabel('Vlastnosť siete', fontsize=14) # Väčší popis osi

# Rotácia popisov osi x o 90 stupňov a menšie písmo
# Zmeníme rotáciu na 90 stupňov (vertikálne) a prípadne zmenšíme písmo ešte viac
# Pouzijeme 'center' pre ha (horizontalalignment) aby bolo text centrovaný pod tick markom
plt.xticks(rotation=90, ha='center', fontsize=8) # Rotácia 90, menšie písmo, zarovnanie 'center'
plt.yticks(rotation=0, fontsize=10) # Písmo na Y osi môže zostať 10 alebo upraviť

# Upraviť layout tak, aby sa titulky neprekrývali (veľmi dôležité!)
# Túto funkciu volať AŽ PO nastavení titulkov, popisiek a rotácie/veľkosti písma
plt.tight_layout()


# Uloženie grafu
# Najprv vytvoríme adresár, ak neexistuje
output_dir = os.path.dirname(OUTPUT_HEATMAP_PNG)
if output_dir and not os.path.exists(output_dir):
    os.makedirs(output_dir)
    print(f"Vytvorený adresár: {output_dir}")

try:
    # Zvýšime DPI (rozlíšenie) pre ostrejší obrázok pri väčších rozmeroch
    plt.savefig(OUTPUT_HEATMAP_PNG, dpi=400)
    print(f"Heatmapa uložená do: {OUTPUT_HEATMAP_PNG}")
except Exception as e:
    print(f"CHYBA pri ukladaní heatmapy do {OUTPUT_HEATMAP_PNG}: {e}")
    traceback.print_exc()


# Zobrazenie grafu (voliteľné, ak spúšťate v prostredí s GUI ako Jupyter alebo Spyder)
# plt.show()

print("\nGenerovanie heatmapy dokončené.")