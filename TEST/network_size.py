import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns

# Predpokladáme, že máme dáta o kvalite detekcie pre rôzne veľkosti sietí
# Tieto hodnoty sú ilustratívne, nahraďte ich skutočnými hodnotami
network_sizes = [34, 62, 77, 115, 500, 1000]
be_quality = [79.5, 75.2, 72.1, 68.5, 60.2, 55.8]
rombach_quality = [82.2, 78.5, 75.3, 70.1, 65.3, 62.1]
cucuringu_quality = [82.2, 76.8, 73.5, 69.2, 67.5, 65.2]

# Vytvorenie grafu
plt.figure(figsize=(12, 7))

# Grafy kvality detekcie
plt.plot(network_sizes, be_quality, 'o-', linewidth=2, markersize=8, label='BE')
plt.plot(network_sizes, rombach_quality, 's-', linewidth=2, markersize=8, label='Rombach')
plt.plot(network_sizes, cucuringu_quality, '^-', linewidth=2, markersize=8, label='Cucuringu')

# Nastavenie osí a popisov
plt.title('Vplyv veľkosti siete na kvalitu detekcie core-periphery štruktúr', fontsize=14)
plt.xlabel('Počet uzlov v sieti', fontsize=12)
plt.ylabel('Pattern Match (%)', fontsize=12)
plt.legend(fontsize=10)

# Logaritmická škála pre os X
plt.xscale('log')
plt.grid(True, which="both", linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('network_size_quality.png', dpi=300)
plt.close()