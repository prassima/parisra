#!/usr/bin/env python3
"""
Population Data Processing Script

This script fetches population data from Our World in Data, processes it to obtain
the top 8 most populous countries, and exports the results to a CSV file.
"""

import os
import ssl
import urllib.error
import pandas as pd
from typing import List


def fetch_population_data(url: str) -> pd.DataFrame:
    """
    Fetch population data from the specified URL.
    
    Args:
        url: URL to fetch the population data from
        
    Returns:
        DataFrame containing the raw population data
    """
    headers = {'User-Agent': 'Our World In Data data fetch/1.0'}
    
    # Try with certificate verification first
    try:
        return pd.read_csv(url, storage_options=headers)
    except (ssl.SSLError, urllib.error.URLError):
        # If that fails, try with verification disabled
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        import requests
        
        print("Warning: SSL certificate verification failed. Trying with verification disabled.")
        # Using requests to get the data with verification disabled
        response = requests.get(url, headers=headers, verify=False)
        
        if response.status_code == 200:
            from io import StringIO
            return pd.read_csv(StringIO(response.text))
        else:
            raise Exception(f"Failed to fetch data: HTTP {response.status_code}")


def clean_population_data(df: pd.DataFrame, non_country_entities: List[str], 
                         year: int = 2021) -> pd.DataFrame:
    """
    Clean the population data by filtering out non-countries and selecting the latest year.
    
    Args:
        df: Raw population DataFrame
        non_country_entities: List of entities to exclude from the data
        year: Year to filter the data (default: 2021)
        
    Returns:
        Cleaned DataFrame with only country-level data for the specified year
    """
    # Filter only latest data, and exclude non countries
    cleaned_df = df.loc[
        (df['Year'] == year) & 
        (~df['Entity'].isin(non_country_entities)) & 
        (df['Entity'].notna())
    ].copy()
    
    # Sort by population
    cleaned_df.sort_values('population_historical', ascending=False, inplace=True)
    
    # Drop irrelevant columns
    cleaned_df.drop(columns=['Code', 'Year'], inplace=True)
    
    # Rename columns
    cleaned_df.rename(
        columns={'Entity': 'Country', 'population_historical': f'Population {year}'}, 
        inplace=True
    )
    
    return cleaned_df


def export_top_countries(df: pd.DataFrame, n: int = 8, 
                        output_path: str = './data/output/Bar chart - Population counts.csv') -> None:
    """
    Export the top n countries by population to a CSV file.
    
    Args:
        df: Cleaned population DataFrame
        n: Number of countries to export (default: 8)
        output_path: Path to save the output CSV file
        
    Returns:
        None
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Export only top n values
    df.head(n).to_csv(output_path, index=False)
    print(f"Successfully exported top {n} countries to {output_path}")


def main() -> None:
    """Main function to orchestrate the population data processing workflow."""
    # Data source URL
    url = "https://ourworldindata.org/grapher/population.csv?v=1&csvType=full&useColumnShortNames=true"
    
    # List of entities that are not countries, to filter out
    non_country_entities = [
        "Africa (UN)",
        "Africa",
        "Americas (UN)",
        "Antarctica",
        "Asia",
        "Asia (UN)",
        "Asia (excl. China and India)",
        "Europe",
        "Europe (UN)",
        "Europe (excl. EU-27)",
        "Europe (excl. EU-28)",
        "Europe (excl. Russia)",
        "European Union (27)",
        "European Union (28)",
        "High-income countries",
        "Upper-middle-income countries",
        "International aviation",
        "International shipping",
        "Latin America and the Caribbean (UN)",
        "Low-income countries",
        "Lower-middle-income countries",
        "Northern America (UN)",
        "North America",
        "North America (excl. USA)",
        "Oceania",
        "Ryukyu Islands (GCP)",
        "Kuwaiti Oil Fires (GCP)",
        "South America",
        "South America (excl. Brazil)",
        "World"
    ]
    
    # Execute the data processing pipeline
    pop_data = fetch_population_data(url)
    pop_cleaned = clean_population_data(pop_data, non_country_entities)
    export_top_countries(pop_cleaned)


if __name__ == "__main__":
    main()