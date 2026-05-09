"""Tests for greptransactions helpers."""

from decimal import Decimal

import pytest

from greptransactions.__main__ import csv_to_tsv, parse_amount


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        ("35.99", Decimal("35.99")),
        ("$35.99", Decimal("35.99")),
        ("+ $7,500.00", Decimal("7500.00")),
        ("- $72.23", Decimal("-72.23")),
        ("-1,814.83", Decimal("-1814.83")),
    ],
)
def test_parse_amount_normalizes_supported_formats(
    amount: str,
    expected: Decimal,
) -> None:
    """Amount parsing should preserve signs while ignoring presentation marks."""
    assert parse_amount(amount) == expected


def test_csv_to_tsv_sorts_amounts_ascending() -> None:
    """Amount sorting should use numeric values, not amount display text."""
    csv_text = "\n".join(
        [
            "2025-01-01,Plain,35.99",
            '2025-01-02,Large deposit,"+ $7,500.00"',
            "2025-01-03,Withdrawal,- $72.23",
            '2025-01-04,Negative comma,"-1,814.83"',
            "2025-01-05,Currency,$35.99",
        ]
    )

    assert csv_to_tsv(csv_text, sort="amount") == (
        "2025-01-04\tNegative comma\t-1,814.83\n"
        "2025-01-03\tWithdrawal\t- $72.23\n"
        "2025-01-01\tPlain\t35.99\n"
        "2025-01-05\tCurrency\t$35.99\n"
        "2025-01-02\tLarge deposit\t+ $7,500.00\n"
    )


def test_csv_to_tsv_sorts_amounts_descending() -> None:
    """Reverse amount sorting should place larger numeric values first."""
    csv_text = "\n".join(
        [
            "2025-01-01,Plain,35.99",
            '2025-01-02,Large deposit,"+ $7,500.00"',
            "2025-01-03,Withdrawal,- $72.23",
        ]
    )

    assert csv_to_tsv(csv_text, sort="amount", reverse=True) == (
        "2025-01-02\tLarge deposit\t+ $7,500.00\n"
        "2025-01-01\tPlain\t35.99\n"
        "2025-01-03\tWithdrawal\t- $72.23\n"
    )


def test_csv_to_tsv_preserves_current_order_by_default() -> None:
    """Omitted sort should preserve the current date-like file order."""
    csv_text = "\n".join(
        [
            "2025-01-03,C,3.00",
            "2025-01-01,A,1.00",
            "2025-01-02,B,2.00",
        ]
    )

    assert csv_to_tsv(csv_text) == (
        "2025-01-03\tC\t3.00\n2025-01-01\tA\t1.00\n2025-01-02\tB\t2.00\n"
    )


def test_csv_to_tsv_sorts_by_date() -> None:
    """Date sorting should use the transaction date column."""
    csv_text = "\n".join(
        [
            "2025-01-03,C,3.00",
            "2025-01-01,A,1.00",
            "2025-01-02,B,2.00",
        ]
    )

    assert csv_to_tsv(csv_text, sort="date") == (
        "2025-01-01\tA\t1.00\n2025-01-02\tB\t2.00\n2025-01-03\tC\t3.00\n"
    )


def test_csv_to_tsv_sorts_by_description() -> None:
    """Description sorting should use the transaction description column."""
    csv_text = "\n".join(
        [
            "2025-01-01,Zebra,1.00",
            "2025-01-02,Apple,2.00",
            "2025-01-03,Middle,3.00",
        ]
    )

    assert csv_to_tsv(csv_text, sort="description") == (
        "2025-01-02\tApple\t2.00\n2025-01-03\tMiddle\t3.00\n2025-01-01\tZebra\t1.00\n"
    )


def test_csv_to_tsv_reverses_default_date_sort() -> None:
    """Reverse should flip the current date-like file order when sort is omitted."""
    csv_text = "\n".join(
        [
            "2025-01-01,A,1.00",
            "2025-01-02,B,2.00",
            "2025-01-03,C,3.00",
        ]
    )

    assert csv_to_tsv(csv_text, reverse=True) == (
        "2025-01-03\tC\t3.00\n2025-01-02\tB\t2.00\n2025-01-01\tA\t1.00\n"
    )
