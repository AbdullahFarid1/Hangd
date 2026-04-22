import re
import pandas as pd

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

PGN_FILES = [
    ("MAF13-white.pgn", "White"),  # you are White in this file
    ("MAF13-black.pgn", "Black"),  # you are Black in this file
]

OUTPUT_CSV = "opening_stats_by_color.csv"


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def parse_pgn_headers(pgn_text: str):
    """
    Very simple PGN header parser: returns a dict of tag -> value.
    Assumes headers appear as [Tag \"Value\"] lines at the top.
    """
    headers = {}
    for line in pgn_text.splitlines():
        line = line.strip()
        if not line.startswith("["):
            # headers finished
            break
        m = re.match(r'\[(\w+)\s+"(.*)"\]', line)
        if m:
            tag, val = m.group(1), m.group(2)
            headers[tag] = val
    return headers


def extract_opening_name(eco_url: str) -> str:
    """
    From ECOUrl like:
      https://www.chess.com/openings/Nimzowitsch-Larsen-Attack-Indian-Variation...4.f4-c5-5.Nf3-Nc6
    return:
      Nimzowitsch Larsen Attack Indian Variation
    """
    if not eco_url:
        return ""
    # Take everything after the last '/'
    last = eco_url.split("/")[-1]
    # Remove move suffix after '...' if present
    main = last.split("...")[0]
    # Replace '-' and URL spaces
    main = main.replace("-", " ").replace("%20", " ")
    return main.strip()


def result_from_perspective(result_tag: str, you_are: str) -> str:
    """
    Map PGN result + which side you are to 'win'/'loss'/'draw'/'other'.
    you_are is 'White' or 'Black'.
    """
    if result_tag == "1-0":
        return "win" if you_are == "White" else "loss"
    elif result_tag == "0-1":
        return "win" if you_are == "Black" else "loss"
    elif result_tag == "1/2-1/2":
        return "draw"
    else:
        return "other"


# --------------------------------------------------
# MAIN EXTRACTION
# --------------------------------------------------

records = []

for path, your_color in PGN_FILES:
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"PGN file not found: {path} (skipping)")
        continue

    # Split games by blank line between games; robust split uses '\n\n[' pattern
    # but we handle edge cases by using regex.
    games_raw = re.split(r'\n\n(?=\[Event )', content.strip())
    for game_txt in games_raw:
        if not game_txt.strip():
            continue

        headers = parse_pgn_headers(game_txt)
        eco = headers.get("ECO", "")
        eco_url = headers.get("ECOUrl", "")
        result_tag = headers.get("Result", "")

        opening_name = extract_opening_name(eco_url)
        perspective_result = result_from_perspective(result_tag, your_color)

        records.append({
            "file": path,
            "your_color": your_color,
            "eco": eco,
            "opening_name": opening_name,
            "raw_result": result_tag,
            "perspective_result": perspective_result,
        })

# Convert to DataFrame
df = pd.DataFrame(records)

# Filter valid results
valid = df[df["perspective_result"].isin(["win", "loss", "draw"])].copy()

# --------------------------------------------------
# STATS BY OPENING + COLOR
# --------------------------------------------------

group = (
    valid
    .groupby(["your_color", "opening_name", "eco", "perspective_result"])
    .size()
    .unstack(fill_value=0)
)

# Ensure columns exist
for col in ["win", "loss", "draw"]:
    if col not in group.columns:
        group[col] = 0

group["total"] = group[["win", "loss", "draw"]].sum(axis=1)
group["win_rate"] = group["win"] / group["total"].replace(0, pd.NA)

opening_stats = group.reset_index()

# Save to CSV
opening_stats.to_csv(OUTPUT_CSV, index=False)
print(f"Saved opening stats per color to: {OUTPUT_CSV}\n")

# Print a few lines for sanity check
print("=== SAMPLE OPENING STATS ===")
print(opening_stats.sort_values(["your_color", "total"], ascending=[True, False]).head(20))
