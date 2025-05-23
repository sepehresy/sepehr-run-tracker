import re
import io
import pandas as pd
import csv
from io import StringIO


def parse_markdown_plan_table(md_text):
    """Parse a markdown table string into a pandas DataFrame."""
    table_lines = [line for line in md_text.splitlines() if line.strip().startswith('|') and line.strip().endswith('|')]
    table_lines = [line for line in table_lines if not re.match(r"^\|[\s\-\|]+\|$", line)]
    if not table_lines:
        return None
    header_line = table_lines[0]
    expected_cols = len(header_line.strip().strip('|').split('|'))
    split_lines = []
    for line in table_lines:
        raw_cells = [cell.strip() for cell in re.split(r'\s*\|\s*', line.strip())[1:-1]]
        if len(raw_cells) > expected_cols:
            fixed_row = raw_cells[:expected_cols-1] + [' | '.join(raw_cells[expected_cols-1:])]
            split_lines.append(fixed_row)
        elif len(raw_cells) == expected_cols:
            split_lines.append(raw_cells)
        else:
            continue
    table_str = '\n'.join([','.join(row) for row in split_lines])
    df = pd.read_csv(io.StringIO(table_str), skipinitialspace=True)
 
    return df


def parse_csv_plan_table(csv_raw):
    """Parse a raw CSV training-plan string into a DataFrame, merging multiline quoted rows."""
    # Prepare raw text
    text = csv_raw.strip()
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1]
    text = text.replace('\\n', '\n')
    lines = text.split('\n')
    if len(lines) < 2:
        return None
    # Determine header and expected columns
    header = lines[0]
    expected_cols = header.count(',') + 1
    # Reconstruct records, merging lines with unclosed quotes
    records = []
    i = 1
    while i < len(lines):
        line = lines[i]
        # if odd count of quotes, merge subsequent lines until balanced
        if line.count('"') % 2 != 0:
            while line.count('"') % 2 != 0 and i + 1 < len(lines):
                i += 1
                line += '\n' + lines[i]
        records.append(line)
        i += 1
    # Combine header and records
    csv_text = '\n'.join([header] + records)
    # Parse with pandas python engine
    try:
        return pd.read_csv(io.StringIO(csv_text), quotechar='"', skipinitialspace=True, engine='python')
    except Exception as e:
        print('Fallback pandas python engine failed:', e)
    # Final fallback: csv.reader merging extra fields into last column
    try:
        reader = csv.reader(io.StringIO(csv_text), delimiter=',', quotechar='"', skipinitialspace=True)
        rows = list(reader)
        hdr = rows[0]
        data = []
        for r in rows[1:]:
            if len(r) > len(hdr):
                r = r[:len(hdr)-1] + [','.join(r[len(hdr)-1:])]
            if len(r) == len(hdr):
                data.append(r)
        return pd.DataFrame(data, columns=hdr)
    except Exception as e:
        print('CSV final fallback failed:', e)
        return None
    

EXPECTED_COLUMNS = [
    "Week", "Start Date", 
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday", "Total", "Comment"
]

def parse_training_plan(csv_text: str) -> pd.DataFrame:
    """
    Parse a training plan CSV string and apply fallback handling:
    - Trims whitespace
    - Ignores malformed rows
    - Warns if columns mismatch
    - Fills missing columns with empty values
    """
    try:
        csv_text = csv_text.strip().replace('\r\n', '\n').replace('\r', '\n')

        # Try parsing strictly first
        df = pd.read_csv(StringIO(csv_text), quotechar='"', skip_blank_lines=True)

        # If columns mismatch, fix by padding/truncating
        if list(df.columns) != EXPECTED_COLUMNS:
            print("[⚠️ Warning] Column mismatch. Attempting to fix...")
            df = df.iloc[:, :len(EXPECTED_COLUMNS)]  # Trim extra cols
            df.columns = EXPECTED_COLUMNS[:df.shape[1]]  # Assign expected headers

            # Add any missing columns as empty
            for col in EXPECTED_COLUMNS:
                if col not in df.columns:
                    df[col] = ""

            df = df[EXPECTED_COLUMNS]

        return df

    except Exception as e:
        print(f"[❌ Parse Error] Could not parse CSV: {e}")
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

def load_csv_from_text(csv_raw):
    # Strip outer quotes if present
    if csv_raw.startswith('"') and csv_raw.endswith('"'):
        csv_raw = csv_raw[1:-1]
    # Replace any \n within fields (e.g., wrapped comments) if necessary
    csv_raw = csv_raw.replace('\\n', '\n')

    return pd.read_csv(io.StringIO(csv_raw))