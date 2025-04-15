#!/usr/bin/env python3
"""
GDP and Gini Data Processing Script

This script fetches GDP data and Gini coefficient data from multiple sources,
merges them into a comprehensive dataset, and exports the results to a CSV file.
"""

import os
import ssl
import urllib.error
import pandas as pd
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Tuple


def fetch_table_data(url: str, table_index: int = 0) -> pd.DataFrame:
    """
    Fetch HTML table data from the specified URL with error handling.
    
    Args:
        url: URL to fetch the table data from
        table_index: Index of the table to extract (default: 0, first table)
        
    Returns:
        DataFrame containing the table data
    """
    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()
        tables = pd.read_html(response.content)
        
        if len(tables) <= table_index:
            raise ValueError(f"No table found at index {table_index} (only {len(tables)} tables available)")
        
        return tables[table_index]
    except Exception as e:
        print(f"Error fetching data from {url}: {e}")
        return pd.DataFrame()


def fetch_western_countries_data(url: str) -> pd.DataFrame:
    """
    Fetch and parse 'Western' countries classification data using BeautifulSoup.
    
    Args:
        url: URL to fetch the western countries classification data
        
    Returns:
        DataFrame containing the western countries classification
    """
    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()
        
        # Parse HTML content
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Locate the table
        western_table = soup.find("table")
        if not western_table:
            raise ValueError("No table found on the page")
        
        # Extract rows
        rows = []
        for row in western_table.find_all("tr")[1:]:  # Skip the header row
            cells = row.find_all(["th", "td"])
            row_data = []
            for cell in cells:
                # Check for SVG icons
                svg = cell.find("svg")
                if svg:
                    if "tabler-icon-x" in svg.get("class", []):
                        row_data.append(False)
                    elif "tabler-icon-check" in svg.get("class", []):
                        row_data.append(True)
                    else:
                        row_data.append(None)  # Handle unexpected cases
                else:
                    row_data.append(cell.text.strip())
            rows.append(row_data)
        
        # Create a DataFrame with Western country classification data
        western_cols = {
            0: 'Country',
            1: 'Latin West',
            2: 'Cold War West',
            3: 'Rich West',
            4: 'Western Europe',
            5: 'Western Hemisphere'
        }
        
        df = pd.DataFrame(rows)
        df.rename(columns=western_cols, inplace=True)
        
        return df
    except Exception as e:
        print(f"Error fetching western countries data: {e}")
        return pd.DataFrame()


def merge_datasets(gdp_df: pd.DataFrame, gini_df: pd.DataFrame, 
                  western_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge multiple datasets into a single comprehensive DataFrame.
    
    Args:
        gdp_df: GDP data DataFrame
        gini_df: Gini coefficient DataFrame
        western_df: Western classification DataFrame
        
    Returns:
        Merged DataFrame with all data
    """
    # Merge GDP and Gini data
    merged_df = gdp_df.merge(gini_df, left_on='Country', right_on='Country', how='left')
    
    # Create a combined Gini coefficient column
    merged_df['Gini coefficient'] = merged_df['Gini Coefficient (World Bank) (%)'].fillna(
        merged_df['Gini Coefficient (CIA) (%)']
    )
    
    # Merge with western country classification data
    merged_df = merged_df.merge(western_df, left_on='Country', right_on='Country', how='left')
    
    # Fill NaN values in boolean columns with False
    western_cols = ['Latin West', 'Cold War West', 'Rich West', 'Western Europe', 'Western Hemisphere']
    for col in western_cols:
        if col in merged_df.columns:
            merged_df.loc[:, col] = merged_df[col].fillna(False)
    
    return merged_df


def export_data(df: pd.DataFrame, 
               output_path: str = './data/output/Scatter plot - GDP per capita and Gini.csv') -> None:
    """
    Export the processed data to a CSV file.
    
    Args:
        df: Processed DataFrame to export
        output_path: Path to save the output CSV file
        
    Returns:
        None
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Export to CSV
    df.to_csv(output_path, index=False)
    print(f"Successfully exported data to {output_path}")


def main() -> None:
    """Main function to orchestrate the data processing workflow."""
    # Disable SSL warnings for requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Define data source URLs
    gdp_url = 'https://www.worldometers.info/gdp/gdp-by-country/'
    gini_url = 'https://worldpopulationreview.com/country-rankings/gini-coefficient-by-country'
    western_url = 'https://worldpopulationreview.com/country-rankings/western-countries'
    
    # Fetch data from various sources
    print("Fetching GDP data...")
    gdp_table = fetch_table_data(gdp_url, 0)
    
    print("Fetching Gini coefficient data...")
    gini_table = fetch_table_data(gini_url, 0)
    
    print("Fetching Western countries classification data...")
    western_df = fetch_western_countries_data(western_url)
    
    # Merge datasets
    print("Merging datasets...")
    merged_data = merge_datasets(gdp_table, gini_table, western_df)
    
    # Export the merged dataset
    export_data(merged_data)
    
    print("Data processing completed successfully.")


if __name__ == "__main__":
    main()