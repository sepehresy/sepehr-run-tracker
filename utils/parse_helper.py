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

        # First attempt: Try parsing with pandas using error_bad_lines=False for robustness
        try:
            # Try with newer pandas parameter first
            try:
                df = pd.read_csv(StringIO(csv_text), quotechar='"', skip_blank_lines=True, on_bad_lines='skip')
            except TypeError:
                # Fallback for older pandas versions
                df = pd.read_csv(StringIO(csv_text), quotechar='"', skip_blank_lines=True, error_bad_lines=False)
        except:
            # Second attempt: Use CSV reader with manual error handling
            print("[⚠️ Warning] Standard CSV parsing failed. Using robust fallback...")
            reader = csv.reader(StringIO(csv_text), delimiter=',', quotechar='"')
            rows = []
            
            for line_num, row in enumerate(reader, 1):
                try:
                    if line_num == 1:
                        # Header row - determine expected column count
                        header = row
                        expected_cols = len(header)
                        rows.append(row)
                    else:
                        # Data rows - handle extra columns by merging them into the last column
                        if len(row) > expected_cols:
                            # Too many columns - merge extra ones into the last column
                            fixed_row = row[:expected_cols-1] + [', '.join(row[expected_cols-1:])]
                            rows.append(fixed_row)
                        elif len(row) == expected_cols:
                            # Correct number of columns
                            rows.append(row)
                        elif len(row) < expected_cols:
                            # Too few columns - pad with empty strings
                            padded_row = row + [''] * (expected_cols - len(row))
                            rows.append(padded_row)
                except Exception as e:
                    print(f"[⚠️ Warning] Skipping malformed row {line_num}: {e}")
                    continue
            
            if len(rows) < 2:
                raise ValueError("No valid data rows found")
                
            df = pd.DataFrame(rows[1:], columns=rows[0])

        # If columns mismatch with expected, fix by padding/truncating
        if list(df.columns) != EXPECTED_COLUMNS:
            print("[⚠️ Warning] Column mismatch. Attempting to fix...")
            
            # Ensure we have the right number of columns
            if df.shape[1] > len(EXPECTED_COLUMNS):
                df = df.iloc[:, :len(EXPECTED_COLUMNS)]  # Trim extra cols
            
            # Set column names to expected ones
            df.columns = EXPECTED_COLUMNS[:df.shape[1]]

            # Add any missing columns as empty
            for col in EXPECTED_COLUMNS:
                if col not in df.columns:
                    df[col] = ""

            df = df[EXPECTED_COLUMNS]

        return df

    except Exception as e:
        print(f"[❌ Parse Error] Could not parse CSV: {e}")
        print(f"[💡 Debug] CSV content preview: {csv_text[:200]}...")
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

def debug_csv_structure(csv_text: str) -> None:
    """
    Debug helper to analyze CSV structure and identify parsing issues.
    """
    print("[🔍 CSV Debug] Analyzing CSV structure...")
    lines = csv_text.strip().split('\n')
    
    print(f"[📊 Stats] Total lines: {len(lines)}")
    
    if len(lines) > 0:
        header = lines[0]
        expected_cols = header.count(',') + 1
        print(f"[📋 Header] {header}")
        print(f"[🔢 Expected columns] {expected_cols}")
        
        # Check each line for column count mismatches
        for i, line in enumerate(lines[1:], 2):
            actual_cols = line.count(',') + 1
            if actual_cols != expected_cols:
                print(f"[⚠️ Line {i}] Expected {expected_cols} columns, found {actual_cols}")
                print(f"[📝 Content] {line}")
                
                # Try to identify where the extra comma might be
                if actual_cols > expected_cols:
                    # Split and show the problematic parts
                    parts = line.split(',')
                    print(f"[🔍 Fields] {parts}")

def load_csv_from_text(csv_raw):
    # Strip outer quotes if present
    if csv_raw.startswith('"') and csv_raw.endswith('"'):
        csv_raw = csv_raw[1:-1]
    # Replace any \n within fields (e.g., wrapped comments) if necessary
    csv_raw = csv_raw.replace('\\n', '\n')

    return pd.read_csv(io.StringIO(csv_raw))