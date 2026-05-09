"""Convert CSV stdin to tab-delimited stdout."""

import csv
import sys


def main() -> None:
    """Write stdin CSV rows to stdout as TSV rows."""
    reader = csv.reader(sys.stdin)
    writer = csv.writer(sys.stdout, dialect="excel-tab", lineterminator="\n")

    try:
        for row in reader:
            writer.writerow(row)
    except BrokenPipeError:
        sys.stdout.close()


if __name__ == "__main__":  # pragma: no cover
    main()
