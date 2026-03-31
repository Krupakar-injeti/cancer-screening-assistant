"""
CancerScreen AI — Python Report Analyzer
=========================================
Final Year Project — Python Analysis Module
Company: Python Fullstack

This script demonstrates Python skills by:
1. Extracting text from PDF cancer screening reports
2. Analyzing key medical values and flagging abnormal ones
3. Generating a structured visual summary chart
4. Exporting a formatted PDF analysis report
5. Calling the OpenRouter AI API for plain-language explanation

Usage:
    python report_analyzer.py --file "path/to/report.pdf"
    python report_analyzer.py --file "path/to/report.pdf" --lang Hindi
    python report_analyzer.py --demo
"""

import os
import re
import sys
import json
import argparse
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from colorama import Fore, Style, init

load_dotenv()
init(autoreset=True)

try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    CHART_SUPPORT = True
except ImportError:
    CHART_SUPPORT = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    PDF_EXPORT = True
except ImportError:
    PDF_EXPORT = False


MEDICAL_MARKERS = {
    'hemoglobin':     {'unit': 'g/dL',  'normal_min': 12.0, 'normal_max': 17.5, 'label': 'Hemoglobin'},
    'wbc':            {'unit': 'K/uL',  'normal_min': 4.5,  'normal_max': 11.0, 'label': 'WBC Count'},
    'platelets':      {'unit': 'K/uL',  'normal_min': 150,  'normal_max': 400,  'label': 'Platelets'},
    'psa':            {'unit': 'ng/mL', 'normal_min': 0.0,  'normal_max': 4.0,  'label': 'PSA'},
    'cea':            {'unit': 'ng/mL', 'normal_min': 0.0,  'normal_max': 5.0,  'label': 'CEA'},
    'ca125':          {'unit': 'U/mL',  'normal_min': 0.0,  'normal_max': 35.0, 'label': 'CA-125'},
    'ca199':          {'unit': 'U/mL',  'normal_min': 0.0,  'normal_max': 37.0, 'label': 'CA 19-9'},
    'afp':            {'unit': 'ng/mL', 'normal_min': 0.0,  'normal_max': 10.0, 'label': 'AFP'},
    'creatinine':     {'unit': 'mg/dL', 'normal_min': 0.6,  'normal_max': 1.2,  'label': 'Creatinine'},
    'glucose':        {'unit': 'mg/dL', 'normal_min': 70,   'normal_max': 100,  'label': 'Glucose'},
    'albumin':        {'unit': 'g/dL',  'normal_min': 3.5,  'normal_max': 5.0,  'label': 'Albumin'},
    'bilirubin':      {'unit': 'mg/dL', 'normal_min': 0.1,  'normal_max': 1.2,  'label': 'Bilirubin'},
}

CANCER_KEYWORDS = {
    'high_risk':   ['malignant', 'carcinoma', 'metastasis', 'tumor', 'invasive', 'stage iii', 'stage iv', 'aggressive'],
    'medium_risk': ['suspicious', 'abnormal', 'atypical', 'lesion', 'nodule', 'mass', 'elevated', 'stage i', 'stage ii'],
    'low_risk':    ['benign', 'normal', 'negative', 'clear', 'no evidence', 'unremarkable', 'within normal limits'],
}


def print_banner():
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}  🧬  CancerScreen AI — Python Analysis Module")
    print(f"{Fore.CYAN}  Final Year Project | Python Fullstack")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")


def extract_text_from_pdf(file_path: str) -> str:
    if not PDF_SUPPORT:
        print(f"{Fore.RED}✗ pdfplumber not installed. Run: pip install pdfplumber{Style.RESET_ALL}")
        return ""

    print(f"{Fore.YELLOW}→ Extracting text from PDF...{Style.RESET_ALL}")
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            total_pages = len(pdf.pages)
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                print(f"  Page {i+1}/{total_pages} processed", end='\r')
        print(f"\n{Fore.GREEN}✓ Extracted {len(text)} characters from {total_pages} page(s){Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}✗ Error reading PDF: {e}{Style.RESET_ALL}")
    return text


