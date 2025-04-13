# Core-Periphery Network Analysis Tool

Tento projekt poskytuje webové rozhranie na analýzu a vizualizáciu core-periphery štruktúr v sieťach. Obsahuje backend postavený na FastAPI a frontend vytvorený pomocou Reactu.

## Požiadavky

Pred spustením projektu sa uistite, že máte nainštalované:

*   **Python:** Verzia 3.12+ (Overte pomocou `python3 --version`)
*   **Node.js:** Verzia 18.x+ (Overte pomocou `node --version`)
*   **npm:** (Inštaluje sa spolu s Node.js, overte pomocou `npm --version`)
*   **Git:** Na klonovanie repozitára.

## Lokálne nastavenie a spustenie

Nasledujte tieto kroky na nastavenie a spustenie aplikácie na vašom lokálnom počítači:

1.  **Klonujte repozitár:**
    ```bash
    git clone <URL_VÁŠHO_REPOZITÁRA> # Nahraďte URL adresou vášho GitHub repozitára
    cd Core_periphery # Alebo názov adresára, kam ste klonovali
    ```

2.  **Nastavte Python virtuálne prostredie (odporúčané):**
    ```bash
    python3 -m venv .venv  # Vytvorí adresár .venv
    source .venv/bin/activate # Aktivácia na Linux/macOS
    # Pre Windows použite: .venv\Scripts\activate
    ```

3.  **Nainštalujte backend závislosti:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Nainštalujte frontend závislosti:**
    ```bash
    cd frontend
    npm install # Alebo npm ci, ak preferujete použiť package-lock.json
    cd .. # Vráťte sa späť do koreňového adresára projektu
    ```

5.  **Spustite Backend Server:**
    *   Otvorte **prvý** terminál (s aktívnym virtuálnym prostredím `.venv`).
    *   Spustite FastAPI server:
        ```bash
        python -m backend.main
        ```
    *   Backend by mal bežať na `http://localhost:8080`.

6.  **Spustite Frontend Development Server:**
    *   Otvorte **druhý** terminál.
    *   Prejdite do adresára `frontend`:
        ```bash
        cd frontend
        ```
    *   Spustite React development server:
        ```bash
        npm start
        ```
    *   Frontend by sa mal automaticky otvoriť v prehliadači na `http://localhost:3000` (alebo inom porte, ak je 3000 obsadený). Aplikácia bude komunikovať s backendom na porte 8080.

Teraz by ste mali mať plne funkčnú aplikáciu bežiacu lokálne. Backend je na porte 8080 a frontend na porte 3000.
