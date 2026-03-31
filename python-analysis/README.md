# Python Analysis Module — CancerScreen AI

This module demonstrates Python skills as part of the final year project.

## What it does

- Extracts text from PDF cancer screening reports using `pdfplumber`
- Detects and analyzes medical values (PSA, CEA, Hemoglobin, WBC, etc.)
- Flags abnormal values as HIGH / LOW / NORMAL
- Assesses risk level using keyword analysis
- Generates a visual chart (bar chart + pie chart) using `matplotlib`
- Calls OpenRouter AI API for plain-language explanation
- Exports a formatted PDF report using `reportlab`

## Setup

```bash
cd python-analysis
pip install -r requirements.txt
```

## Usage

**Run with demo data (no PDF needed):**
```bash
python report_analyzer.py --demo
```

**Run with a real PDF report:**
```bash
python report_analyzer.py --file "path/to/report.pdf"
```

**Run with Hindi explanation:**
```bash
python report_analyzer.py --file "report.pdf" --lang Hindi
```

**Skip AI call (offline mode):**
```bash
python report_analyzer.py --demo --no-ai
```

## Output files

| File | Description |
|---|---|
| `report_chart.png` | Visual chart of medical values |
| `analysis_report.pdf` | Full formatted PDF report |

## Python libraries used

| Library | Purpose |
|---|---|
| `pdfplumber` | Extract text from PDF files |
| `matplotlib` | Generate bar and pie charts |
| `reportlab` | Create formatted PDF reports |
| `requests` | Call OpenRouter AI API |
| `python-dotenv` | Load API key from .env file |
| `colorama` | Colored terminal output |
| `re` | Regex to extract medical values |
| `pandas` | Data handling |

## Note

The `.env` file in the `backend/` folder is automatically used.
Make sure `MEDGEMMA_API_KEY` is set with your OpenRouter API key.
