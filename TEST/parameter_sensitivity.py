import os
import time
import itertools
import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
import json
from pathlib import Path
import sys
import math
import uuid
import shutil
from typing import List, Dict, Any, Tuple, Iterator, Optional, Callable

# Set up paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RESULTS_DIR = os.path.join(BASE_DIR, "TEST", "results", "parameter_sensitivity_rerun")
os.makedirs(RESULTS_DIR, exist_ok=True)
OUTPUT_CSV = os.path.join(RESULTS_DIR, "parameter_sensitivity_results_rerun.csv")

results_list = []
algorithms_to_run = ['BE', 'Rombach', 'Cucuringu']
# Import core-periphery algorithms
sys.path.append(BASE_DIR)
try:
    from backend.functions import get_algorithm_function
    from backend.functions import get_core_stats
    print("Successfully imported backend functions.")
except ImportError as import_error:
    print(f"Error importing backend functions: {import_error}")
    print("Please ensure 'backend.functions' module exists and contains 'get_algorithm_function' and 'get_core_stats'.")
    print("Exiting.")
    sys.exit(1)
except Exception as e:
    print(f"An unexpected error occurred during import: {e}")
    sys.exit(1)

# Define small networks
SMALL_NETWORKS = [
    {"name": "Karate Club", "path": os.path.join(DATA_DIR, "male_site", "karate.gml"), "format": "gml"},
    {"name": "Dolphins", "path": os.path.join(DATA_DIR, "male_site", "dolphins.gml"), "format": "gml"},
    {"name": "Les Miserables", "path": os.path.join(DATA_DIR, "male_site", "lesmis.gml"), "format": "gml"},
    {"name": "Football", "path": os.path.join(DATA_DIR, "male_site", "football.gml"), "format": "gml"},
    {"name": "Facebook Combined", "path": os.path.join(DATA_DIR, "male_site", "facebook_combined.csv"), "format": "csv", "delimiter": " "},
    {"name": "Power Grid", "path": os.path.join(DATA_DIR, "male_site", "USpowergrid_n4941.csv"), "format": "csv", "delimiter": " "},
    {"name": "Bianconi-0.7", "path": os.path.join(DATA_DIR, "site_pro_modely", "Bianconi-Triadic-Closure 0.7 3.csv"), "format": "csv", "delimiter": ","},
    {"name": "Bianconi-0.97", "path": os.path.join(DATA_DIR, "site_pro_modely", "Bianconi-Triadic-Closure 0.97 3.csv"), "format": "csv", "delimiter": ","}
]

# Define parameter grids
BE_PARAMS = {"num_runs": [5, 10, 20, 50]}
ROMBACH_PARAMS = {
    "alpha": [0.1, 0.3, 0.5, 0.7, 0.9],
    "beta": [0.1, 0.3, 0.5, 0.7, 0.9],
    "num_runs": [5, 10, 20]
}
CUCURINGU_PARAMS = {"beta": [0.1, 0.3, 0.5, 0.7, 0.9]}

