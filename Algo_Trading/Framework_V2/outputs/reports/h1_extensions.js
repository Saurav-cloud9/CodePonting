// h1_extensions.js — persistent H1 add-ons
// This file is NEVER overwritten by build_html1.py.
// All H1 feature installations go here.
// Loaded after the main H1 script on every page load.

// ── Crosshair Axis Labels ──────────────────────────────────────
// Adds a teal price badge on the right Y-axis and a time badge
// on the bottom X-axis that track the cursor position.
// Uses globals from main script: candles, zoomStart, zoomEnd,
// W, H, plotW, plotH, PAD, isPanning, priceOffset, timeLabel()
(function () {
    function init() {
        const chartArea = document.getElementById('chartArea');
        if (!chartArea) { setTimeout(init, 100); return; }

        // Y-axis price badge
        const priceLabel = document.createElement('div');
        priceLabel.id = 'axisLabelY';
        priceLabel.style.cssText = [
            'position:absolute',
            'background:#14b8a6',
            'color:#0a1628',
            'font-size:10px',
            'font-family:"JetBrains Mono",monospace',
            'font-weight:600',
            'padding:1px 5px',
            'border-radius:2px',
            'pointer-events:none',
            'display:none',
            'transform:translateY(-50%)',
            'z-index:20',
            'white-space:nowrap'
        ].join(';');
        chartArea.appendChild(priceLabel);

        // X-axis time badge
        const timeAxisLabel = document.createElement('div');
        timeAxisLabel.id = 'axisLabelX';
        timeAxisLabel.style.cssText = [
            'position:absolute',
            'background:#14b8a6',
            'color:#0a1628',
            'font-size:10px',
            'font-family:"JetBrains Mono",monospace',
            'font-weight:600',
            'padding:1px 5px',
            'border-radius:2px',
            'pointer-events:none',
            'display:none',
            'transform:translateX(-50%)',
            'z-index:20',
            'white-space:nowrap'
        ].join(';');
        chartArea.appendChild(timeAxisLabel);

        function hideLabels() {
            priceLabel.style.display = 'none';
            timeAxisLabel.style.display = 'none';
        }

        // Helper: recompute lo/hi matching draw() exactly, including priceOffset
        function getLoHi() {
            const viewCandles = candles.slice(zoomStart, zoomEnd);
            let lo = Infinity, hi = -Infinity;
            viewCandles.forEach(function (c) {
                if (c.l < lo) lo = c.l;
                if (c.h > hi) hi = c.h;
                if (c.ma && c.ma < lo) lo = c.ma;
                if (c.ma && c.ma > hi) hi = c.ma;
            });
            const margin = (hi - lo) * 0.08;
            lo -= margin; hi += margin;
            // Apply same offset as draw()
            const offset = (typeof priceOffset !== 'undefined') ? priceOffset : 0;
            lo -= offset; hi -= offset;
            return { lo, hi };
        }

        chartArea.addEventListener('mousemove', function (e) {
            if (typeof isPanning !== 'undefined' && isPanning) { hideLabels(); return; }
            if (!candles || !candles.length) return;
            if (typeof W === 'undefined' || !plotH || !plotW) return;

            const rect = chartArea.getBoundingClientRect();
            const mx = e.clientX - rect.left;
            const my = e.clientY - rect.top;

            if (mx < PAD.left || mx > W - PAD.right || my < PAD.top || my > PAD.top + plotH) {
                hideLabels(); return;
            }

            const { lo, hi } = getLoHi();

            // Price badge — right Y-axis
            const price = hi - (hi - lo) * (my - PAD.top) / plotH;
            priceLabel.textContent = price.toFixed(2);
            priceLabel.style.left = (W - PAD.right) + 'px';
            priceLabel.style.top = my + 'px';
            priceLabel.style.display = 'block';

            // Time badge — bottom X-axis
            const n = zoomEnd - zoomStart;
            const cw = plotW / n;
            const idx = Math.floor((mx - PAD.left) / cw);
            if (idx >= 0 && idx < n) {
                const fullIdx = zoomStart + idx;
                const cx = PAD.left + idx * cw + cw / 2;
                timeAxisLabel.textContent = timeLabel(fullIdx);
                timeAxisLabel.style.left = cx + 'px';
                timeAxisLabel.style.top = (H - PAD.bottom / 2) + 'px';
                timeAxisLabel.style.display = 'block';
            }
        });

        chartArea.addEventListener('mouseleave', hideLabels);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

// ── Vertical Panning ───────────────────────────────────────────
// Drag up/down on the price plot to shift the price range.
// Uses globals: priceOffset, plotH, plotW, W, H, PAD, isPanning, draw()
// Issue fixes applied:
//   #1 — getLoHi() in axis labels already subtracts priceOffset
//   #2 — gated to price-plot region only (y < H, within PAD bounds)
//   #3 — panStartRange captured at mousedown, held constant during drag
//   #4 — priceOffset reset handled in build_html1.py (loadDay + resetZoom)
//   #5 — absolute formula: priceOffset = panStartOffset + delta (never cumulative)
(function () {
    let panStartY = 0;
    let panStartOffset = 0;
    let panStartRange = 0;
    let vertPanActive = false;

    function init() {
        const chartArea = document.getElementById('chartArea');
        if (!chartArea) { setTimeout(init, 100); return; }

        chartArea.addEventListener('mousedown', function (e) {
            if (e.button !== 0) return;
            if (!candles || !candles.length) return;
            if (typeof W === 'undefined' || !plotH || !plotW) return;

            const rect = chartArea.getBoundingClientRect();
            const my = e.clientY - rect.top;

            // Issue #2: gate — only activate vertical pan in the price plot region
            if (my < PAD.top || my > PAD.top + plotH) return;

            // Issue #3: capture range at mousedown, held constant during drag
            const viewCandles = candles.slice(zoomStart, zoomEnd);
            let lo = Infinity, hi = -Infinity;
            viewCandles.forEach(function (c) {
                if (c.l < lo) lo = c.l;
                if (c.h > hi) hi = c.h;
                if (c.ma && c.ma < lo) lo = c.ma;
                if (c.ma && c.ma > hi) hi = c.ma;
            });
            const margin = (hi - lo) * 0.08;
            panStartRange = (hi - lo) + 2 * margin;  // price range in view

            panStartY = e.clientY;
            panStartOffset = (typeof priceOffset !== 'undefined') ? priceOffset : 0;
            vertPanActive = true;
        });

        document.addEventListener('mousemove', function (e) {
            if (!vertPanActive || !isPanning) return;
            if (!plotH || panStartRange === 0) return;

            // Issue #5: absolute formula — never cumulative
            const pixelDelta = panStartY - e.clientY;          // +ve = dragged up
            const priceDelta = pixelDelta * (panStartRange / plotH);
            priceOffset = panStartOffset + priceDelta;
            draw();
        });

        document.addEventListener('mouseup', function () {
            vertPanActive = false;
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
