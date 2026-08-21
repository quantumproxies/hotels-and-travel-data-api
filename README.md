# Hotels & travel data API — rates by date, market and currency

The [`hotels` collector](https://quanticdata.io/collectors/google-hotels-api/) takes a
destination and a stay and returns properties as rows: name, price (text **and** `price_value`),
currency, `total_price`, rating, review count, the dates the price applies to, property type,
amenities, link and thumbnail. **$0.002 per property**, up to the collector's cap per run.

Travel pricing is the most geo- and time-sensitive data on the web, which makes it the best
example of why exit country and collection timestamp belong in every row.

```bash
pip install requests
export QUANTICDATA_API_KEY=qd_live_your_key_here

python3 rates.py "Lisbon, Portugal" --checkin 2026-10-14 --nights 2 --out lisbon.csv
python3 rate_calendar.py "Lisbon, Portugal" --weeks 8 --nights 2    # price by arrival date
python3 pos_check.py "Lisbon, Portugal" --countries us gb de br jp  # point-of-sale pricing
```

## Files

| File | What it does |
|---|---|
| [`travel.py`](travel.py) | the collector call + date helpers |
| [`rates.py`](rates.py) | one destination and stay → CSV, with the price distribution |
| [`rate_calendar.py`](rate_calendar.py) | the same stay length across N arrival dates — a seasonality curve |
| [`pos_check.py`](pos_check.py) | the same stay priced from several countries |

## Input

| Field | Notes |
|---|---|
| `location` | destination — city, region, or a specific area |
| `check_in_date` / `check_out_date` | `YYYY-MM-DD`; both required, and both must be in the future |
| `adults` | occupancy — changes the price, not just the filter |
| `currency` | ISO code; ask for the one you intend to report in |
| `country`, `lang` | point of sale and language |
| `max_results` | properties to deliver |

## Output row

```jsonc
{ "rank": 1, "name": "Hotel Example Lisboa",
  "price": "€142", "price_value": 142, "currency": "EUR",
  "total_price": "€284",
  "rating": 4.5, "reviews": 1820,
  "dates": "Oct 14 – Oct 16",
  "property_type": "Hotel",
  "amenities": ["Free Wi-Fi", "Pool", "Breakfast"],
  "link": "https://…", "thumbnail": "https://…",
  "check_in_date": "2026-10-14", "check_out_date": "2026-10-16" }
```

`price` is the nightly rate as displayed, `total_price` the whole stay. Which one a property
shows varies, so always report which you used — `rates.py` prints both and prefers `price_value`
for comparisons.

## Three ways travel data goes wrong

**Dates in the past.** The collector needs future dates. `travel.py` has a `future_date()` helper
so scheduled jobs never quietly start requesting yesterday.

**Point of sale.** A hotel priced from a US IP, a UK IP and a Brazilian IP can differ by more
than a rounding error — currency, tax display, and genuine market pricing all move. `pos_check.py`
shows the spread for a given stay; do not average across it.

**Comparing across stay lengths.** A two-night rate is not half a four-night rate: minimum-stay
rules and weekend pricing break the arithmetic. Keep `nights` fixed within any comparison, which
is what `rate_calendar.py` does.

## Related

- [Google Hotels API](https://quanticdata.io/collectors/google-hotels-api/) · [All collectors](https://quanticdata.io/collectors/) · [SERP API](https://quanticdata.io/serp-api/)
- [Market research data](https://quanticdata.io/market-research-data/) · [Competitor price monitoring](https://quanticdata.io/competitor-price-monitoring/)
- [Documentation](https://quanticdata.io/docs/)

MIT licensed.