def load_network_from_path(network_info: dict) -> Optional[nx.Graph]:
    """Loads a network graph from a file path, adapted from backend logic."""
    path = network_info["path"]
    network_name = network_info["name"] # For specific fallbacks like Karate

    if not os.path.exists(path):
        print(f"    ERROR: Network file not found: {path}")
        return None

    # Infer extension if format not explicitly given
    ext = network_info.get("format")
    if not ext:
        try:
            ext = path.split(".")[-1].lower()
        except IndexError:
            print(f"    ERROR: Could not determine file extension for {path}")
            return None

    print(f"  Attempting to load network '{network_name}' from: {path} (format: {ext})")
    G = None
    try:
        if ext == "gml":
            try:
                G = nx.read_gml(path)
                print("    Successfully loaded GML file (standard).")
            except Exception as gml_error:
                print(f"    Standard GML loading failed: {str(gml_error)}")
                try:
                    G = nx.read_gml(path, label=None)
                    print("    Successfully loaded GML file (label=None).")
                except Exception as gml_error2:
                    print(f"    GML loading with label=None failed: {str(gml_error2)}")
                    try:
                        G = nx.read_gml(path, label='id')
                        print("    Successfully loaded GML file (label='id').")
                    except Exception as gml_error3:
                        print(f"    GML loading with label=id failed: {str(gml_error3)}")
                        # Add other label attempts if needed (e.g., 'name')

                        # Specific fallback for Karate Club
                        if 'karate' in network_name.lower():
                            try:
                                print("    Attempting to load built-in karate club graph...")
                                G = nx.karate_club_graph()
                                print("    Successfully loaded built-in karate club network.")
                            except Exception as karate_error:
                                print(f"    Built-in karate club loading failed: {str(karate_error)}")
                                print(f"    ERROR: Could not load GML or fallback for {network_name}.")
                                return None # Failed to load karate
                        else:
                            print(f"    ERROR: Failed to load GML file '{path}' with multiple methods.")
                            return None # Failed to load other GML

        elif ext in ["csv", "txt", "tsv", "dat", "edgelist"]: # Treat all as potential edge lists
            # Try specified delimiter first
            specified_delimiter = network_info.get("delimiter")
            delimiters_to_try = []
            if specified_delimiter:
                delimiters_to_try.append(specified_delimiter)
            # Add common delimiters if specified one fails or none was given
            common_delimiters = [d for d in [',', '\t', ' ', ';'] if d != specified_delimiter]
            delimiters_to_try.extend(common_delimiters)

            loaded_successfully = False
            last_error = None
            df = None

            for sep in delimiters_to_try:
                print(f"      Trying delimiter: '{repr(sep)}'")
                try:
                    # Attempt to read with header detection
                    df_header = pd.read_csv(path, sep=sep, encoding='utf-8', engine='python',
                                            comment='#', skipinitialspace=True, nrows=5) # Read a few rows to check header

                    # Simple header check: are column names mostly non-numeric?
                    # (More robust checks could be added)
                    header_row = 0 if all(isinstance(col, str) and not col.replace('.', '', 1).isdigit() for col in df_header.columns) else None

                    # Read the full file
                    df = pd.read_csv(path, sep=sep, header=header_row, encoding='utf-8', engine='python',
                                     comment='#', skipinitialspace=True, on_bad_lines='warn', dtype=str) # Read all as string initially

                    if df.shape[1] >= 2:
                        # Assume first two columns are source/target
                        df = df.iloc[:, :2]
                        df.columns = ['source', 'target'] # Rename columns
                        df.dropna(inplace=True) # Drop rows with missing source/target

                        if not df.empty:
                            # Convert node IDs back if needed, but string is safest
                            # df['source'] = pd.to_numeric(df['source'], errors='ignore')
                            # df['target'] = pd.to_numeric(df['target'], errors='ignore')

                            G = nx.from_pandas_edgelist(df, source='source', target='target', create_using=nx.Graph())
                            print(f"    Successfully loaded edgelist with delimiter '{repr(sep)}'.")
                            loaded_successfully = True
                            break # Stop trying delimiters
                        else:
                            print(f"      Warning: Edgelist file '{path}' with delimiter '{repr(sep)}' resulted in empty dataframe after dropna.")
                            last_error = f"Empty dataframe with delimiter '{repr(sep)}'"
                    else:
                        last_error = f"Less than 2 columns found with delimiter '{repr(sep)}'"
                        continue # Try next delimiter

                except pd.errors.ParserError as e_parse:
                    last_error = f"ParserError with delimiter '{repr(sep)}': {e_parse}"
                    continue # Try next delimiter
                except Exception as e_csv:
                    print(f"      Warning: Error reading edgelist '{path}' with delimiter '{repr(sep)}': {e_csv}")
                    last_error = f"Exception with delimiter '{repr(sep)}': {e_csv}"
                    continue # Try next delimiter

            if not loaded_successfully:
                print(f"    ERROR: Failed to load edgelist file '{path}' with any tried delimiter.")
                if last_error:
                    print(f"      Last attempt info: {last_error}")
                return None

        # Add other format handlers here if needed (GraphML, GEXF, Pajek)
        # elif ext == "graphml":
        #     G = nx.read_graphml(path)
        # elif ext == "gexf":
        #     G = nx.read_gexf(path)
        # elif ext == "pajek" or ext == "net":
        #     G = nx.read_pajek(path)

        else:
            print(f"    ERROR: Unsupported file format '{ext}' for network '{network_name}'.")
            return None

        # --- Final Graph Check ---
        if G is None:
             print(f"    ERROR: Graph object is None after attempting to load '{path}'.")
             return None
        if G.number_of_nodes() == 0:
            print(f"    Warning: Graph loaded from '{path}' has 0 nodes.")
            # Allow empty graphs for now, could return None if they are invalid
        elif G.number_of_edges() == 0:
             print(f"    Warning: Graph loaded from '{path}' has 0 edges.")

        print(f"    Successfully loaded graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges.")
        return G

    except Exception as e:
        print(f"    ERROR: Unexpected error during loading of '{path}': {e}")
        import traceback
        print(traceback.format_exc()) # Print full traceback for unexpected errors
        return None

