# Quotex Vision AI — NextGen 4.0 Trusted

## The purpose of this version

The system is designed to make the computer's reasoning auditable while the
chart is moving.

### What is always visible

- One box around every detected candle.
- Detection confidence for every candle.
- The latest/rightmost candle is highlighted as CURRENT.
- Current candle direction: BULL or BEAR.
- Current candle time window.
- Seconds remaining in that candle.
- Explicit prediction window.
- Explicit UP / DOWN probabilities.
- Confidence and layer agreement.
- Decision audit showing the individual analysis layers.
- NO TRADE reasons when a gate fails.

## Prediction meaning

When the selected window is 30 seconds:

NEXT 30s: UP

means:

> The model estimates that the next 30-second window is more likely to finish
> above the current visible reference price than below it.

It does NOT mean a guaranteed exact future price.

### Time source

The app uses the local PC clock as its candle-window clock.

Because a screen-only application does not have access to Quotex's private
server clock, the app includes a manual clock offset. Use it to synchronize the
displayed candle boundaries with the visible chart timer.

## Exact numeric future price

A screen-only reader can estimate direction and normalized movement, but an exact
future numeric price requires trustworthy price-scale reconstruction. This
version therefore does NOT invent a future numeric quote.

## Data honesty

True broker volume and genuine higher-timeframe data are not available from a
single visible chart ROI. They remain explicitly unavailable rather than
fabricated.

## Run

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

For the packaged Windows installer, use the GitHub Actions installer artifact.


## 4.0.1 packaging fix
PyInstaller 6 onedir builds may place bundled data files under `_internal`. The application now searches both the bundle root and `_internal`, and the CI verification checks both locations.
