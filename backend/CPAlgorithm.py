from abc import ABCMeta, abstractmethod
import numpy as np
from . import utils

class CPAlgorithm(metaclass=ABCMeta):
    """
    Abstraktná základná trieda pre algoritmy detekcie Core-Periphery štruktúr.
    """
    def __init__(self):
        """
        Inicializátor triedy. Pripravuje prázdne zoznamy pre uloženie výsledkov.
        """
        self.x_ = [] # hodnoty "coreness" pre každý uzol (výstup Rombach).
        self.c_ = [] # binárne priradenie uzlov (0=periféria, 1=jadro).
        self.Q_ = [] # celkovú kvalitu (skóre) detekovanej štruktúry.
        self.qs_ = [] # skóre kvality pre jednotlivé behy (ak algoritmus beží viackrát).

    @abstractmethod
    def detect(self):
        """
        Abstraktná metóda pre spustenie detekcie core-periphery štruktúry.
        """
        pass

    @abstractmethod
    def _score(self, A, c, x):
        """
        Abstraktná metóda pre výpočet skóre (kvality) danej core-periphery štruktúry.
        """
        pass

    def pairing(self, labels, a):
        """
        Pomocná metóda na vytvorenie slovníka z označení uzlov a poľa hodnôt.
        """
        return dict(zip(labels, a))

    def depairing(self, labels, d):
        """
        Pomocná metóda na konverziu slovníka (označenie -> hodnota) späť na pole NumPy,
        zoradené podľa poradia označení v `labels`.
        """
        return np.array([d[x] for x in labels])

    def get_pair_id(self):
        """
        Vráti finálne priradenie uzlov (core/periphery) ako slovník.
        """
        return self.pairing(self.nodelabel, self.c_)

    def get_coreness(self):
        """
        Vráti vypočítané hodnoty coreness pre každý uzol ako slovník.
        """
        return self.pairing(self.nodelabel, self.x_)

    def score(self, G, c, x):
        """
        Vypočíta a vráti skóre kvality pre zadanú CP štruktúru na grafe G.
        """
        A, nodelabel = utils.to_adjacency_matrix(G)
        c_array = self.depairing(nodelabel, c)
        x_array = self.depairing(nodelabel, x)
        return self._score(A, c_array, x_array)