def generate_param_combinations(algorithm_name: str) -> Iterator[Dict[str, Any]]:
    """Generates parameter combinations for a given algorithm."""
    if algorithm_name == "BE":
        param_grid = BE_PARAMS
    elif algorithm_name == "Rombach":
        param_grid = ROMBACH_PARAMS
    elif algorithm_name == "Cucuringu":
        param_grid = CUCURINGU_PARAMS
    else:
        print(f"Warning: Unknown algorithm '{algorithm_name}' for parameter generation. Returning empty.")
        return iter([]) # Vráť prázdny iterátor

    keys = param_grid.keys()
    values = param_grid.values()
    for instance in itertools.product(*values):
        yield dict(zip(keys, instance))

def run_algorithm(algorithm_name: str, G: nx.Graph, params: Dict[str, Any]) -> Optional[Dict]:
    """Runs the specified algorithm with error handling."""
    try:
        algo_func = get_algorithm_function(algorithm_name)
        if algo_func is None:
            print(f"    ERROR: Could not retrieve function for algorithm '{algorithm_name}'.")
            return None
        
        # Run the algorithm, expecting three return values
        classifications, coreness, stats = algo_func(G, **params)

        if classifications is None:
             print(f"    WARNING: Algorithm '{algorithm_name}' returned None for classifications.")
             return None

        # No longer extract core/periphery here, return the raw classifications dict
        # core_nodes = [node for node, label in classifications.items() if label == 'C']
        # periphery_nodes = [node for node, label in classifications.items() if label == 'P']

        # print(f"      Finished {algorithm_name}. Core size derived later from classifications.") 
        return classifications # Return the dictionary
    
    except ValueError as ve:
         # Handle the specific case where the backend function might still return only 2 values (if it errored internally before returning 3)
         # Or if the unpacking failed for other reasons.
         print(f"    ERROR: Algorithm '{algorithm_name}' failed during execution or return value unpacking with params {params} on network.")
         print(f"      ValueError details: {ve}")
         # import traceback
         # print(traceback.format_exc())
         return None
    except Exception as e:
        print(f"    ERROR: Algorithm '{algorithm_name}' failed with params {params} on network.")
        print(f"      General Error details: {e}")
        # import traceback
        # print(traceback.format_exc())
        return None

def calculate_metrics(G: nx.Graph, classifications: Optional[Dict]) -> Optional[Dict[str, Any]]:
    """Calculates metrics using the backend function with error handling."""
    # Check if classifications dictionary is None or empty
    if classifications is None or not classifications:
        print("    Skipping metrics calculation due to missing or empty classifications.")
        return None
    try:
        # print("      Calculating metrics...") # Uncomment for detailed logging
        # Pass the classifications dict directly to get_core_stats
        metrics = get_core_stats(G, classifications)
        # print("      Metrics calculated.") # Uncomment
        return metrics
    except Exception as e:
        print(f"    ERROR: Metrics calculation failed.")
        # Error message no longer needs core/periphery size as it's not directly available here
        print(f"      Error details: {e}")
        # import traceback
        # print(traceback.format_exc())
        return None

