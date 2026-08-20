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

### Fri-Tue, Feb 13-17, 2026 - Framework_V1 Validation
- framework v1 validation resumed
- created mega_backtest_48M_30S_v1_4_5_tatasteel.py to run it only for tatasteel after removing the issue where ma20 for first 19 candles was showing NaN
- used the TATASTEEL.parquet to fetch data instead of Upstox API call
- Need to now run the latest Claude sqlite3 query to test the mega_backtest_48M_30S_v1_4_5_tatasteel.db database however, there are some issue around it
- mega_backtest_48M_30S_v1_4_5_tatasteel.db and framework v1 output for tatasteel almost match. Need to further refine for an exact match

**TOMORROW'S TODO**
- Check on both mega_backtest_48M_30S_v1_4_5_tatasteel.py and framework v1 to fix the differences. Post that the framework v1 can be scaled to 30 stocks for futher backtesting

### Wed-Thu, Feb 18-19, 2026 - Framework_V1 Validation
- mega_backtest_48M_30S_v1_4_5_tatasteel.py and framework v1 output have certain mismatches that are being fixed such that we have the exact match of the outputs while retaining the superior logic overall
- fv1 and v145 now match exactly. Tested on tatasteel and vedanta

**TOMORROW'S TODO**
- Declare fv1 as the new flagship. scale to 30 stocks and further backtest to get better pnl etc

### Fri, Feb 20, 2026 - Backtest Analysis including v143/v145/v146 & fv1
- Currently writing sql queries to explore the results of all the 4 files in the sub heading

### Sat-Mon, Feb 21-23, 2026 - Backtest Analysis including v143/v145/v146 & fv1 and fv2 inception
- Ran multiple SQL queiries and found that the v143/145 had inflated results and v146/fv1 had technically sound script but strategically not up to the mark
- Biggest take away from fv1 development and analysis ---> helped to comeup with a roboust environment that can be used to implement strategies effectively
- Currently working towards development of fv2
- fv2 development has been paused as the focus has shifted to regime detection
- close > ma50 for current day changes the CAGR for fv1 from -9.74% to +8.77%. It can be used as the Ground Truth to build the regime detection filter upon

**TOMORROW'S TODO**
- Start the day with clarification around ma50 for jan and feb 2022 for fv1.
- understand the Drawdown concept using the information provided by CC in the last most recent chat
- work with Claude to build the regime filter that can match the Ground truth upto 70-80%

### Tue-Thu, Feb 24-26 - fv1_strategy_review.md walkthrough & Framework_V1_Sandbox Creation
- Currently reviewing fv1_strategy_review.md with Claude. Later would deploy the improvents on the fv1 via its sandbox environment + add optuna optimization
- downloaded dataset 1 and 2 from kaggle platform. The dataset shall be used for backtesting purpose

### Fri-Wed, Feb 27 - Mar 11 -  Kaggle dataset validation and fv1_strategy_review.md walkthrough
- Kaggle Dataset1(DS1) has 105 stock data and the DS2 has 499 stock data
- Plan is to now build Dataset3 or the DS3 via Kite MCP server. DS3 would hold the fv1 30 stock data
- Once DS3 is built, the fv1 review shall be resumed and improvements shall be applied on the fv1
- If the improved fv1 fetches good results then we move from DS3 to DS4 which is going to be 100 stocks universe
- DS5 has been discussed as a future option if and when required. universe of 500 stocks data
- Working with Claude Code to build the 
- DS3 build is complete
- Codeponting Project for storing important docs and CC context to be re-visited after fv1 review completion
# ORDER OF OPERATIONS for the fv1 review + fv1 sandbox run
-   STEP 1 → fv1_review.md Section 7, 8, 9
-   STEP 2 → TradingView Phase 1 visualization ← BEFORE backtest -> check the dedicated claude chat for tool list
            Confirm logic looks correct visually
-   STEP 3 → Sandbox 16 combinations on 2022-2025 -> Add pending changes from fv1_pending_changes.md
-   Step 4  → Regime filter Optuna — RE-RUNNING on full DS3 2015–2025 🔄
           Previous run was on 2022–2025 only → overfit, invalid.
           Script: Framework_V1_Sandbox/scripts/sb_regime_optuna.py
           Date filter: REMOVED — all years 2015–2025 included
           28 params (23 original + 5 new: PF10, MF6, TF5, MF7, SF1)
           Warm-up: 28 trials (one per filter, solo) via enqueue_trial()
           Sampler: TPE, 3000+ trials, fresh study DB
           Gate logic: OR and AND both in search space
           Optimize on: raw_pnl (raw CAGR)
           Baseline to beat: TBD after 2015–2025 baseline confirmed
           Stretch goal: net_pnl_kite CAGR positive
           Outputs: Framework_V1_Sandbox/outputs/optuna/
             ├── best_params.json
             ├── top20_trials.csv
             ├── optuna_study.db
             ├── optimization_history.png
             └── feature_importance.png

            Step 4.1 → Regime Filter Optuna — 2022–2025 (COMPLETE ✅)
             Best: Trial #2827, raw CAGR -4.48%, PF9+TF4, OR gate
             Finding: overfit — zero trades in 2015–2020
             Verdict: INVALID as general regime filter

            Step 4.2 → Regime Filter Optuna — Full DS3 2015–2025 (IN PROGRESS 🔄)
             Fresh run, date filter removed, dir_* TPE fix applied
             28 params, 3000 trials, TPE + 28 warm-up trials
             Baseline to beat: TBD after 2015–2025 baseline confirmed
             Constraint: no year should have zero trades with filter ON

            Step 4.3 → Bounce Quality Score

-   Step 5  → Full DS3 backtest 2015–2025 with Step 4 winner params
           Purpose: confirm Step 4 CAGR, update confirmed baseline
           This is a formality — sanity check only, no new Optuna run
           Status: PENDING Step 4 completion
-   STEP 6 → Python Phase 2 viewer ← AFTER backtest -> check the dedicated claude chat for tool list
-   STEP 7 → WFA + Optuna
-   STEP 8 → Paper trading (PENDING)
-   STEP 9 → Live trading

Parked for later steps:
  SL=D (trailing, ACT=3.0, TR=0.5) → revisit Step 7
  Fixed Fractional sizing (SB-G)   → revisit Step 7

**TOMORROW'S TODO**
- Analyse step 3 results. check the cost per trade that was discussed and accordingly have it applied.
- Check the CAGR for the 16 combinations without any changes i.e. remove the change 4 and 7 per pending review doc and then have the CAGR calculated for all the 16 combos and compare with fv1. pending changes can be applied right after step 3 in an independent way via optuna run

### Thu, Mar 12 -  fv1 Sandbox Development and testing
- Step 3 done. working on Step 4
- Master plan updated and so the CC context file