def extract_medical_values(text: str) -> list:
    print(f"\n{Fore.YELLOW}→ Analyzing medical values...{Style.RESET_ALL}")
    found_values = []
    text_lower = text.lower()

    for marker_key, marker_info in MEDICAL_MARKERS.items():
        pattern = rf'(?i){re.escape(marker_key)}[:\s]+([0-9]+\.?[0-9]*)'
        matches = re.findall(pattern, text_lower)

        if matches:
            try:
                value = float(matches[0])
                normal_min = marker_info['normal_min']
                normal_max = marker_info['normal_max']

                if value < normal_min:
                    status = 'LOW'
                    color = 'orange'
                elif value > normal_max:
                    status = 'HIGH'
                    color = 'red'
                else:
                    status = 'NORMAL'
                    color = 'green'

                found_values.append({
                    'name':       marker_info['label'],
                    'value':      value,
                    'unit':       marker_info['unit'],
                    'normal_min': normal_min,
                    'normal_max': normal_max,
                    'status':     status,
                    'color':      color
                })

                status_color = Fore.GREEN if status == 'NORMAL' else Fore.RED if status == 'HIGH' else Fore.YELLOW
                print(f"  {marker_info['label']:15} {value:8.2f} {marker_info['unit']:8} → {status_color}{status}{Style.RESET_ALL}")
            except ValueError:
                pass

    if not found_values:
        print(f"  {Fore.YELLOW}No standard numeric markers detected in this report{Style.RESET_ALL}")

    return found_values


def assess_risk_level(text: str) -> dict:
    print(f"\n{Fore.YELLOW}→ Assessing risk keywords...{Style.RESET_ALL}")
    text_lower = text.lower()
    found = {'high_risk': [], 'medium_risk': [], 'low_risk': []}

    for level, keywords in CANCER_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                found[level].append(kw)

    if found['high_risk']:
        overall = 'HIGH'
        overall_color = Fore.RED
    elif found['medium_risk']:
        overall = 'MEDIUM'
        overall_color = Fore.YELLOW
    else:
        overall = 'LOW'
        overall_color = Fore.GREEN

    print(f"  Risk level: {overall_color}{overall}{Style.RESET_ALL}")
    if found['high_risk']:
        print(f"  {Fore.RED}High-risk terms: {', '.join(found['high_risk'])}{Style.RESET_ALL}")
    if found['medium_risk']:
        print(f"  {Fore.YELLOW}Medium-risk terms: {', '.join(found['medium_risk'])}{Style.RESET_ALL}")
    if found['low_risk']:
        print(f"  {Fore.GREEN}Positive terms: {', '.join(found['low_risk'])}{Style.RESET_ALL}")

    return {'level': overall, 'found': found}


