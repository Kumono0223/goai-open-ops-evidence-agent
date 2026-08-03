from __future__ import annotations

import argparse
import json

from .analyzer import analyze_csv, profile_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline CSV productivity analytics")
    parser.add_argument("--csv", required=True, help="path to a local CSV file")
    parser.add_argument("--query", default="概览数据", help="natural-language intent")
    parser.add_argument("--profile", action="store_true", help="return schema profile instead of analysis")
    args = parser.parse_args()
    result = profile_csv(args.csv) if args.profile else analyze_csv(args.csv, args.query)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

