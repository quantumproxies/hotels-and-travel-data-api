"""The same stay, priced from several countries.

Currency is printed, never converted. If two markets quote different currencies,
they go in different columns — averaging them is how travel dashboards end up
claiming Japan is the cheapest destination on earth.

    python3 pos_check.py "Lisbon, Portugal" --countries us gb de br jp --nights 2
"""
from __future__ import annotations

import argparse
import statistics
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor

from travel import future_date, hotels, stay


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("location")
    ap.add_argument("--checkin", default=None)
    ap.add_argument("--nights", type=int, default=2)
    ap.add_argument("--adults", type=int, default=2)
    ap.add_argument("--countries", nargs="+", default=["us", "gb", "de", "br", "jp"])
    ap.add_argument("--currency", default=None, help="force one currency across all markets")
    ap.add_argument("--max", type=int, default=25)
    args = ap.parse_args()

    check_in, check_out = stay(args.checkin or future_date(30), args.nights)

    def probe(country: str):
        try:
            rows = hotels(args.location, check_in, check_out, adults=args.adults,
                          currency=args.currency, country=country, max_results=args.max)
        except RuntimeError as exc:
            return country, [], str(exc)
        return country, rows, None

    print(f"{args.location}  {check_in} → {check_out}  ({args.nights} nights)\n")
    print(f"{'market':<8}{'props':>7}{'low':>10}{'median':>10}{'cur':>6}")

    by_property: dict[str, dict[str, float]] = defaultdict(dict)
    with ThreadPoolExecutor(max_workers=3) as pool:
        for country, rows, error in pool.map(probe, args.countries):
            if error:
                print(f"{country:<8} !! {error}")
                continue
            priced = [r for r in rows if r.get("price_value")]
            if not priced:
                print(f"{country:<8}{len(rows):>7}   no priced properties")
                continue
            values = sorted(r["price_value"] for r in priced)
            currency = Counter(r.get("currency") for r in priced).most_common(1)[0][0] or "?"
            print(f"{country:<8}{len(priced):>7}{values[0]:>10,.0f}"
                  f"{statistics.median(values):>10,.0f}{str(currency):>6}")
            for row in priced:
                if row.get("name"):
                    by_property[row["name"]][country] = row["price_value"]

    everywhere = {name: prices for name, prices in by_property.items()
                  if len(prices) == len(args.countries)}
    if everywhere:
        print(f"\n{len(everywhere)} properties appeared in every market:")
        print(f"{'property':<38}" + "".join(f"{c.upper():>10}" for c in args.countries))
        for name, prices in list(everywhere.items())[:12]:
            print(f"{name[:37]:<38}" + "".join(f"{prices[c]:>10,.0f}" for c in args.countries))
        print("\nSame property, different points of sale. Currencies may differ — "
              "check the table above before reading these side by side.")


if __name__ == "__main__":
    main()
