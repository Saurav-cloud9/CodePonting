# Saurav's 2026 Algo Trading Journey - Jan 30 Onwards

### Fri, Jan 30, 2026 - Progress
- mega_backtest_48M_30S_v1_4_fixed_1 ---> Revisiting this to understand the output and performance.
- we have the best 10-15 stocks based on performance now.
- Need to check if these top stocks can be trusted upon to perform in the live market as well.
- If yes, then we can move ahead with paper trading them.
- Need to discuss the cost involved if any.

**TOMORROW'S TODO**
- Work on websockets + Async fix implementation for paper trading.
- mega_backtest_48M_30S_v1_4_3_DATA ---> check if this can be run on 2015-2022 data and then combined with current O/P
- mega_backtest_48M_30S_v1_4_3_DATA ---> check Gemini's feedback on this version. See if any changes suggested by Gemini can be implemented by claude before we move to paper trading.

---

### Sat, Jan 31, 2026 - mega_backtest_48M_30S_v1_4_3_DATA analysis
- mega_backtest_48M_30S_v1_4_3_DATA ---> Performance review ---> done
- mega_backtest_48M_30S_v1_4_3_DATA ---> need to create a new version to find the best extreme config ---> plan is to deploy the best backtest stocks in paper trading with the best extreme config SL/Target as per backtest results. ---> done
- simultaneoulsy working on websockets + Async fix implementation for paper trading. ---> forwarded to future date
- check Gemini's feedback on this version. See if any changes suggested by Gemini can be implemented by claude before we move to paper trading. ---> done
- Discuss how to use db + Jupyter nb combo for better analysis of backtest results. ---> forwarded to future date
- Check how Redis can be used for storing live trade data for better analysis. ---> forwarded to future date

---

### Sun, Feb 1, 2026 - mega_backtest_48M_30S_v1_4_3_Optimized & mega_backtest_48M_30S_v1_4_4 implementation
- mega_backtest_48M_30S_v1_4_3_DATA ---> Performance review ---> Revisited
- Mock Data Generator ---> whats this? ---> can we use it for backtesting? ---> forwarded to future date
- mega_backtest_48M_30S_v1_4_3_Optimized ---> Anti-Chasing Filter applied and created with multicore processing for faster backtesting ---> done 
- mega_backtest_48M_30S_v1_4_4 ---> New version to find the best extreme config ---> done
- Consistency matrix and csv file missing in mega_backtest_48M_30S_v1_4_3_Optimized and mega_backtest_48M_30S_v1_4_4 ---> forwarded to future date

**TOMORROW'S TODO**
- List all the TODO from the last two days clearly at the start and tick them off as we progress. 

---

### Mon, Feb 2, 2026 - mega_backtest_48M_30S_v1_4_3_Optimized & mega_backtest_48M_30S_v1_4_4 analysis
- Consistency matrix and csv file missing in mega_backtest_48M_30S_v1_4_3_Optimized and mega_backtest_48M_30S_v1_4_4 ---> done
- simultaneously working on websockets + Async fix implementation for paper trading. ---> switched to Framework_v1
- Discuss how to use db + Jupyter nb combo for better analysis of backtest results. ---> forwarded to future date
- Check how Redis can be used for storing live trade data for better analysis. ---> forwarded to future date
- Mock Data Generator ---> what's this? ---> can we use it for backtesting? ---> working with Gemini + Chatgpt to develop a script for this. ---> in progress
- db analysis of mega_backtest_48M_30S_v1_4_3_DATA and mega_backtest_48M_30S_v1_4_3_Optimized tells us that our strategy works only for 1 or 2 stocks at best and not for other stocks. Also, there is no reliability on the current model can easily break on a bad day and cause huge losses ---> done
- mega_backtest_48M_30S_v1_4_3_DATA doesn't give anything concrete. we have huge sl_rate although net profit is usually positive for cumulative data but can't be trusted for a given day. Need to refine the strategy further. 

