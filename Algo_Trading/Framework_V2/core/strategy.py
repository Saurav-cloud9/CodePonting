# fv2 Core Strategy — MA20 Bounce

def is_touch(low, ma20):
    return low <= ma20

def is_bounce(close, open_, ma20):
    return close > ma20 and open_ > ma20