def generate_chart(values: list, output_path: str = 'report_chart.png') -> str:
    if not CHART_SUPPORT or not values:
        return ""

    print(f"\n{Fore.YELLOW}→ Generating analysis chart...{Style.RESET_ALL}")

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.patch.set_facecolor('#0d1117')

    ax1 = axes[0]
    ax1.set_facecolor('#161c1a')

    names  = [v['name']  for v in values]
    vals   = [v['value'] for v in values]
    colors_list = []
    for v in values:
        if v['status'] == 'NORMAL':
            colors_list.append('#1D9E75')
        elif v['status'] == 'HIGH':
            colors_list.append('#E24B4A')
        else:
            colors_list.append('#EF9F27')

    bars = ax1.barh(names, vals, color=colors_list, edgecolor='#2a3a2a', linewidth=0.5)

    for bar, v in zip(bars, values):
        ax1.axvline(x=v['normal_min'], color='#7fddba', linestyle='--', alpha=0.4, linewidth=0.8)
        ax1.axvline(x=v['normal_max'], color='#7fddba', linestyle='--', alpha=0.4, linewidth=0.8)
        ax1.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                 f"{v['value']} {v['unit']}", va='center', color='#e8ede9', fontsize=8)

    ax1.set_title('Medical Values Analysis', color='#7fddba', fontsize=13, pad=10)
    ax1.set_xlabel('Value', color='#8a9e91')
    ax1.tick_params(colors='#8a9e91')
    ax1.spines['bottom'].set_color('#2a3a2a')
    ax1.spines['left'].set_color('#2a3a2a')
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)

    normal_patch = mpatches.Patch(color='#1D9E75', label='Normal')
    high_patch   = mpatches.Patch(color='#E24B4A', label='High')
    low_patch    = mpatches.Patch(color='#EF9F27', label='Low')
    ax1.legend(handles=[normal_patch, high_patch, low_patch],
               facecolor='#161c1a', labelcolor='#e8ede9', fontsize=8)

    ax2 = axes[1]
    ax2.set_facecolor('#161c1a')

    status_counts = {'NORMAL': 0, 'HIGH': 0, 'LOW': 0}
    for v in values:
        status_counts[v['status']] += 1

    pie_labels = [k for k, v in status_counts.items() if v > 0]
    pie_values = [v for v in status_counts.values() if v > 0]
    pie_colors = []
    for label in pie_labels:
        if label == 'NORMAL':
            pie_colors.append('#1D9E75')
        elif label == 'HIGH':
            pie_colors.append('#E24B4A')
        else:
            pie_colors.append('#EF9F27')

    if pie_values:
        wedges, texts, autotexts = ax2.pie(
            pie_values,
            labels=pie_labels,
            colors=pie_colors,
            autopct='%1.0f%%',
            startangle=90,
            textprops={'color': '#e8ede9', 'fontsize': 10}
        )
        for at in autotexts:
            at.set_color('#0d1117')
            at.set_fontweight('bold')

    ax2.set_title('Status Distribution', color='#7fddba', fontsize=13, pad=10)

    plt.suptitle('CancerScreen AI — Python Analysis Report',
                 color='#7fddba', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()

    plt.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor='#0d1117', edgecolor='none')
    plt.close()

    print(f"{Fore.GREEN}✓ Chart saved: {output_path}{Style.RESET_ALL}")
    return output_path


def call_ai_api(text: str, language: str = 'English') -> str:
    api_key = os.getenv('MEDGEMMA_API_KEY')
    if not api_key:
        return "No API key found in .env file."

    print(f"\n{Fore.YELLOW}→ Calling AI for plain-language explanation ({language})...{Style.RESET_ALL}")

    prompt = f"""You are a compassionate medical assistant.
Analyze this cancer screening report and explain it in simple {language} that a patient can understand.
Keep it under 200 words. Highlight any concerning values. End with: "Please consult your doctor."

REPORT:
{text[:3000]}"""

    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'http://localhost:5173',
                'X-Title': 'CancerScreen AI Python'
            },
            json={
                'model': 'openrouter/auto',
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 400
            },
            timeout=30
        )
        data = response.json()
        return data['choices'][0]['message']['content']
    except Exception as e:
        return f"AI explanation unavailable: {str(e)}"


