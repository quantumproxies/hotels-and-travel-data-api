"""One destination, one stay, one CSV.

    python3 rates.py "Lisbon, Portugal" --checkin 2026-10-14 --nights 2 --currency EUR
"""
from __future__ import annotations

import argparse
import csv
import statistics
from collections import Counter

from travel import future_date, hotels, stay

FIELDS = ["rank", "name", "property_type", "rating", "reviews", "price", "price_value",
          "total_price", "currency", "dates", "check_in_date", "check_out_date",
          "amenities", "link"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("location")
    ap.add_argument("--checkin", default=None, help="YYYY-MM-DD (default: 30 days out)")
    ap.add_argument("--nights", type=int, default=2)
    ap.add_argument("--adults", type=int, default=2)
    ap.add_argument("--currency", default=None)
    ap.add_argument("--country", default="us")
    ap.add_argument("--max", type=int, default=30)
    ap.add_argument("--out", default="hotels.csv")
    args = ap.parse_args()

    check_in, check_out = stay(args.checkin or future_date(30), args.nights)
    rows = hotels(args.location, check_in, check_out, adults=args.adults,
                  currency=args.currency, country=args.country, max_results=args.max)

    for row in rows:
        row["amenities"] = "; ".join(row.get("amenities") or [])

    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    priced = [r for r in rows if r.get("price_value")]
    print(f"{len(rows)} properties in {args.location}, "
          f"{check_in} → {check_out} ({args.nights} nights, {args.adults} adults), "
          f"priced from {args.country.upper()} → {args.out}\n")

    if priced:
        values = sorted(r["price_value"] for r in priced)
        currency = Counter(r.get("currency") for r in priced).most_common(1)[0][0]
        print(f"nightly {values[0]:,.0f} … {values[-1]:,.0f} {currency}   "
              f"median {statistics.median(values):,.0f}")

    print("\nby rating, then price")
    for row in sorted(rows, key=lambda r: (-(r.get("rating") or 0), r.get("price_value") or 1e9))[:15]:
        print(f"  {str(row.get('rating') or '-'):>4}★ ({(row.get('reviews') or 0):>5})  "
              f"{str(row.get('price') or '-'):>9}  "
              f"{str(row.get('property_type') or '')[:14]:<15}{(row.get('name') or '')[:40]}")

    print("\nproperty types")
    for kind, n in Counter(r.get("property_type") for r in rows).most_common(6):
        print(f"  {n:>3}  {kind}")


if __name__ == "__main__":
    main()
