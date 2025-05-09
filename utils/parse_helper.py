import re
import io
import pandas as pd
import csv

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
    # Clean up surrounding quotes if present
    csv_raw = csv_raw.strip()
    if csv_raw.startswith('"') and csv_raw.endswith('"'):
        csv_raw = csv_raw[1:-1]
    csv_raw = csv_raw.replace("\\n", "\n")

    # Use csv reader to avoid comma-in-field issues
    try:
        reader = csv.reader(io.StringIO(csv_raw))
        rows = list(reader)

        # Check for consistent number of columns
        header = rows[0]
        data = [row for row in rows[1:] if len(row) == len(header)]

        df = pd.DataFrame(data, columns=header)
        return df
    except Exception as e:
        print("CSV parsing failed:", e)
        return None
    

def load_csv_from_text(csv_raw):
    # Strip outer quotes if present
    if csv_raw.startswith('"') and csv_raw.endswith('"'):
        csv_raw = csv_raw[1:-1]
    # Replace any \n within fields (e.g., wrapped comments) if necessary
    csv_raw = csv_raw.replace('\\n', '\n')

    return pd.read_csv(io.StringIO(csv_raw))