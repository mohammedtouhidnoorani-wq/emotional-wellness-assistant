"""CSV Exporter module for the Trading Journey Database.

Generates RFC 4180-compliant CSV files from trade records and returns
them as downloadable Flask Response objects.
"""

import csv
import io
from datetime import date

from flask import Response


# Column headers for the CSV export
CSV_HEADERS = [
    'date', 'symbol', 'trade_type', 'entry_price', 'exit_price',
    'quantity', 'stop_loss', 'target', 'status', 'pnl',
    'strategy', 'notes', 'emotion_before', 'emotion_after'
]


def generate_csv_response(trades):
    """Generate a Flask Response containing CSV-formatted trade data.

    Args:
        trades: A list of Trade model instances to export.

    Returns:
        A Flask Response object with Content-Type text/csv and
        Content-Disposition set for file download.

    The CSV is RFC 4180 compliant:
    - Fields containing commas, double quotes, or newlines are enclosed
      in double quotes.
    - Internal double quotes are escaped by doubling them.
    - Date fields are formatted as ISO 8601 (YYYY-MM-DD).
    - Numeric fields have no rounding applied beyond stored precision.
    - An empty trade list returns headers only.
    """
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL, lineterminator='\r\n')

    # Write header row
    writer.writerow(CSV_HEADERS)

    # Write trade data rows
    for trade in trades:
        row = [
            _format_date(trade.date),
            _safe_str(trade.symbol),
            _safe_str(trade.trade_type),
            _format_numeric(trade.entry_price),
            _format_numeric(trade.exit_price),
            _format_numeric(trade.quantity),
            _format_numeric(trade.stop_loss),
            _format_numeric(trade.target),
            _safe_str(trade.status),
            _format_numeric(trade.pnl),
            _safe_str(trade.strategy),
            _safe_str(trade.notes),
            _safe_str(trade.emotion_before),
            _safe_str(trade.emotion_after),
        ]
        writer.writerow(row)

    csv_content = output.getvalue()
    output.close()

    # Build filename with today's date
    today = date.today().isoformat()
    filename = f'trading_journal_{today}.csv'

    response = Response(
        csv_content,
        mimetype='text/csv',
        headers={
            'Content-Type': 'text/csv',
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
    )

    return response


def _format_date(value):
    """Format a date value as ISO 8601 (YYYY-MM-DD).

    Returns empty string for None values.
    """
    if value is None:
        return ''
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    return str(value)


def _format_numeric(value):
    """Format a numeric value without rounding.

    Returns empty string for None values.
    Preserves the stored precision of the number.
    """
    if value is None:
        return ''
    return str(value)


def _safe_str(value):
    """Convert a value to string, returning empty string for None."""
    if value is None:
        return ''
    return str(value)