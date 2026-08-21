"""The same stay length across many arrival dates — a seasonality curve.

Stay length is held constant so the numbers are comparable; only the arrival date
moves. The median across properties is the honest summary, because the cheapest
listing on any given week is often a different property.

    python3 rate_calendar.py "Lisbon, Portugal" --weeks 8 --nights 2 --currency EUR
"""
from __future__ import annotations

import argparse
import statistics
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

from travel import hotels, stay


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("location")
    ap.add_argument("--weeks", type=int, default=8, help="how many weekly arrival dates")
    ap.add_argument("--start-in", type=int, default=14, help="days from today for the first arrival")
    ap.add_argument("--nights", type=int, default=2)
    ap.add_argument("--adults", type=int, default=2)
    ap.add_argument("--currency", default=None)
    ap.add_argument("--country", default="us")
    ap.add_argument("--max", type=int, default=25)
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args()

    arrivals = [(date.today() + timedelta(days=args.start_in + 7 * w)).isoformat()
                for w in range(args.weeks)]

    def probe(arrival: str):
        check_in, check_out = stay(arrival, args.nights)
        try:
            rows = hotels(args.location, check_in, check_out, adults=args.adults,
                          currency=args.currency, country=args.country, max_results=args.max)
        except RuntimeError as exc:
            return arrival, None, str(exc)
        values = sorted(r["price_value"] for r in rows if r.get("price_value"))
        return arrival, values, None

    print(f"{args.location} — {args.nights} nights, {args.adults} adults, "
          f"priced from {args.country.upper()}\n")
    print(f"{'arrival':<13}{'props':>7}{'low':>9}{'median':>9}{'p75':>9}")

    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for arrival, values, error in pool.map(probe, arrivals):
            if error:
                print(f"{arrival:<13} !! {error}")
                continue
            if not values:
                print(f"{arrival:<13}{0:>7}   no priced properties")
                continue
            p75 = statistics.quantiles(values, n=4)[2] if len(values) >= 4 else values[-1]
            median = statistics.median(values)
            results.append((arrival, median))
            print(f"{arrival:<13}{len(values):>7}{values[0]:>9,.0f}{median:>9,.0f}{p75:>9,.0f}")

    if len(results) > 1:
        medians = [m for _, m in results]
        floor = min(medians)
        print("\nmedian nightly rate by arrival week")
        for arrival, median in results:
            bar = "#" * round(40 * median / max(medians))
            marker = "  ← cheapest" if median == floor else ""
            print(f"  {arrival}  {median:>8,.0f}  {bar}{marker}")
        print(f"\nspread {min(medians):,.0f} … {max(medians):,.0f} "
              f"({100 * (max(medians) / min(medians) - 1):.0f}% between the cheapest "
              "and dearest week)")


if __name__ == "__main__":
    main()
