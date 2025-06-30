## Challenges
* **Figuring out the top 100 stocks list to include in my custom index.**
  * To pick the top 100 stocks list, the naive approach would have been to fetch a list of all publicly listed US stocks, somehow calculate their market cap everyday and then select the top 100 from among them with the highest market cap. This would be very computationally intense, since there are more than 4000 publicly listed US companies.
  * Instead I chose to fetch the stocks in S&P 500 everyday and calculate their market caps followed by selecting the top 100 stocks from this list everyday. I chose S&P500 because it consists of the top 500 publicly listed US companies with the largest market cap, so our top 100 stocks will very likely be in this list.
* **Calculating historical market cap**
  * At first I decided to use the yf.ticker module to fetch market cap data everyday, but the problem was it returns a snapshot of the current market data of a given ticker, which would not work if we wanted to backfill.
  * So I rewrote my logic to fetch market data using yf.download module, which allows to specify a data range, but it doesn't provide market cap values directly in the response.
  * To solve the above problem I used a combination of yf.ticker and yf.download.
  * I used yf.ticker to fetch *sharesOutstanding* for each ticker in S&P500 and yf.donwload to fetch *Close* price for each ticker, then calculated `marketCap = sharesOutstanding * Close`.
* **Market Holidays**
  * I didn't initially consider market holidays in my index generation logic.