def export_pdf_report(file_name: str, values: list, risk: dict,
                      ai_explanation: str, chart_path: str,
                      output_path: str = 'analysis_report.pdf'):
    if not PDF_EXPORT:
        print(f"{Fore.YELLOW}⚠ reportlab not installed. Skipping PDF export.{Style.RESET_ALL}")
        return

    print(f"\n{Fore.YELLOW}→ Exporting PDF report...{Style.RESET_ALL}")

    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story  = []

    title_style = ParagraphStyle('Title', parent=styles['Title'],
                                  fontSize=20, textColor=colors.HexColor('#0F6E56'),
                                  spaceAfter=6, alignment=TA_CENTER)
    sub_style   = ParagraphStyle('Sub', parent=styles['Normal'],
                                  fontSize=10, textColor=colors.grey,
                                  spaceAfter=4, alignment=TA_CENTER)
    h2_style    = ParagraphStyle('H2', parent=styles['Heading2'],
                                  fontSize=13, textColor=colors.HexColor('#0F6E56'),
                                  spaceBefore=12, spaceAfter=6)
    body_style  = ParagraphStyle('Body', parent=styles['Normal'],
                                  fontSize=10, leading=16, spaceAfter=8)
    warn_style  = ParagraphStyle('Warn', parent=styles['Normal'],
                                  fontSize=9, textColor=colors.HexColor('#854F0B'),
                                  backColor=colors.HexColor('#FAEEDA'),
                                  borderPadding=8, spaceAfter=10)

    story.append(Paragraph('🧬 CancerScreen AI', title_style))
    story.append(Paragraph('Python Medical Report Analysis', sub_style))
    story.append(Paragraph(f'Generated: {datetime.now().strftime("%d %B %Y, %I:%M %p")}', sub_style))
    story.append(Paragraph(f'Source file: {file_name}', sub_style))
    story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#1D9E75'), spaceAfter=12))

    story.append(Paragraph('⚠ Medical Disclaimer', warn_style))
    story.append(Paragraph(
        'This is an AI-generated analysis for informational purposes only. '
        'It is NOT a substitute for professional medical advice. '
        'Always consult a qualified doctor or oncologist.',
        warn_style
    ))

    risk_color_map = {'HIGH': '#E24B4A', 'MEDIUM': '#EF9F27', 'LOW': '#1D9E75'}
    risk_color = risk_color_map.get(risk['level'], '#888')
    story.append(Paragraph('Risk Assessment', h2_style))
    risk_style = ParagraphStyle('Risk', parent=styles['Normal'],
                                 fontSize=14, fontName='Helvetica-Bold',
                                 textColor=colors.HexColor(risk_color), spaceAfter=8)
    story.append(Paragraph(f'Overall Risk Level: {risk["level"]}', risk_style))

    if values:
        story.append(Paragraph('Medical Values Analysis', h2_style))
        table_data = [['Marker', 'Value', 'Unit', 'Normal Range', 'Status']]
        for v in values:
            status_color = colors.HexColor('#1D9E75') if v['status'] == 'NORMAL' else \
                           colors.HexColor('#E24B4A') if v['status'] == 'HIGH' else \
                           colors.HexColor('#EF9F27')
            table_data.append([
                v['name'],
                str(v['value']),
                v['unit'],
                f"{v['normal_min']} – {v['normal_max']}",
                v['status']
            ])

        table = Table(table_data, colWidths=[4*cm, 2.5*cm, 2*cm, 4*cm, 2.5*cm])
        table_style_list = [
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F6E56')),
            ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
            ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0,0), (-1,-1), 9),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#F9F9F9'), colors.white]),
            ('GRID',       (0,0), (-1,-1), 0.3, colors.HexColor('#CCCCCC')),
            ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
            ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]
        for i, v in enumerate(values, start=1):
            sc = colors.HexColor('#1D9E75') if v['status'] == 'NORMAL' else \
                 colors.HexColor('#E24B4A') if v['status'] == 'HIGH' else \
                 colors.HexColor('#EF9F27')
            table_style_list.append(('TEXTCOLOR', (4,i), (4,i), sc))
            table_style_list.append(('FONTNAME',  (4,i), (4,i), 'Helvetica-Bold'))

        table.setStyle(TableStyle(table_style_list))
        story.append(table)
        story.append(Spacer(1, 12))

    if chart_path and Path(chart_path).exists():
        from reportlab.platypus import Image as RLImage
        story.append(Paragraph('Visual Analysis Chart', h2_style))
        story.append(RLImage(chart_path, width=16*cm, height=7*cm))
        story.append(Spacer(1, 12))

    story.append(Paragraph('AI Plain-Language Explanation', h2_style))
    story.append(Paragraph(ai_explanation.replace('\n', '<br/>'), body_style))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width='100%', thickness=0.5, color=colors.grey))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'],
                                   fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    story.append(Paragraph(
        'CancerScreen AI — Python Fullstack Final Year Project | '
        'This report is AI-generated and for educational purposes only.',
        footer_style
    ))

    doc.build(story)
    print(f"{Fore.GREEN}✓ PDF report saved: {output_path}{Style.RESET_ALL}")


