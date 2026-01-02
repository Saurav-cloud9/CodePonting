from __future__ import annotations
# download_historical_data_upstox.py
# Downloads 5-min historical data via Upstox API with MAs calculated

import requests
import pandas as pd
from typing import cast
import os
import urllib.parse

# Fix: import `cast` to explicitly tell static analyzers when a variable is a DataFrame

# ============================================
# CONFIGURATION
# ============================================

ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTU2Mjg5MTM2Y2Q3YjE0Y2VkMGYwM2UiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2NzI1NDE2MSwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY3MzA0ODAwfQ.fPdRxuanahJl4fKaPeUt9i6s6NVBeENyaQqhzhRxYgI"

# Stocks to analyze - Upstox format
STOCKS = {
    "YESBANK": "NSE_EQ|INE528G01027",
    "SUZLON": "NSE_EQ|INE040H01021",
    "PNB": "NSE_EQ|INE160A01022",
    "TATASTEEL": "NSE_EQ|INE081A01020",
    "IDEA": "NSE_EQ|INE669E01016"
}

# Date range
END_DATE = "2024-12-31"
START_DATE = "2024-12-20"

# Precompute date objects for filtering
START_DATE_DT = pd.to_datetime(START_DATE).date()
END_DATE_DT = pd.to_datetime(END_DATE).date()

# Output directory
OUTPUT_DIR = os.path.expanduser(r"C:\Users\saurav\CodePonting\pythonProject\Algo Trading\Equity\Strategy Developer\MA Bounce Strategy")


# ============================================
# FUNCTIONS
# ============================================

def calculate_ma(df, period):
    """Calculate Simple Moving Average"""
    return df['close'].rolling(window=period).mean()


def find_instrument_key(stock_symbol: str, headers: dict) -> str | None:
    """Attempt to find an instrument key by querying common Upstox instruments endpoints.

    Returns first plausible instrument_key/identifier or None if not found.
    """
    base = "https://api.upstox.com/v2"
    endpoints = [
        f"{base}/instruments?exchange=NSE",
        f"{base}/instruments",
        f"{base}/instruments/NSE",
        f"{base}/instruments/search/{urllib.parse.quote(stock_symbol)}",
    ]

    for ep in endpoints:
        try:
            print(f"  ➜ Probing instruments endpoint: {ep}")
            r = requests.get(ep, headers=headers, timeout=10)
        except Exception as e:
            print(f"    ❌ Probe request failed: {e}")
            continue

        if r.status_code != 200:
            print(f"    ⚠️ Probe returned status {r.status_code}")
            continue

        try:
            payload = r.json()
        except Exception as e:
            print(f"    ⚠️ Could not decode JSON from {ep}: {e}")
            continue

        # Diagnostic: print brief summary of payload structure to aid debugging
        try:
            import json as _json
            if isinstance(payload, dict):
                print(f"    ℹ️ Payload keys: {list(payload.keys())}")
            else:
                print(f"    ℹ️ Payload type: {type(payload).__name__}")
        except Exception:
            pass

        # Payload may be a list or contain a 'data' list
        candidates = []
        if isinstance(payload, dict):
            if 'data' in payload and isinstance(payload['data'], list):
                candidates = payload['data']
            elif isinstance(payload.get('instruments'), list):
                candidates = payload.get('instruments')
            else:
                # If it's a dict of instruments keyed by something, try values
                vals = [v for v in payload.values() if isinstance(v, list)]
                if vals:
                    candidates = vals[0]
        elif isinstance(payload, list):
            candidates = payload

        # Search for matching trading symbol / ISIN
        print(f"    ℹ️ Inspecting {len(candidates)} candidate instruments (showing up to 3):")
        try:
            import json as _json
            for sample in candidates[:3]:
                if isinstance(sample, dict):
                    snippet = {k: sample.get(k) for k in ('tradingsymbol', 'symbol', 'isin', 'instrument_key', 'instrumentKey', 'token', 'id') if k in sample}
                    print(f"      - { _json.dumps(snippet, ensure_ascii=False) }")
                else:
                    print(f"      - {repr(sample)[:200]}")
        except Exception:
            pass

        for item in candidates:
            if not isinstance(item, dict):
                continue
            ts = item.get('tradingsymbol') or item.get('symbol') or item.get('tradingSymbol')
            isin = item.get('isin') or item.get('ISIN')
            # Match exact or case-insensitive
            if ts and ts.upper() == stock_symbol.upper():
                # Prefer instrument_key-like fields
                for key_field in ('instrument_key', 'instrumentKey', 'instrument_token', 'instrumentToken', 'token', 'id'):
                    if key_field in item:
                        print(f"    ✅ Found instrument via {ep}: {key_field}={item[key_field]}")
                        return item[key_field]
                # Fall back to ISIN if present
                if isin:
                    print(f"    ✅ Found instrument via {ep}: use ISIN {isin}")
                    return isin
                # Try combining exchange with symbol
                if ts:
                    candidate = f"NSE:{ts}"
                    print(f"    ℹ️ Found tradingsymbol; suggesting candidate {candidate}")
                    return candidate
            # Relaxed match: substring match in trading symbol
            if ts and stock_symbol.upper() in ts.upper():
                for key_field in ('instrument_key', 'instrumentKey', 'instrument_token', 'instrumentToken', 'token', 'id'):
                    if key_field in item:
                        print(f"    ✅ (substring) Found instrument via {ep}: {key_field}={item[key_field]}")
                        return item[key_field]
                if isin:
                    print(f"    ✅ (substring) Found ISIN via {ep}: {isin}")
                    return isin

        # Not found in this endpoint, continue
    return None


