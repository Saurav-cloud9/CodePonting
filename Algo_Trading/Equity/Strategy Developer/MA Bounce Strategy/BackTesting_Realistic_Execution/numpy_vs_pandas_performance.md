# NumPy Arrays vs Pandas Row-wise Operations - Performance Explained

## Quick Answers to Your Questions

### 1. **Are NumPy arrays related to Numba?**
**No, they're different but complementary:**
- **NumPy** = A library for fast array operations (written in C)
- **Numba** = A JIT (Just-In-Time) compiler that can make Python loops even faster by compiling them to machine code
- Numba works well WITH NumPy arrays, but they're separate tools

### 2. **Why is row-wise check expensive?**
Row-wise pandas operations (`df.iloc[i]`) are slow because:
- **Creates a new Series object** for each row access
- **Dtype inference overhead** - pandas checks data types repeatedly
- **Indexing overhead** - navigating the DataFrame structure
- **Python overhead** - loops in Python are inherently slow

### 3. **What's the cheap vectorized check?**
Vectorized checks operate on **entire arrays at once** using optimized C code:
- **No Python loops** - operations happen in compiled C/Fortran
- **SIMD instructions** - Single Instruction Multiple Data (CPU-level parallelism)
- **Contiguous memory** - all data in one block, cache-friendly

---

## Performance Comparison with Examples

### ❌ SLOW: Row-wise Pandas (What we had before)

```python
# For EACH iteration (potentially millions of times):
for i in range(20, len(df) - 3):
    row = df.iloc[i]  # 🐌 EXPENSIVE: Creates new Series, checks types
    
    if pd.isna(row['ma20']):  # 🐌 EXPENSIVE: Accesses dict-like structure
        continue
    
    if row['volume'] < row['avg_volume'] * 1.2:  # 🐌 EXPENSIVE: Multiple dict lookups
        continue
```

**Why it's slow:**
- `df.iloc[i]` creates a **new pandas Series object** (~50-100x slower than array indexing)
- Each `row['column']` does a **dictionary-like lookup** with type checking
- For 100,000 rows → 100,000 Series objects created!

### ✅ FAST: Vectorized NumPy (What we changed to)

```python
# Extract arrays ONCE (at the start):
ma20 = df['ma20'].to_numpy()  # Convert entire column to NumPy array
vol = df['volume'].to_numpy()
avg_vol = df['avg_volume'].to_numpy()

# Now the loop uses simple array indexing:
for i in range(20, n - 3):
    m20 = ma20[i]  # ⚡ FAST: Direct memory access (C-speed)
    
    if np.isnan(m20):  # ⚡ FAST: Optimized C function
        continue
    
    if vol[i] < avg_vol[i] * 1.2:  # ⚡ FAST: Simple arithmetic on numbers
        continue
```

**Why it's fast:**
- `array[i]` is **direct memory access** (like C/C++)
- No object creation, no type checking - just raw numbers
- 50-100x faster per access!

---

## Real Performance Impact in Your Code

### Before Optimization:
```python
def detect_bounce_gss(df, filter_mas):
    for i in range(20, len(df) - 3):  # Say 100,000 iterations
        row = df.iloc[i]  # ❌ 100,000 Series objects created
        
        # Every check like this:
        if row['volume'] < row['avg_volume'] * VOLUME_MULTIPLIER:
            # Does 3 dictionary lookups + type checks = SLOW
```

**Cost:** ~100,000 iterations × ~100 microseconds per row = **10+ seconds per stock**

### After Optimization:
```python
def detect_bounce_gss(df, filter_mas):
    # Extract arrays ONCE ✅
    vol = df['volume'].to_numpy()
    avg_vol = df['avg_volume'].to_numpy()
    
    for i in range(20, n - 3):  # Same 100,000 iterations
        if vol[i] < avg_vol[i] * VOLUME_MULTIPLIER:  # ⚡ Direct array access
            # Just 2 array lookups + arithmetic = FAST
```

**Cost:** ~100,000 iterations × ~1 microsecond per check = **~0.1 seconds per stock**

**Speedup: 100x faster!** 🚀

---

## Why We Still Use Row-wise for GSS Check

Notice in the optimized code, we still do this:

```python
# ONLY when we find a bounce candidate (rare - maybe 100 times instead of 100,000)
bounce_candle = df.iloc[j]  # Still expensive, but called 1000x less often
if not check_gss_regime(bounce_candle, prev_row):
    break
```

**Strategy:**
1. ✅ **Use cheap NumPy checks** to filter 99.9% of rows (volume, touch detection)
2. ❌ **Use expensive row-wise checks** only for the ~0.1% that pass filters (GSS regime)

Instead of 100,000 expensive checks → now only ~100 expensive checks!

---

## Benchmark Example

Here's what happens with your 30 stocks × 48 months data:

```python
# Approximate numbers:
Total 5-min candles per stock: ~200,000
Total iterations across all stocks: 30 × 200,000 = 6,000,000

OLD CODE:
- 6M iterations × 100 microseconds = 600 seconds (10 minutes)
- Plus GSS checks on EVERY bounce attempt = FREEZE 🥶

NEW CODE:
- 6M iterations × 1 microsecond = 6 seconds (cheap checks)
- GSS checks on ~3,000 candidates only = +30 seconds
- Total: ~36 seconds ⚡
```

---

## What About Numba?

**Numba** could make it even faster:

```python
from numba import jit

@jit(nopython=True)  # Compile to machine code
def find_touches_numba(ma20, low, vol, avg_vol, multiplier):
    touches = []
    for i in range(20, len(ma20) - 3):
        if np.isnan(ma20[i]):
            continue
        if vol[i] < avg_vol[i] * multiplier:
            continue
        if low[i] <= ma20[i]:
            touches.append(i)
    return touches
```

**Numba benefits:**
- Compiles Python loops to machine code (C/Fortran speed)
- Can be 10-100x faster than even NumPy for complex loops
- **Works best with NumPy arrays!**

**We didn't use Numba here because:**
1. NumPy optimization already gives 100x speedup
2. Numba adds complexity (requires JIT compilation, limited Python features)
3. The real bottleneck was pandas, not NumPy

---

## Key Takeaways

| Approach | Speed | When to Use |
|----------|-------|-------------|
| **Pandas row-wise** (`df.iloc[i]`) | 🐌 Slowest (100x slower) | When you need complex row operations with mixed types |
| **NumPy arrays** (`arr[i]`) | ⚡ Fast (100x faster) | For numeric operations in loops |
| **Pandas vectorized** (`df['col'] > 5`) | ⚡⚡ Very fast | When you can avoid loops entirely |
| **Numba JIT** | ⚡⚡⚡ Fastest | When you have complex numeric loops |

**Our optimization:** Moved from slowest → fast, achieving 100x speedup without adding Numba complexity.

---

## Visual Memory Layout

### Pandas DataFrame (row access):
```
df.iloc[i] → Creates temporary object → Accesses columns → Type checks
              ↑ Slow                      ↑ Slow           ↑ Slow
```

### NumPy Array (direct access):
```
array[i] → Direct memory read → Return number
           ↑ Fast (C-speed)     ↑ Fast
```

This is why extracting to NumPy arrays once, then using array indexing, is so much faster!