def get_demo_text() -> str:
    return """
    PATIENT MEDICAL REPORT — CANCER SCREENING
    Date: 2024-03-15
    Patient: Demo Patient | Age: 45

    BLOOD TEST RESULTS:
    Hemoglobin: 10.2 g/dL (Low)
    WBC: 14.5 K/uL (High)
    Platelets: 180 K/uL
    PSA: 6.8 ng/mL (High)
    CEA: 8.2 ng/mL (High)
    CA125: 22.0 U/mL
    Creatinine: 1.0 mg/dL
    Glucose: 95 mg/dL
    AFP: 4.2 ng/mL
    Albumin: 3.8 g/dL

    FINDINGS:
    Suspicious nodule detected in right lung.
    Elevated PSA levels suggest further investigation needed.
    CEA elevated — possible colorectal involvement.
    Biopsy recommended for abnormal lesion.
    No evidence of distant metastasis at this stage.
    Stage I classification pending biopsy confirmation.
    """


def main():
    print_banner()

    parser = argparse.ArgumentParser(description='CancerScreen AI — Python Report Analyzer')
    parser.add_argument('--file',  type=str, help='Path to PDF report')
    parser.add_argument('--lang',  type=str, default='English', help='Language for AI explanation')
    parser.add_argument('--demo',  action='store_true', help='Run with demo data')
    parser.add_argument('--no-ai', action='store_true', help='Skip AI API call')
    args = parser.parse_args()

    if args.demo:
        print(f"{Fore.CYAN}Running in DEMO mode with sample report data{Style.RESET_ALL}\n")
        text = get_demo_text()
        source_name = 'demo_report.pdf'
    elif args.file:
        if not Path(args.file).exists():
            print(f"{Fore.RED}✗ File not found: {args.file}{Style.RESET_ALL}")
            sys.exit(1)
        text = extract_text_from_pdf(args.file)
        source_name = Path(args.file).name
        if not text:
            print(f"{Fore.RED}✗ Could not extract text from file{Style.RESET_ALL}")
            sys.exit(1)
    else:
        print(f"{Fore.YELLOW}No file specified. Running in demo mode.{Style.RESET_ALL}")
        print(f"Usage: python report_analyzer.py --file report.pdf")
        print(f"       python report_analyzer.py --demo\n")
        text = get_demo_text()
        source_name = 'demo_report.pdf'

    values      = extract_medical_values(text)
    risk        = assess_risk_level(text)
    chart_path  = generate_chart(values, 'report_chart.png')
    ai_text     = '' if args.no_ai else call_ai_api(text, args.lang)

    if ai_text:
        print(f"\n{Fore.CYAN}── AI Explanation ({args.lang}) ──{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{ai_text}{Style.RESET_ALL}")

    export_pdf_report(
        file_name=source_name,
        values=values,
        risk=risk,
        ai_explanation=ai_text or 'AI explanation skipped.',
        chart_path=chart_path,
        output_path='analysis_report.pdf'
    )

    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.GREEN}✅ Analysis complete!")
    print(f"{Fore.CYAN}   Chart  → report_chart.png")
    print(f"{Fore.CYAN}   Report → analysis_report.pdf")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")


if __name__ == '__main__':
    main()
