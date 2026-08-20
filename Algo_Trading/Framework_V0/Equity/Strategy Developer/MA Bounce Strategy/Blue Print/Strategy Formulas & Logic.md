# ATR-based SL/Target configurations ---> mega_backtest_48M_30S_v1_4_3_DATA
ATR_CONFIGS = {
    'Sideways': {'sl_mult': 1.0, 'tp_mult': 1.5},
    'Regular-1': {'sl_mult': 1.5, 'tp_mult': 2.0},
    'Regular-2': {'sl_mult': 2.0, 'tp_mult': 3.0},
    'Extreme': {'sl_mult': 2.5, 'tp_mult': 4.0}
}

# ATR-based SL/Target configurations ---> mega_backtest_48M_30S_v1_4_4
ATR_CONFIGS = {
    'Extreme-1': {'sl_mult': 2.5, 'tp_mult': 4.0},  # v1_4_3_DATA proven winner
    'Extreme-2': {'sl_mult': 2.5, 'tp_mult': 4.5},  # Wider target, same SL
    'Extreme-3': {'sl_mult': 3.0, 'tp_mult': 4.5},  # Both wider
    'Extreme-4': {'sl_mult': 3.0, 'tp_mult': 5.0}   # Maximum aggression
}
