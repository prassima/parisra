import os
from dotenv import load_dotenv
from google.oauth2 import service_account
import pandas_gbq

# I use environment variables from my .env file. Read more about this approach here: https://pypi.org/project/python-dotenv/
load_dotenv()

# Get the credentials path from the environment variable
key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
project_id = os.getenv("GOOGLE_CLOUD_PROJECT")

# Authenticate using the service account credentials
credentials = service_account.Credentials.from_service_account_file(key_path)

sql = '''
select 
-- adding in user first touch timestamp as a failsafe when the user_id is null.
  CONCAT(COALESCE(user_pseudo_id,cast(user_first_touch_timestamp as string)),coalesce((select value.int_value from unnest(event_params) where key = 'ga_session_id'),user_first_touch_timestamp)) as unique_session_id,

  timestamp_micros(event_timestamp) as event_timestamp, event_name, device.category as device,

  -- making a clean page_location without parameters etc
  -- beginning with regexp_replace to remove the final / from the string
  lower(REGEXP_REPLACE(
  -- if the page location has a ?
  if(regexp_contains((SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location'),r'\?'),
  -- then return the string until the ?, minus 1.
  left((SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location'),
  regexp_instr((SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location'), r'\?')-1),
  -- else provide the string
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location'))
  -- and here is the end of the regexp_replace to replace the final / with nothing, as well as https:// and www. with nothing
  , r'(https?://(?:www\.)?|\/$)','')) as page_location_clean,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location') as page_location,

  -- signal if the entire session was engaged based on the below
  MAX(
    (case
      when (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'session_engaged') = '1'
      then 1
      when (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'session_engaged') = 1
      then 1
      when (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'engaged_session_event') = 1
      then 1
      else 0 end
      )
    )
  OVER (
    PARTITION BY concat(coalesce(user_pseudo_id,cast(user_first_touch_timestamp as string)),coalesce((select value.int_value from unnest(event_params) where key = 'ga_session_id'),user_first_touch_timestamp))
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING -- this ensures all rows in the partition are assessed
  ) as engaged_session,
  -- utm_parameters for all events beyond page_view
  LAST_VALUE((select value.string_value from unnest(event_params) where key = 'source'))
  OVER (
    PARTITION BY concat(coalesce(user_pseudo_id,cast(user_first_touch_timestamp as string)),coalesce((select value.int_value from unnest(event_params) where key = 'ga_session_id'),user_first_touch_timestamp)) -- we want the same value across entire unique_session_ids
    ORDER BY (select value.string_value from unnest(event_params) where key = 'source') -- we order by source to ensure the null value would be first
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING -- this ensures all rows in the partition are assessed
  ) as utm_source,
  LAST_VALUE((select value.string_value from unnest(event_params) where key = 'medium'))
  OVER (
    PARTITION BY concat(coalesce(user_pseudo_id,cast(user_first_touch_timestamp as string)),coalesce((select value.int_value from unnest(event_params) where key = 'ga_session_id'),user_first_touch_timestamp)) -- we want the same value across entire unique_session_ids
    ORDER BY (select value.string_value from unnest(event_params) where key = 'medium') -- we order by medium to ensure the null value would be first
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING -- this ensures all rows in the partition are assessed
  ) as utm_medium,
  LAST_VALUE((select value.string_value from unnest(event_params) where key = 'campaign'))
  OVER (
    PARTITION BY concat(coalesce(user_pseudo_id,cast(user_first_touch_timestamp as string)),coalesce((select value.int_value from unnest(event_params) where key = 'ga_session_id'),user_first_touch_timestamp)) -- we want the same value across entire unique_session_ids
    ORDER BY (select value.string_value from unnest(event_params) where key = 'campaign') -- we order by campaign to ensure the null value would be first
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING -- this ensures all rows in the partition are assessed
  ) as utm_campaign,
  LAST_VALUE((select value.string_value from unnest(event_params) where key = 'term'))
  OVER (
    PARTITION BY concat(coalesce(user_pseudo_id,cast(user_first_touch_timestamp as string)),coalesce((select value.int_value from unnest(event_params) where key = 'ga_session_id'),user_first_touch_timestamp)) -- we want the same value across entire unique_session_ids
    ORDER BY (select value.string_value from unnest(event_params) where key = 'term') -- we order by term to ensure the null value would be first
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING -- this ensures all rows in the partition are assessed
  ) as utm_term,
  LAST_VALUE((select value.string_value from unnest(event_params) where key = 'content'))
  OVER (
    PARTITION BY concat(coalesce(user_pseudo_id,cast(user_first_touch_timestamp as string)),coalesce((select value.int_value from unnest(event_params) where key = 'ga_session_id'),user_first_touch_timestamp)) -- we want the same value across entire unique_session_ids
    ORDER BY (select value.string_value from unnest(event_params) where key = 'content') -- we order by content to ensure the null value would be first
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING -- this ensures all rows in the partition are assessed
  ) as utm_content,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'percent_scrolled') as percent_scrolled,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'engagement_time_msec') as engagement_time_msec,
  geo.country as country

from `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_20210106` --single date chosen

order by event_timestamp

limit 2000 --only first 2000 events in the day to limit file size for demo purpose
'''

# Query BigQuery
df = pandas_gbq.read_gbq(sql, project_id=project_id, credentials=credentials)

df.to_csv('./data/output/GA4 sample - BQ public data.csv', index=False)
