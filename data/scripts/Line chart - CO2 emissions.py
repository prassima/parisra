#!/usr/bin/env python3
"""
CO2 Emissions Data Processing Script

This script fetches CO2 emissions data from Our World in Data, processes it to obtain
global emissions by decade since 1800, and exports the results to a CSV file.
"""

import os
import ssl
import urllib.error
import pandas as pd
from typing import List, Dict, Any


def fetch_emissions_data(url: str) -> pd.DataFrame:
    """
    Fetch CO2 emissions data from the specified URL with error handling.
    
    Args:
        url: URL to fetch the emissions data from
        
    Returns:
        DataFrame containing the raw emissions data
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


def clean_emissions_data(df: pd.DataFrame, entity: str = 'World', 
                         start_year: int = 1800, decade_interval: bool = True) -> pd.DataFrame:
    """
    Clean the emissions data by filtering for a specific entity and time period.
    
    Args:
        df: Raw emissions DataFrame
        entity: Entity to filter for (default: 'World')
        start_year: Starting year for the data (default: 1800)
        decade_interval: Whether to filter for decade intervals only (default: True)
        
    Returns:
        Cleaned DataFrame with only the specified entity and time period
    """
    # Apply filters
    query = f"Entity == '{entity}' & Year > {start_year}"
    if decade_interval:
        query += " & Year % 10 == 0"
    
    cleaned_df = df.query(query).copy()
    
    # Create combined category for cement, flaring and other industry
    cleaned_df['Cement, Flaring & Other Industry'] = cleaned_df[[
        'emissions_from_cement',
        'emissions_from_flaring',
        'emissions_from_other_industry'
    ]].sum(axis=1)
    
    # Drop unnecessary columns
    cleaned_df.drop(columns=[
        'Entity',
        'Code',
        'emissions_from_cement',
        'emissions_from_other_industry',
        'emissions_from_flaring'
    ], inplace=True)
    
    # Rename remaining emissions columns
    cleaned_df.rename(columns={
        'emissions_from_oil': 'Oil',
        'emissions_from_coal': 'Coal',
        'emissions_from_gas': 'Gas'
    }, inplace=True)
    
    # Sort by year for chronological order
    cleaned_df.sort_values('Year', inplace=True)
    
    return cleaned_df


def export_data(df: pd.DataFrame, 
               output_path: str = './data/output/Line chart - CO2 emissions.csv') -> None:
    """
    Export the processed emissions data to a CSV file.
    
    Args:
        df: Processed emissions DataFrame
        output_path: Path to save the output CSV file
        
    Returns:
        None
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Export to CSV
    df.to_csv(output_path, index=False)
    print(f"Successfully exported emissions data to {output_path}")


def main() -> None:
    """Main function to orchestrate the CO2 emissions data processing workflow."""
    # Data source URL
    url = ("https://ourworldindata.org/grapher/co2-emissions-by-fuel-line.csv"
           "?v=1&csvType=full&useColumnShortNames=true")
    
    # Execute the data processing pipeline
    co2_data = fetch_emissions_data(url)
    co2_cleaned = clean_emissions_data(co2_data)
    export_data(co2_cleaned)


if __name__ == "__main__":
    main()