def download_upstox_data(symbol_name: str, instrument_key: str) -> pd.DataFrame | None:
    """Download historical data from Upstox"""

    print(f"\nDownloading {symbol_name}...")

    # Fix: use base endpoint and specify interval in the path.
    # Upstox API expects the path `/historical-candle/{interval}/{instrument_key}/{to_date}`
    # Note: Upstox does not accept '5minute' as interval (error UDAPI1020). Use one of
    # (1minute,30minute,day,week,month). We'll use 1minute here (you can change as needed).
    url = "https://api.upstox.com/v2/historical-candle"
    interval = "1minute"  # Fix applied: 5minute is unsupported by Upstox; using 1minute

    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {ACCESS_TOKEN}'
    }

    # Try several candidate instrument key formats to handle API expectations
    # Common variants: original (NSE_EQ|ISIN), ISIN only, NSE:{symbol}, symbol only, and alternate separators
    stock_symbol = symbol_name  # e.g., 'YESBANK'
    raw_key = instrument_key
    isin = instrument_key.split('|')[-1] if '|' in instrument_key else instrument_key
    # Add more candidate formats to handle different API expectations
    candidates = [
        raw_key,
        instrument_key.replace('|', ':'),
        isin,
        f"NSE:{stock_symbol}",
        stock_symbol,
        f"NSE_EQ|{isin}",
        f"NSE|{isin}",
        f"NSE:{isin}",
        f"{isin}|NSE_EQ",
        instrument_key.replace('|', ''),
    ]

    # Fix: attempt to discover the instrument key via instruments endpoints and try it first if found
    discovered_key = find_instrument_key(stock_symbol, headers)
    if discovered_key:
        print(f"  ➜ Using discovered instrument key: {discovered_key}")
        candidates.insert(0, discovered_key)

    response = None
    tried_endpoints = []

    for cand in candidates:
        cand_enc = urllib.parse.quote(cand, safe='')
        int_enc = urllib.parse.quote(interval, safe='')
        endpoint = f"{url}/{int_enc}/{cand_enc}/{END_DATE}"
        tried_endpoints.append(endpoint)
        print(f"  ➜ Trying endpoint: {endpoint}")

        try:
            response = requests.get(endpoint, headers=headers)
        except Exception as e:
            print(f"  ❌ Request error for {endpoint}: {e}")
            response = None

        if response is None:
            continue

        if response.status_code == 200:
            # success
            break

        # if 400 with instrument/interval parse errors, try next candidate
        if response.status_code == 400:
            # Print response body for debugging (UDAPI error codes live here)
            try:
                print(f"    ❗ Response body for {cand}: {response.text}")
                err = response.json()
                codes = [e.get('errorCode') for e in err.get('errors', []) if isinstance(err.get('errors', []), list)]
            except Exception:
                codes = []

            # If error indicates invalid instrument key, continue to next candidate
            if any(c in ('UDAPI100011', 'UDAPI1020', 'UDAPI1021') for c in codes):
                print(f"  ⚠️ API returned {codes} for candidate '{cand}', trying next format...")
                continue

        # For other error codes, stop and report
        print(f"  ❌ Error {response.status_code}: {response.text}")
        return None

    if response is None:
        print("  ❌ No response from server")
        return None

    if response.status_code != 200:
        # Try to discover instrument key via instruments endpoints as a fallback
        print("  ⚠️ Candidate formats failed; attempting to probe instruments endpoint to discover instrument key...")
        discovered = find_instrument_key(stock_symbol, headers)
        if discovered:
            print(f"  ➜ Discovered instrument key suggestion: {discovered}; retrying request")
            cand_enc = urllib.parse.quote(discovered, safe='')
            int_enc = urllib.parse.quote(interval, safe='')
            endpoint = f"{url}/{int_enc}/{cand_enc}/{END_DATE}"
            print(f"  ➜ Trying discovered endpoint: {endpoint}")
            try:
                response = requests.get(endpoint, headers=headers)
            except Exception as e:
                print(f"  ❌ Request error for discovered endpoint: {e}")
                return None

            if response.status_code == 200:
                data = response.json()
            else:
                print(f"  ❌ Discovered key attempt failed with {response.status_code}: {response.text}")
                # Fall through to diagnostics below

        if response.status_code != 200:
            # Print diagnostic: tried endpoints and the last response body
            print("  ❌ After trying candidates, no valid instrument_key found.")
            print("  ❗ Tried endpoints:")
            for e in tried_endpoints:
                print(f"    - {e}")
            print("  ❗ Last response body:")
            try:
                print(response.text)
            except Exception:
                print("    (unable to print response text)")

            # Interactive fallback: ask the user to provide an instrument key to retry once
            try:
                user_key = input(f"Enter instrument_key for {stock_symbol} (or press Enter to skip): ")
            except Exception:
                user_key = None

            if user_key:
                cand_enc = urllib.parse.quote(user_key, safe='')
                int_enc = urllib.parse.quote(interval, safe='')
                endpoint = f"{url}/{int_enc}/{cand_enc}/{END_DATE}"
                print(f"  ➜ Trying user-supplied endpoint: {endpoint}")
                try:
                    response = requests.get(endpoint, headers=headers)
                except Exception as e:
                    print(f"  ❌ Request error for user-supplied endpoint: {e}")
                    return None

                if response.status_code == 200:
                    data = response.json()
                else:
                    print(f"  ❌ User-supplied key attempt failed with {response.status_code}: {response.text}")
                    print("\nSuggestion: verify the instrument_key values in the STOCKS mapping or obtain the correct instrument key/ISIN from Upstox or your data provider.")
                    return None

            else:
                print("\nSuggestion: verify the instrument_key values in the STOCKS mapping.\n" \
                      "If you don't have instrument keys, call the Upstox instruments API or ask your data provider for the correct instrument key/ISIN.\n" \
                      "You can also add the correct instrument_key directly to STOCKS and rerun.")
                return None

    data = response.json()

    if 'data' not in data or 'candles' not in data['data']:
        print(f"  ❌ No candle data in response")
        return None

    # Upstox candles format: [timestamp, open, high, low, close, volume, oi]
    candles = data['data']['candles']

    if not candles:
        print("  ❌ No candles returned")
        return None

    # Initialize locals (df as empty DataFrame so static analysis recognizes its type)
    df = pd.DataFrame()
    cols = []

    # Normalize candle rows: some responses omit 'oi' (6 items) while others include it (7 items)
    first_len = len(candles[0])
    if first_len == 7:
        cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'oi']
    elif first_len == 6:
        cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    else:
        # Fall back to a generic DataFrame and try to coerce expected columns by position
        df = pd.DataFrame(candles)
        # Attempt to name first 6 columns if present
        if df.shape[1] >= 6:
            df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume'] + [f'v{i}' for i in range(df.shape[1]-6)]
        else:
            # Unexpected format
            print(f"  ❌ Unexpected candle format with {df.shape[1]} columns")
            return None

    # If df is still empty (not filled in fallback), create with determined cols
    if df.empty:
        df = pd.DataFrame(candles, columns=cols)

    # Fix: explicitly cast df to pd.DataFrame so static type-checkers know its type
    # This clears misleading warnings about df possibly being None or 'type' in analysis tools
    df = cast(pd.DataFrame, df)  # Fix applied: ensure df treated as DataFrame

    # Ensure required columns exist before proceeding
    if 'timestamp' not in df.columns or 'close' not in df.columns:
        print("  ❌ Required columns ('timestamp' and 'close') missing in candle data")
        return None

    # Ensure numeric columns are numeric (coerce invalid values to NaN)
    for col in ['open', 'high', 'low', 'close', 'volume', 'oi']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Convert timestamp to datetime (use apply to get date/time to avoid .dt type warnings)
    df['timestamp'] = pd.to_datetime(df['timestamp'])  # Fix: use plain to_datetime for clarity
    # Fix: use apply(...) to extract python date/time objects — avoids static analyzer `.dt` issues
    df['date'] = df['timestamp'].apply(lambda ts: ts.date() if pd.notnull(ts) else None)
    df['time'] = df['timestamp'].apply(lambda ts: ts.time() if pd.notnull(ts) else None)

    # Filter date range using precomputed dates
    # Fix: ensure 'date' is of proper date type; keep DataFrame semantics
    df = df[(df['date'] >= START_DATE_DT) & (df['date'] <= END_DATE_DT)]

    # Calculate MAs
    df['MA20'] = calculate_ma(df, 20)
    df['MA50'] = calculate_ma(df, 50)
    df['MA100'] = calculate_ma(df, 100)
    df['MA200'] = calculate_ma(df, 200)

    # Trend checks
    df['Price_Above_MA50'] = df['close'] > df['MA50']
    df['Price_Above_MA100'] = df['close'] > df['MA100']
    df['Price_Above_MA200'] = df['close'] > df['MA200']
    df['MA20_Above_MA50'] = df['MA20'] > df['MA50']
    df['MA20_Above_MA100'] = df['MA20'] > df['MA100']
    df['MA20_Above_MA200'] = df['MA20'] > df['MA200']

    # Distance from MAs
    df['Distance_MA20_%'] = ((df['close'] - df['MA20']) / df['MA20'] * 100).round(2)
    df['Distance_MA50_%'] = ((df['close'] - df['MA50']) / df['MA50'] * 100).round(2)

    # Add symbol
    df['symbol'] = symbol_name

    # Reorder columns
    cols_present = [c for c in ['date', 'time', 'symbol', 'open', 'high', 'low', 'close', 'volume',
                                'MA20', 'MA50', 'MA100', 'MA200',
                                'Price_Above_MA50', 'Price_Above_MA100', 'Price_Above_MA200',
                                'MA20_Above_MA50', 'MA20_Above_MA100', 'MA20_Above_MA200',
                                'Distance_MA20_%', 'Distance_MA50_%'] if c in df.columns]
    df = df[cols_present]

    print(f"  ✅ Downloaded {len(df)} candles")
    return df