**TOMORROW'S TODO**
- work with Gemini + Chatgpt to develop a Mock Data Generator script for backtesting. ---> discussion done ---> conclusion to be shared with Claude for further inputs.
- Check how Redis can be used for storing live trade data for better analysis. ---> starts from paper trading phase onwards.
- if time permits check with Claude regarding mega_backtest_48M_30S_v1_4_5 analysis, this is the one with all extreme configs and no anti-chasing filter. This one can be analysed for no filter performance. ---> done
- Based on our current backtesting, need to either revisit strategy or the GSS route based on how the best and worst months work. ---> done

---

### Tue, Feb 3, 2026 - Backtesting and strategy approach refinement
- "The XGBoost code uses yfinance.download() once, then pure local processing." ---> done
- work with Gemini + Chatgpt to develop a Mock Data Generator script for backtesting. ---> done

**TOMORROW'S TODO**
- Backtesting Code Robustness Comparison ---> discussion with gemini + chatgpt ---> Need to share the conclusion with Claude for further inputs. ---> done

---

### Wed, Feb 4, 2026 - Backtesting and strategy approach refinement contd.
- Backtesting Code Robustness Comparison ---> discussion with gemini + chatgpt ---> conclusion shared with Claude for further inputs. ---> done
- Backtesting_Framework & One System, Three Environments ---> Revisit these two ---> Create a master framework for all three environments and then get started with reframing the flagship backtesting code accordingly. ---> done

**TOMORROW'S TODO**
- Develop Framework_v1 code with Claude, Chatgpt and Gemini ---> in progress
- Quick review of new AI windsurf 

---

### Thu, Feb 5, 2026 - Framework_V1 development
- Developing Framework_v1 code with Claude, Chatgpt and Gemini 
- Quick review of new AI windsurf done
- Created the Core files for Framework_v1 i.e. engine.py, portfolio.py, strategy.py, indicators.py

**TOMORROW'S TODO**
- Resume developing Framework_v1 code with Claude, Chatgpt and Gemini
- Port the flagship strategy i.e. mega_backtest_48M_30S_v1_4_5 into Framework_v1 

### Fri-Mon, Feb 6-9, 2026 - Framework_V1 development
- run_backtest.py is built. Next need to run it and validate the flagship strategy ---> in progress
- Working on 01_data_download_exploration.ipynb to understand Upstox API and download data. Also, understand how parquet files are created and stored.
- 01_data_download_exploration.ipynb ---> Executed successfully for mock learning

---

### Mon-Thu, Feb 9-12, 2026 - Framework_V1 development
- Ran download_data.py successfully and downloaded intraday and daily 5 min candles for 30 stocks + Nifty
- 02_indicator_calculation.ipynb ---> Created 
- Dark view workaround established on Excel via claude Add-in ---> Needs refinement
- Installed visualization tools on Pycharm namely plotly, mplfinance and lightweight-charts
- 02_indicator_calculation.ipynb 03_bounce_detection.ipynb notebooks created and tested for mock learning
- run_backtest.py created and run successfully

**TOMORROW'S TODO**
- Validate the framework v1 against flagship backtest output

---

### Fri-Sun, Feb 13-17, 2026 - Framework_V1 Validation
- framework v1 validation resumed
- created mega_backtest_48M_30S_v1_4_5_tatasteel.py to run it only for tatasteel after removing the issue where ma20 for first 19 candles was showing NaN
- used the TATASTEEL.parquet to fetch data instead of Upstox API call
- Need to now run the latest Claude sqlite3 query to test the mega_backtest_48M_30S_v1_4_5_tatasteel.db database however, there are some issue around it.
- mega_backtest_48M_30S_v1_4_5_tatasteel.db and framework v1 output for tatasteel almost match. Need to further refine for an exact match

**TOMORROW'S TODO**
- Check on both mega_backtest_48M_30S_v1_4_5_tatasteel.py and framework v1 to fix the differences. Post that the framework v1 can be scaled to 30 stocks for futher backtesting