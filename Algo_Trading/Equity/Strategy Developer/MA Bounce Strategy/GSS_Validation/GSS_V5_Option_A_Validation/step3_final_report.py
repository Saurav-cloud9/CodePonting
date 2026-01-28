import pandas as pd


def generate_report():
    print("STEP 3: FINAL REPORT")
    tr = pd.read_csv('multistock_trading_results.csv')
    sr = pd.read_csv('threshold_sweep_results.csv')
    best_t = sr.loc[sr['test_precision'].idxmax()]

    total_pnl = tr['net_pnl'].sum()
    profitable = tr[tr['net_pnl'] > 0].shape[0]
    decision = "PASS" if (profitable >= 3 and total_pnl > 0) else "FAIL"

    report = f"""# GSS v5.0 Option A Report
## Summary
- **Decision:** {decision} {'✅' if decision == 'PASS' else '❌'}
- **Total P&L:** ₹{total_pnl:,.0f}
- **Profitable Stocks:** {profitable}/40
- **Best Threshold:** {int(best_t['threshold'])} ({best_t['test_precision']:.1f}% Precision)

## Results
{tr[['stock', 'total_trades', 'win_rate', 'net_pnl', 'wl_ratio']].to_markdown(index=False)}
"""
    with open('GSS_v5_Refinement_Report.md', 'w', encoding='utf-8') as f:
        f.write(report)
    emoji = '[PASS]' if decision == 'PASS' else '[FAIL]'
    print(f"Decision: {decision} {emoji}")

if __name__ == "__main__": generate_report()