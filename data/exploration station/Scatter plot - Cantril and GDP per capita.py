import pandas as pd
import pycountry_convert as pc

gdp_pop_url = 'https://www.worldometers.info/gdp/gdp-by-country/'
gdp_pop = pd.read_html(gdp_pop_url)

##The first/only table is the one we want
gdp_pop_table = gdp_pop[0]
##fix formatting of GDP
gdp_pop_table['GDP  (nominal, 2023)']=gdp_pop_table['GDP  (nominal, 2023)'].str.replace('$','').str.replace(',','').astype(int)
gdp_pop_table.drop(columns={'GDP  (abbrev.)','GDP growth','GDP per capita','Share of  World GDP'}, inplace=True)
gdp_pop_table.rename(columns={'GDP  (nominal, 2023)':'GDP', 'Population  (2023)':'Population'}, inplace=True)
##drop the first column, called '#'
gdp_pop_table=gdp_pop_table.iloc[:,1:]

cantril = pd.read_csv("https://ourworldindata.org/grapher/happiness-cantril-ladder.csv?v=1&csvType=full&useColumnShortNames=true", storage_options = {'User-Agent': 'Our World In Data data fetch/1.0'})
cantril.rename(columns={'Entity':'Country','cantril_ladder_score':'Cantril Ladder Score'}, inplace=True)
cantril.sort_values(by=['Country','Year'], inplace=True)
latest_cantril = cantril.groupby('Country').tail(1).reset_index(drop=True)

df=gdp_pop_table.merge(latest_cantril, on='Country', how='left')

##clean columns and rename
df.drop(columns=['Code','Year'], axis=1, inplace=True)

##Add continent column
remaining_countries = {
    'Czech Republic (Czechia)': 'Europe',
    'DR Congo': 'Africa',
    'State of Palestine': 'Asia',
    'Timor-Leste': 'Oceania',
    'St. Vincent & Grenadines': 'North America',
    'Saint Kitts & Nevis': 'North America',
    'Sao Tome & Principe': 'Africa'
}

def country_to_continent(country_name):
    # First, try to map the country using pycountry
    try:
        country_code = pc.country_name_to_country_alpha2(country_name, cn_name_format="default")
        continent_code = pc.country_alpha2_to_continent_code(country_code)
        continent_name = pc.convert_continent_code_to_continent_name(continent_code)
        return continent_name
    except:
        # If pycountry fails, check the remaining_countries dictionary
        return remaining_countries.get(country_name, None)

df['Continent'] = df['Country'].apply(country_to_continent)
df['GDP per Capita'] = df['GDP'] / df['Population']

df.to_csv('./data/output/Scatter plot - Cantril and GDP per capita by country.csv', index=False)

##aggregate at continent level
continent_gdp_per_capita = df.pivot_table(index='Continent', values=['GDP','Population'], aggfunc='sum').reset_index()
continent_cantril = df.pivot_table(index='Continent', values=['Cantril Ladder Score'], aggfunc='mean').reset_index()
continent=continent_gdp_per_capita.merge(continent_cantril, on='Continent', how='left')
continent.rename(columns={'Cantril Ladder Score':'Avg Cantril Ladder Score'}, inplace=True)
continent['GDP per Capita'] = continent['GDP'] / continent['Population']

continent.to_csv('./data/output/Scatter plot - Cantril and GDP per capita by continent.csv', index=False)