def main():
    """Main execution"""

    print("=" * 60)
    print("UPSTOX HISTORICAL DATA DOWNLOADER - MA BOUNCE STRATEGY")
    print("=" * 60)

    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {ACCESS_TOKEN}'
    }

    all_data = []

    # Download data for each stock
    for stock, instrument_key in STOCKS.items():
        print(f"\nProcessing {stock}...")
        df = download_upstox_data(stock, instrument_key)
        if df is not None and not df.empty:
            all_data.append(df)
        else:
            print(f"  ❌ No data downloaded for {stock}")

    if not all_data:
        print("  ❌ No data available for analysis. Check errors above.")
        return

    # Concatenate all data into a single DataFrame
    full_data = pd.concat(all_data, ignore_index=True)

    # Output file
    output_file = os.path.join(OUTPUT_DIR, f"upstox_historical_data_{START_DATE}_{END_DATE}.xlsx")
    print(f"\nSaving combined data to {output_file}...")

    # Write to Excel with separate sheets for each stock
    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        # Write each DataFrame to a separate sheet
        for stock, df in zip(STOCKS.keys(), all_data):
            df.to_excel(writer, sheet_name=stock[:31], index=False)

        # Get the xlsxwriter workbook and worksheet objects.
        workbook  = writer.book
        #worksheet = writer.sheets['Sheet1']

        # Add a header format with bold text and a background color.
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#FFA07A',  # Light Salmon
            'border': 1})

        # Apply the header format to all sheets
        for stock in STOCKS.keys():
            worksheet = writer.sheets[stock[:31]]  # Get the worksheet by name (truncate to 31 chars)
            # Get the number of columns in the DataFrame
            num_cols = len(all_data[0].columns)
            # Apply the format to the first row (header row)
            worksheet.set_row(0, None, header_format)
            # Optionally, set the column width for better readability
            worksheet.set_column(0, num_cols-1, 12)  # Set width for all columns

    print(f"  ✅ Data successfully saved to {output_file}")

    # Diagnostics: show a few rows of the combined DataFrame
    try:
        print("\nCombined Data (sample):")
        print(full_data.head())
    except Exception as e:
        print(f"  ❌ Error displaying combined data sample: {e}")

    print("\nDone.")


# Execute only if run as a script (not imported)
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Unexpected error in main execution: {e}")
        import traceback
        traceback.print_exc()
