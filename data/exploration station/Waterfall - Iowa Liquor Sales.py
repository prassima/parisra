from pandas_gbq import read_gbq
import pandas

query = """
    SELECT case
           when chg >= 20000 then category
           when chg <= -20000 then category
           when chg < 20000 then "Other"
           when chg > -20000 then "Other"
           else category end as category, sum(chg) as chg
    from (
         select initcap(category_name) as category,
                cast(
                        sum(
                                if( date>='2024-01-01',volume_sold_liters,null)
                        )
                            -
                        sum(
                                if( date<'2024-01-01',volume_sold_liters,null)
                        )
                    as int) as chg

         FROM `bigquery-public-data.iowa_liquor_sales.sales`
         where date between '2023-01-01' and '2024-12-31'

         group by all)


    group by all

    order by 1
"""

project_id = "data-warehouse-dummy" ##adjust accordingly


df = read_gbq(query, project_id=project_id)

df.to_csv('./data/output/Waterfall - Iowa Liquor Sales.csv', index=False)