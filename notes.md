
## Usefull Commands

wrangler d1 migrations apply npsnav --remote 
wrangler d1 migrations apply npsnav  


#### Import data from local to d1
npx wrangler d1 execute npsnav --remote --file=fund_data.sql


Add somewhere that reliance, DSP historical data is not tracked on website, but available in json

wrangler publish   - to publish worker to CF