def calculate_metrics_for_csv(raw_metrics: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Formats metrics for CSV, adding 'metrics.' prefix and handling missing keys."""
    formatted_metrics = {}
    # Očakávané kľúče v CSV (bez prefixu 'metrics.')
    expected_metric_keys_in_csv = [
        "core_size", "periphery_size", "core_percentage",
        "core_density", "core_density_interpretation",
        "periphery_core_connectivity", "periphery_isolation",
        "core_periphery_ratio", "cp_ratio_interpretation",
        "connection_patterns", "ideal_pattern_match",
        "pattern_match_interpretation", "structure_quality",
        "avg_core_coreness", "avg_periphery_coreness",
        "coreness_std"
    ]
    if raw_metrics:
        for key, value in raw_metrics.items():
            formatted_metrics[f"metrics.{key}"] = value

    # Ensure all expected columns exist, fill with NaN if missing
    for key_without_prefix in expected_metric_keys_in_csv:
        full_key = f"metrics.{key_without_prefix}"
        if full_key not in formatted_metrics:
            formatted_metrics[full_key] = math.nan

    return formatted_metrics

def generate_summary_report(all_results: List[Dict[str, Any]], output_dir: str):
    """Generates a summary report of the analysis."""
    report_path = os.path.join(output_dir, "summary_report.txt")
    print(f"\nGenerating summary report: {report_path}")

    if not all_results:
        print("  WARNING: No results were generated. Cannot create summary report.")
        with open(report_path, "w", encoding='utf-8') as f:
            f.write("Parameter sensitivity analysis ran, but no results were generated.\n")
            f.write("This likely indicates issues loading network files or errors during algorithm execution.\n")
            f.write(f"Please check the console output and the existence/paths of network files in DATA_DIR: {DATA_DIR}\n")
        return # Exit the function early

    try:
        df = pd.DataFrame(all_results)

        # Ensure required columns exist before proceeding
        required_cols = ['network', 'algorithm', 'runtime', 'metrics.ideal_pattern_match']
        if not all(col in df.columns for col in required_cols):
             print(f"  ERROR: DataFrame is missing one or more required columns for summary: {required_cols}")
             print(f"  Available columns: {df.columns.tolist()}")
             # Optionally write this error to the report file as well
             with open(report_path, "w", encoding='utf-8') as f:
                 f.write(f"Error generating summary: DataFrame missing required columns.\n")
                 f.write(f"Required: {required_cols}\n")
                 f.write(f"Available: {df.columns.tolist()}\n")
             return


        with open(report_path, "w", encoding='utf-8') as f:
            f.write("===== Parameter Sensitivity Analysis Summary =====\n\n")
            f.write(f"- Total runs executed: {len(df)}\n")
            f.write(f"- Networks analyzed: {df['network'].nunique()} ({', '.join(df['network'].unique())})\n")
            f.write(f"- Algorithms tested: {df['algorithm'].nunique()} ({', '.join(df['algorithm'].unique())})\n")
            f.write(f"- Average runtime per run: {df['runtime'].mean():.4f} seconds\n")
            f.write(f"- Total execution time (estimated): {df['runtime'].sum():.2f} seconds\n\n")

            f.write("--- Performance Highlights ---\n")
            # Check if ideal_pattern_match column exists and has non-NA values
            metric_col = 'metrics.ideal_pattern_match'
            if metric_col in df.columns and df[metric_col].notna().any():
                best_match_idx = df[metric_col].idxmax() # This might raise FutureWarning if all are NA, but we checked notna().any()
                if pd.notna(best_match_idx): # Check if idxmax itself returned NaN
                   best_match = df.loc[best_match_idx]
                   f.write(f"- Best Ideal Pattern Match: {best_match[metric_col]:.4f}\n")
                   f.write(f"  (Network: {best_match['network']}, Algorithm: {best_match['algorithm']}, Params: { {k.split('.')[-1]: v for k, v in best_match.items() if k.startswith('parameters.')} })\n")
                else:
                   f.write("- Best Ideal Pattern Match: N/A (Index calculation failed)\n")
            else:
                f.write("- Best Ideal Pattern Match: N/A (No valid results)\n")


            # Check runtime column
            runtime_col = 'runtime'
            if runtime_col in df.columns and df[runtime_col].notna().any():
                fastest_run_idx = df[runtime_col].idxmin()
                if pd.notna(fastest_run_idx):
                    fastest_run = df.loc[fastest_run_idx]
                    f.write(f"- Fastest Run: {fastest_run[runtime_col]:.6f} seconds\n")
                    f.write(f"  (Network: {fastest_run['network']}, Algorithm: {fastest_run['algorithm']}, Params: { {k.split('.')[-1]: v for k, v in fastest_run.items() if k.startswith('parameters.')} })\n\n")
                else:
                    f.write("- Fastest Run: N/A (Index calculation failed)\n\n")
            else:
                 f.write("- Fastest Run: N/A (No valid results)\n\n")


            f.write("--- Results per Algorithm ---\n")
            if 'algorithm' in df.columns:
                for algo, group in df.groupby('algorithm'):
                    f.write(f"\nAlgorithm: {algo}\n")
                    f.write(f"  - Runs Attempted: {len(group)}\n") # Changed label slightly
                    # Calculate stats only if columns exist and have data
                    if runtime_col in group.columns and group[runtime_col].notna().any():
                         f.write(f"  - Avg. Runtime: {group[runtime_col].mean():.4f} s\n")
                    else:
                         f.write(f"  - Avg. Runtime: N/A\n")
                    if metric_col in group.columns and group[metric_col].notna().any():
                         f.write(f"  - Avg. Ideal Pattern Match: {group[metric_col].mean():.4f}\n")
                    else:
                         f.write(f"  - Avg. Ideal Pattern Match: N/A\n")
            else:
                f.write("No algorithm data found to group.\n")

        print("Summary report generated successfully.")
    except KeyError as e:
        print(f"  ERROR generating summary report: Missing key {e}. DataFrame columns might be incomplete.")
        print(f"  Available columns: {df.columns.tolist() if 'df' in locals() else 'DataFrame not created'}")
        # Write error to file
        with open(report_path, "w", encoding='utf-8') as f:
            f.write(f"Error generating summary report: Missing key {e}.\n")
            f.write(f"Available columns: {df.columns.tolist() if 'df' in locals() else 'DataFrame not created'}\n")
    except Exception as e:
        print(f"  ERROR generating summary report: {e}")
        # Write error to file
        with open(report_path, "w", encoding='utf-8') as f:
            f.write(f"An unexpected error occurred during summary report generation: {e}\n")

def analyze_small_networks():
    """Run parameter sensitivity analysis for small networks"""
    # Create visualization directories
    viz_dir = os.path.join(RESULTS_DIR, "visualizations")
    os.makedirs(viz_dir, exist_ok=True)
    # Removed creation of sub-directory as visualization is commented out
    # os.makedirs(os.path.join(viz_dir, "network_visualizations"), exist_ok=True)

    # Store all results
    all_results = [] # Ensure it's initialized here

    # Check if DATA_DIR exists before starting
    if not os.path.isdir(DATA_DIR):
        print(f"CRITICAL ERROR: Data directory not found at the expected path: {DATA_DIR}")
        print("Please ensure the 'data' directory exists in the project root and contains the network files.")
        # Generate an empty summary indicating the issue
        generate_summary_report([], RESULTS_DIR)
        return # Stop execution if data directory is missing

    for network_info in tqdm(SMALL_NETWORKS, desc="Processing Networks"):
        # Load the network
        graph = load_network_from_path(network_info)
        if graph is None:
            print(f"  Skipping network {network_info['name']} due to loading error.")
            continue

        network_name = network_info["name"]
        print(f"\nAnalyzing {network_name}...")

        # Define algorithms and their parameter grids directly here or load from constants
        algorithms = [
            ("BE", BE_PARAMS),
            ("Rombach", ROMBACH_PARAMS),
            ("Cucuringu", CUCURINGU_PARAMS)
        ]

        # Define names of networks considered too large for BE
        large_networks_for_be = {"Facebook Combined", "Power Grid", "Bianconi-0.7", "Bianconi-0.97"}

        for algo_name, params_grid in algorithms:
            # --- Add check to skip BE for large networks ---
            if algo_name == "BE" and network_name in large_networks_for_be:
                print(f"  Skipping BE algorithm for large network: {network_name}")
                continue # Skip to the next algorithm
            # --- End check ---
            
            print(f"  Running {algo_name} algorithm...")
            
            # Use the helper function to generate combinations
            param_combinations = list(generate_param_combinations(algo_name))
            if not param_combinations:
                 print(f"    No parameters defined for {algo_name}, skipping.")
                 continue

            for params in tqdm(param_combinations, desc=f"  {algo_name} parameters", leave=False):
                # Run the algorithm using the helper function
                start_time = time.time()
                # run_algorithm now returns the classifications dictionary
                classifications = run_algorithm(algo_name, graph, params)
                runtime = time.time() - start_time

                # Pass classifications dictionary directly to calculate_metrics
                raw_metrics = calculate_metrics(graph, classifications)

                # Format metrics for CSV/DataFrame (handles None from calculate_metrics)
                metrics_for_csv = calculate_metrics_for_csv(raw_metrics)

                # Store the results in a flat structure
                flat_result = {
                    "network": network_name,
                    "algorithm": algo_name,
                    "runtime": runtime
                }

                # Add parameters with prefix
                for param_key, param_value in params.items():
                    flat_result[f"parameters.{param_key}"] = param_value

                # Add metrics (already have prefix from calculate_metrics_for_csv)
                flat_result.update(metrics_for_csv)

                all_results.append(flat_result)

                # Visualize the core-periphery structure (Commented out)
                # if graph.number_of_nodes() < 100:
                #    visualize_cp_structure(...)

    # Save all results as CSV
    if all_results:
        try:
            results_df = pd.DataFrame(all_results)
            # Define column order again for saving, ensuring consistency
            column_order = [
                "network", "algorithm", "runtime",
                "parameters.num_runs", "parameters.alpha", "parameters.beta",
                "metrics.core_size", "metrics.periphery_size", "metrics.core_percentage",
                "metrics.core_density", "metrics.core_density_interpretation",
                "metrics.periphery_core_connectivity", "metrics.periphery_isolation",
                "metrics.core_periphery_ratio", "metrics.cp_ratio_interpretation",
                "metrics.connection_patterns", "metrics.ideal_pattern_match",
                "metrics.pattern_match_interpretation", "metrics.structure_quality",
                "metrics.avg_core_coreness", "metrics.avg_periphery_coreness",
                "metrics.coreness_std"
            ]
            # Reindex to ensure all columns exist and are in order
            results_df = results_df.reindex(columns=column_order)
            results_df.to_csv(OUTPUT_CSV, index=False, float_format='%.8f', encoding='utf-8')
            print(f"\nResults saved successfully to {OUTPUT_CSV}")
        except Exception as e:
            print(f"\nERROR saving results to CSV: {e}")
    else:
        print("\nNo results were generated to save to CSV.")


    # Generate parameter sensitivity plots (Commented out)
    # plot_parameter_sensitivity(all_results, viz_dir)

    # Generate algorithm comparison plots (Commented out)
    # plot_algorithm_comparison(all_results, viz_dir)

    # Generate summary report (Now handles empty results)
    generate_summary_report(all_results, RESULTS_DIR)

if __name__ == "__main__":
    # Check DATA_DIR early
    if not os.path.isdir(DATA_DIR):
         print(f"CRITICAL ERROR: Data directory not found at the expected path: {DATA_DIR}")
         print("Please ensure the 'data' directory exists in the project root relative to the script location.")
         print("Script cannot proceed.")
    else:
         print(f"Data directory found: {DATA_DIR}")
         # Call the main analysis function if needed, or structure as before
         # Assuming the main logic is within analyze_small_networks for now
         analyze_small_networks() 