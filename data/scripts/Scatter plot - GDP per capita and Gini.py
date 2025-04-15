import pandas as pd
import requests
from bs4 import BeautifulSoup

# URL of the webpage containing the GDP table
gdp_url = 'https://www.worldometers.info/gdp/gdp-by-country/'
gdp_response = requests.get(gdp_url)
gdp = pd.read_html(gdp_response.content)

# The first/only table is the one we want
gdp_table = gdp[0]

## Get Gini Coefficient data
gini_url = 'https://worldpopulationreview.com/country-rankings/gini-coefficient-by-country'
gini_response = requests.get(gini_url)
gini = pd.read_html(gini_response.content)

# The 1st table is the one we want
gini_table = gini[0]


# Get table classifying various 'Western' countries
western_url = "https://worldpopulationreview.com/country-rankings/western-countries"
western_response = requests.get(western_url)
western_html_content = western_response.content
soup = BeautifulSoup(western_html_content, "html.parser")

# Locate the table
western_table = soup.find("table")  # Adjust if there multiple tables arise

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

# Create a DataFrame
western = pd.DataFrame(rows)
# update column names
western_cols = {0:'Country',1:'Latin West',2:'Cold War West',3:'Rich West',4:'Western Europe',5:'Western Hemisphere'}
western.rename(columns=western_cols, inplace=True)


# Merge the various DataFrames on the 'Country' column
merged_table = gdp_table.merge(gini_table, left_on='Country', right_on='Country', how='left')
merged_table['Gini coefficient']=merged_table['Gini Coefficient (World Bank) (%)'].fillna(merged_table['Gini Coefficient (CIA) (%)'])
merged_table = merged_table.merge(western, left_on='Country', right_on='Country', how='left')
#fillna with False
merged_table.loc[:, ['Latin West', 'Cold War West', 'Rich West', 'Western Europe', 'Western Hemisphere']] = (
    merged_table[['Latin West', 'Cold War West', 'Rich West', 'Western Europe', 'Western Hemisphere']].fillna(False)
)

# Save the updated DataFrame to a new CSV file
merged_table.to_csv('./data/output/Scatter plot - GDP per capita and Gini.csv', index=False)