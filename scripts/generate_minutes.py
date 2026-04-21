#!/usr/bin/env python3
"""
Generate TCDD-style meeting minutes (.docx) from a JSON data file.

Uses the original template document as a base, unpacks it, replaces content
via XML manipulation, then repacks.

Usage:
    python generate_minutes.py --data meeting.json --template template.docx --output output.docx

The JSON schema is defined in references/data-schema.md
"""
import argparse
import json
import os
import re
import subprocess
import sys
import shutil
import uuid
import html
import zipfile
import tempfile

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPTS_DIR)


# ============================================================================
# TEMPLATE MARKERS
# ----------------------------------------------------------------------------
# Sablon (assets/template.docx) icindeki SABIT metinler — bu script onlari
# anchor (yer imi) olarak kullaniyor. Sablon guncellenirse (orn. yeni baslik,
# yeni ornek tarih/saat/yer/hazirlayan), bu sabitleri yeni sablondaki metne
# gore guncelle. Bu sabitlerin disinda kod icinde hardcoded anchor kullanma.
# ============================================================================
TEMPLATE_MARKERS = {
    # Toplanti basligi icinde gecen benzersiz bir substring.
    # Sablonda baslik birden fazla <w:r> run'ina bolunmus olabilir; bu substring
    # paragrafi bulmaya yarar, sonra tum paragraf yeniden yazilir.
    "title_anchor": "BVA_KP",

    # TARIH satirinin etiket hucresinin metni (I/i farki nedeniyle unicode).
    "date_label": "TAR\u0130H",

    # SAAT hucresindeki mevcut ornek deger (dogrudan yerinde degisir).
    "time_value": "10.00",

    # YER hucresindeki mevcut ornek deger (dogrudan yerinde degisir).
    "location_value": "Online Toplant\u0131-Teams",

    # Hazirlayan hucresinde gecen mevcut isim (dogrudan yerinde degisir).
    # Sablon guncellenince bu da guncellenmelidir — aksi halde prepared_by
    # atamasi sessizce basarisiz olur. Kod, outer tablonun son cell'indeki
    # bu ismi arar; ayni ad katilimcilar tablosunda da gecse lookahead
    # sayesinde sadece Hazirlayan hedeflenir.
    "prepared_by_value": "Kerem T\u00fcrky\u0131lmaz",
}


def escape_xml(text):
    """Escape text for safe XML insertion, preserving Turkish characters as UTF-8."""
    if text is None:
        return ""
    text = str(text)
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    # Smart quotes for apostrophes
    text = text.replace("'", "&#x2019;")
    return text


def gen_para_id():
    """Generate a random 8-char hex paraId that is < 0x7FFFFFFF."""
    import random
    val = random.randint(0x00000001, 0x7FFFFFFE)
    return f"{val:08X}"


def gen_text_id():
    """Generate a random 8-char hex textId that is < 0x7FFFFFFF."""
    import random
    val = random.randint(0x00000001, 0x7FFFFFFE)
    return f"{val:08X}"


RUN_PROPS = """<w:rPr>
                <w:rFonts w:ascii="Tahoma" w:hAnsi="Tahoma" w:cs="Tahoma"/>
                <w:smallCaps w:val="0"/>
              </w:rPr>"""

RUN_PROPS_BOLD = """<w:rPr>
                <w:rFonts w:ascii="Tahoma" w:hAnsi="Tahoma" w:cs="Tahoma"/>
                <w:b/>
                <w:bCs/>
                <w:smallCaps w:val="0"/>
              </w:rPr>"""

CELL_RUN_PROPS = """<w:rPr>
                      <w:rFonts w:ascii="Tahoma" w:hAnsi="Tahoma" w:cs="Tahoma"/>
                      <w:smallCaps w:val="0"/>
                    </w:rPr>"""


def make_paragraph(text, bold=False, num_id=None, para_id=None, text_id=None):
    """Create a simple paragraph XML element."""
    pid = para_id or gen_para_id()
    tid = text_id or gen_text_id()
    rpr = RUN_PROPS_BOLD if bold else RUN_PROPS

    ppr_parts = []
    if num_id is not None:
        ppr_parts.append(f"""<w:numPr>
                <w:ilvl w:val="0"/>
                <w:numId w:val="{num_id}"/>
              </w:numPr>""")
    ppr_parts.append(
        '<w:spacing w:before="100" w:beforeAutospacing="1" w:after="100" w:afterAutospacing="1"/>'
    )
    if bold and num_id is None:
        ppr_parts.append('<w:outlineLvl w:val="1"/>')

    ppr_rpr = RUN_PROPS_BOLD if bold else RUN_PROPS
    ppr_content = "\n              ".join(ppr_parts)

    xml_space = ' xml:space="preserve"' if text.startswith(" ") or text.endswith(" ") else ""

    return f"""          <w:p w14:paraId="{pid}" w14:textId="{tid}" w:rsidR="00AA0001" w:rsidRDefault="00AA0001" w:rsidP="00AA0001">
            <w:pPr>
              {ppr_content}
              {ppr_rpr}
            </w:pPr>
            <w:r>
              {rpr}
              <w:t{xml_space}>{escape_xml(text)}</w:t>
            </w:r>
          </w:p>"""


def build_gorusulen_konular(topics):
    """Build XML for the GÖRÜŞÜLEN KONULAR section from topic list."""
    # Each topic: { "title": "...", "items": ["...", "..."] }
    # We use numId 28, 30, 31, 32 cycling for different topic bullet groups
    num_ids = [28, 30, 31, 32, 33, 34, 35, 36]
    paragraphs = []

    for i, topic in enumerate(topics):
        num = i + 1
        title = f"{num}. {topic['title']}"
        paragraphs.append(make_paragraph(title, bold=True))

        nid = num_ids[i % len(num_ids)]
        for item in topic.get("items", []):
            paragraphs.append(make_paragraph(item, bold=False, num_id=nid))

    return "\n".join(paragraphs)


def build_action_row(no, text, responsible, planned_date="", odd_band=False):
    """Build a single action item table row."""
    pid1 = gen_para_id()
    pid2 = gen_para_id()
    pid3 = gen_para_id()
    pid4 = gen_para_id()

    cnf_row = ""
    cnf_cell = ""
    if odd_band:
        cnf_row = """<w:trPr>
                <w:cnfStyle w:val="000000100000" w:firstRow="0" w:lastRow="0" w:firstColumn="0" w:lastColumn="0" w:oddVBand="0" w:evenVBand="0" w:oddHBand="1" w:evenHBand="0" w:firstRowFirstColumn="0" w:firstRowLastColumn="0" w:lastRowFirstColumn="0" w:lastRowLastColumn="0"/>
              </w:trPr>"""
        cnf_cell = """<w:cnfStyle w:val="000000100000" w:firstRow="0" w:lastRow="0" w:firstColumn="0" w:lastColumn="0" w:oddVBand="0" w:evenVBand="0" w:oddHBand="1" w:evenHBand="0" w:firstRowFirstColumn="0" w:firstRowLastColumn="0" w:lastRowFirstColumn="0" w:lastRowLastColumn="0"/>"""
    else:
        cnf_cell = """<w:cnfStyle w:val="000000000000" w:firstRow="0" w:lastRow="0" w:firstColumn="0" w:lastColumn="0" w:oddVBand="0" w:evenVBand="0" w:oddHBand="0" w:evenHBand="0" w:firstRowFirstColumn="0" w:firstRowLastColumn="0" w:lastRowFirstColumn="0" w:lastRowLastColumn="0"/>"""

    return f"""            <w:tr w:rsidR="00AA0001" w:rsidRPr="008B0C06" w14:paraId="{gen_para_id()}" w14:textId="77777777" w:rsidTr="13CB246E">
              {cnf_row}
              <w:tc>
                <w:tcPr>
                  <w:cnfStyle w:val="001000000000" w:firstRow="0" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" w:oddVBand="0" w:evenVBand="0" w:oddHBand="0" w:evenHBand="0" w:firstRowFirstColumn="0" w:firstRowLastColumn="0" w:lastRowFirstColumn="0" w:lastRowLastColumn="0"/>
                  <w:tcW w:w="650" w:type="dxa"/>
                  <w:vAlign w:val="center"/>
                </w:tcPr>
                <w:p w14:paraId="{pid1}" w14:textId="{gen_text_id()}" w:rsidR="00AA0001" w:rsidRDefault="00AA0001" w:rsidP="00AA0001">
                  <w:pPr>
                    <w:jc w:val="center"/>
                    {CELL_RUN_PROPS}
                  </w:pPr>
                  <w:r>
                    {CELL_RUN_PROPS}
                    <w:t>{escape_xml(no)}</w:t>
                  </w:r>
                </w:p>
              </w:tc>
              <w:tc>
                <w:tcPr>
                  <w:tcW w:w="5535" w:type="dxa"/>
                  <w:vAlign w:val="center"/>
                </w:tcPr>
                <w:p w14:paraId="{pid2}" w14:textId="{gen_text_id()}" w:rsidR="00AA0001" w:rsidRDefault="00AA0001" w:rsidP="00AA0001">
                  <w:pPr>
                    <w:jc w:val="both"/>
                    {cnf_cell}
                    {CELL_RUN_PROPS}
                  </w:pPr>
                  <w:r>
                    {CELL_RUN_PROPS}
                    <w:t>{escape_xml(text)}</w:t>
                  </w:r>
                </w:p>
              </w:tc>
              <w:tc>
                <w:tcPr>
                  <w:tcW w:w="2109" w:type="dxa"/>
                  <w:vAlign w:val="center"/>
                </w:tcPr>
                <w:p w14:paraId="{pid3}" w14:textId="{gen_text_id()}" w:rsidR="00AA0001" w:rsidRDefault="00AA0001" w:rsidP="00AA0001">
                  <w:pPr>
                    {cnf_cell}
                    {CELL_RUN_PROPS}
                  </w:pPr>
                  <w:r>
                    {CELL_RUN_PROPS}
                    <w:t>{escape_xml(responsible)}</w:t>
                  </w:r>
                </w:p>
              </w:tc>
              <w:tc>
                <w:tcPr>
                  <w:tcW w:w="1970" w:type="dxa"/>
                  <w:vAlign w:val="center"/>
                </w:tcPr>
                <w:p w14:paraId="{pid4}" w14:textId="{gen_text_id()}" w:rsidR="00AA0001" w:rsidRDefault="00AA0001" w:rsidP="00AA0001">
                  <w:pPr>
                    <w:jc w:val="both"/>
                    {cnf_cell}
                    {CELL_RUN_PROPS}
                  </w:pPr>
                  <w:r>
                    {CELL_RUN_PROPS}
                    <w:t>{escape_xml(planned_date)}</w:t>
                  </w:r>
                </w:p>
              </w:tc>
            </w:tr>"""


def build_participant_row(no, name, unit, title):
    """Build a single participant table row."""
    pid1 = gen_para_id()
    pid2 = gen_para_id()
    pid3 = gen_para_id()
    pid4 = gen_para_id()
    return f"""      <w:tr w:rsidR="00AA0001" w:rsidRPr="008B0C06" w14:paraId="{gen_para_id()}" w14:textId="77777777" w:rsidTr="13CB246E">
        <w:trPr>
          <w:trHeight w:val="397"/>
          <w:jc w:val="center"/>
        </w:trPr>
        <w:tc>
          <w:tcPr>
            <w:tcW w:w="815" w:type="dxa"/>
            <w:vAlign w:val="center"/>
          </w:tcPr>
          <w:p w14:paraId="{pid1}" w14:textId="{gen_text_id()}" w:rsidR="00AA0001" w:rsidRDefault="00AA0001" w:rsidP="00AA0001">
            <w:pPr>
              <w:rPr>
                <w:rFonts w:ascii="Tahoma" w:hAnsi="Tahoma" w:cs="Tahoma"/>
              </w:rPr>
            </w:pPr>
            <w:r>
              <w:rPr>
                <w:rFonts w:ascii="Tahoma" w:hAnsi="Tahoma" w:cs="Tahoma"/>
              </w:rPr>
              <w:t>{escape_xml(str(no))}</w:t>
            </w:r>
          </w:p>
        </w:tc>
        <w:tc>
          <w:tcPr>
            <w:tcW w:w="2730" w:type="dxa"/>
            <w:vAlign w:val="center"/>
          </w:tcPr>
          <w:p w14:paraId="{pid2}" w14:textId="{gen_text_id()}" w:rsidR="00AA0001" w:rsidRDefault="00AA0001" w:rsidP="00AA0001">
            <w:pPr>
              <w:jc w:val="both"/>
              <w:rPr>
                <w:rFonts w:ascii="Tahoma" w:hAnsi="Tahoma" w:cs="Tahoma"/>
                <w:smallCaps w:val="0"/>
              </w:rPr>
            </w:pPr>
            <w:r>
              <w:rPr>
                <w:rFonts w:ascii="Tahoma" w:hAnsi="Tahoma" w:cs="Tahoma"/>
                <w:smallCaps w:val="0"/>
              </w:rPr>
              <w:t>{escape_xml(name)}</w:t>
            </w:r>
          </w:p>
        </w:tc>
        <w:tc>
          <w:tcPr>
            <w:tcW w:w="2829" w:type="dxa"/>
            <w:vAlign w:val="center"/>
          </w:tcPr>
          <w:p w14:paraId="{pid3}" w14:textId="{gen_text_id()}" w:rsidR="00AA0001" w:rsidRDefault="00AA0001" w:rsidP="00AA0001">
            <w:pPr>
              <w:snapToGrid w:val="0"/>
              <w:jc w:val="both"/>
              <w:rPr>
                <w:rFonts w:ascii="Tahoma" w:hAnsi="Tahoma" w:cs="Tahoma"/>
                <w:smallCaps w:val="0"/>
              </w:rPr>
            </w:pPr>
            <w:r>
              <w:rPr>
                <w:rFonts w:ascii="Tahoma" w:hAnsi="Tahoma" w:cs="Tahoma"/>
                <w:smallCaps w:val="0"/>
              </w:rPr>
              <w:t>{escape_xml(unit)}</w:t>
            </w:r>
          </w:p>
        </w:tc>
        <w:tc>
          <w:tcPr>
            <w:tcW w:w="3402" w:type="dxa"/>
            <w:vAlign w:val="center"/>
          </w:tcPr>
          <w:p w14:paraId="{pid4}" w14:textId="{gen_text_id()}" w:rsidR="00AA0001" w:rsidRDefault="00AA0001" w:rsidP="00AA0001">
            <w:pPr>
              <w:snapToGrid w:val="0"/>
              <w:jc w:val="both"/>
              <w:rPr>
                <w:rFonts w:ascii="Tahoma" w:hAnsi="Tahoma" w:cs="Tahoma"/>
                <w:smallCaps w:val="0"/>
              </w:rPr>
            </w:pPr>
            <w:r>
              <w:rPr>
                <w:rFonts w:ascii="Tahoma" w:hAnsi="Tahoma" w:cs="Tahoma"/>
                <w:smallCaps w:val="0"/>
              </w:rPr>
              <w:t>{escape_xml(title)}</w:t>
            </w:r>
          </w:p>
        </w:tc>
      </w:tr>"""


def replace_field(content, marker_text, new_value):
    """Replace text content in a <w:t> element that matches marker_text."""
    pattern = re.compile(
        r'(<w:t[^>]*>)' + re.escape(marker_text) + r'(</w:t>)'
    )
    replacement = r'\g<1>' + escape_xml(new_value) + r'\g<2>'
    return pattern.sub(replacement, content, count=1)


def replace_cell_after_label(content, label_text, new_value):
    """Find a table cell containing label_text, then replace all runs in the NEXT cell's paragraph.

    Used for TARİH / SAAT / YER fields where the value cell follows the label cell and
    the value text may be split across multiple <w:r> runs.
    """
    label_pos = content.find(f'>{label_text}<')
    if label_pos == -1:
        return content
    # Move past the label cell closing tag </w:tc>
    tc_end = content.find('</w:tc>', label_pos)
    if tc_end == -1:
        return content
    tc_end += len('</w:tc>')
    # Find the paragraph inside the next cell
    next_p = content.find('<w:p ', tc_end)
    if next_p == -1:
        next_p = content.find('<w:p>', tc_end)
    if next_p == -1:
        return content
    p_end = content.find('</w:p>', next_p)
    if p_end == -1:
        return content
    p_end += len('</w:p>')

    para_xml = content[next_p:p_end]
    ppr_match = re.search(r'<w:pPr>.*?</w:pPr>', para_xml, re.DOTALL)
    ppr_block = ppr_match.group(0) if ppr_match else ''

    new_para = (
        f'<w:p>'
        f'{ppr_block}'
        f'<w:r><w:rPr><w:rFonts w:ascii="Tahoma" w:hAnsi="Tahoma" w:cs="Tahoma"/>'
        f'<w:smallCaps w:val="0"/></w:rPr>'
        f'<w:t>{escape_xml(new_value)}</w:t></w:r>'
        f'</w:p>'
    )
    return content[:next_p] + new_para + content[p_end:]


def replace_multirun_paragraph(content, anchor_text, new_value):
    """Replace all <w:r> runs in a paragraph that contains anchor_text with a single run.

    Handles titles/fields where Word split the text across multiple runs.
    Preserves the paragraph properties (<w:pPr>) and uses Tahoma font.
    """
    idx = content.find(anchor_text)
    if idx == -1:
        return content
    para_start = content.rfind('<w:p ', 0, idx)
    if para_start == -1:
        para_start = content.rfind('<w:p>', 0, idx)
    if para_start == -1:
        return content
    para_end = content.find('</w:p>', idx)
    if para_end == -1:
        return content
    para_end += len('</w:p>')

    para_xml = content[para_start:para_end]

    # Extract pPr block
    ppr_match = re.search(r'<w:pPr>.*?</w:pPr>', para_xml, re.DOTALL)
    ppr_block = ppr_match.group(0) if ppr_match else ''

    new_para = (
        f'<w:p>'
        f'{ppr_block}'
        f'<w:r><w:rPr><w:rFonts w:ascii="Tahoma" w:hAnsi="Tahoma" w:cs="Tahoma"/>'
        f'<w:smallCaps w:val="0"/></w:rPr>'
        f'<w:t>{escape_xml(new_value)}</w:t></w:r>'
        f'</w:p>'
    )
    return content[:para_start] + new_para + content[para_end:]


def main():
    parser = argparse.ArgumentParser(description="Generate TCDD meeting minutes docx")
    parser.add_argument("--data", required=True, help="Path to meeting data JSON file")
    parser.add_argument("--template", required=True, help="Path to template .docx file")
    parser.add_argument("--output", required=True, help="Output .docx path")
    args = parser.parse_args()

    with open(args.data, "r", encoding="utf-8") as f:
        data = json.load(f)

    work_dir = os.path.join(tempfile.gettempdir(), "_mm_work")
    unpacked_dir = os.path.join(work_dir, "unpacked")

    # Clean up
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.makedirs(unpacked_dir, exist_ok=True)

    # Step 1: Unpack template (docx is a zip file)
    with zipfile.ZipFile(args.template, 'r') as z:
        z.extractall(unpacked_dir)

    doc_path = os.path.join(unpacked_dir, "word", "document.xml")
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Step 2: Replace header fields (TOPLANTI ADI, TARİH, SAAT, YER)
    meta = data.get("meeting", {})
    # Title is split across multiple <w:r> runs in the template → use paragraph-level replace
    content = replace_multirun_paragraph(content, TEMPLATE_MARKERS["title_anchor"], meta.get("title", ""))
    # Date is split char-by-char across runs → use cell-after-label approach
    if meta.get("date", ""):
        content = replace_cell_after_label(content, TEMPLATE_MARKERS["date_label"], meta.get("date", ""))
    content = replace_field(content, TEMPLATE_MARKERS["time_value"], meta.get("time", ""))
    content = replace_field(content, TEMPLATE_MARKERS["location_value"], meta.get("location", ""))

    # Step 3: Replace participants table rows
    # Find participant table: between header row (NO/ADI SOYADI/BİRİM/UNVAN) and table close
    # We'll replace all data rows (keeping header row)
    participants = data.get("participants", [])
    if participants:
        # Find the participant table - locate the header row end and the table closing tag
        # The header row has shading (fill="C0C0C0")
        header_end_marker = re.search(
            r'(</w:tr>\s*)'  # end of header row with C0C0C0 shading
            r'(\s*<w:tr\s+w:rsidR="000C05E1")',  # first data row
            content
        )
        if not header_end_marker:
            # Fallback: find by the UNVAN cell followed by the first data row
            header_end_marker = re.search(
                r'(<w:t>UNVAN</w:t>.*?</w:tr>)\s*',
                content, re.DOTALL
            )

        # Find where participant data rows end and the next section begins
        # Participants table is followed by an empty paragraph then the content table
        participant_table_pattern = re.compile(
            r'(<w:t>UNVAN</w:t>.*?</w:tr>)'  # header row
            r'(.*?)'  # all data rows
            r'(\s*</w:tbl>)',  # table close
            re.DOTALL
        )

        match = participant_table_pattern.search(content)
        if match:
            new_rows = []
            for i, p in enumerate(participants):
                new_rows.append(build_participant_row(
                    i + 1,
                    p.get("name", ""),
                    p.get("unit", ""),
                    p.get("title", "")
                ))
            content = content[:match.end(1)] + "\n" + "\n".join(new_rows) + "\n    " + content[match.start(3):]

    # Step 4: Replace GÖRÜŞÜLEN KONULAR content
    topics = data.get("topics", [])
    if topics:
        topics_xml = build_gorusulen_konular(topics)

        # Strategy: find the GÖRÜŞÜLEN KONULAR: text and İŞLEM MADDELERİ: text,
        # then replace everything between the end of GÖRÜŞÜLEN KONULAR paragraph
        # and the start of İŞLEM MADDELERİ paragraph.
        
        # NOTE: In the template "GÖRÜŞÜLEN KONULAR" and ":" are in separate <w:r> runs,
        # so we match only up to the closing </w:t> of the main text (without the colon run).
        gk_marker = "GÖRÜŞÜLEN KONULAR</w:t>"
        im_marker = "İŞLEM MADDELERİ:</w:t>"
        
        gk_pos = content.find(gk_marker)
        im_pos = content.find(im_marker)
        
        if gk_pos != -1 and im_pos != -1:
            # Find the end of the GÖRÜŞÜLEN KONULAR paragraph (first </w:p> after marker)
            gk_para_end = content.find("</w:p>", gk_pos)
            if gk_para_end != -1:
                gk_para_end += len("</w:p>")
            
            # Find the start of the İŞLEM MADDELERİ paragraph (go back to find <w:p before the marker)
            # Search backwards from im_pos for the nearest <w:p
            search_back = content[:im_pos].rfind("<w:p ")
            if search_back == -1:
                search_back = content[:im_pos].rfind("<w:p>")
            
            if gk_para_end != -1 and search_back != -1:
                content = content[:gk_para_end] + "\n" + topics_xml + "\n          " + content[search_back:]

    # Step 5: Replace İŞLEM MADDELERİ (action items) table rows
    actions = data.get("actions", [])
    if actions:
        # Find the action items table header row (No/İşlem Maddesi/İlgili Birim/Planlanan Tarih)
        action_table_pattern = re.compile(
            r'(<w:t>Planlanan Tarih</w:t>.*?</w:tr>)'  # header row end
            r'(.*?)'  # all data rows
            r'(\s*</w:tbl>)',  # table close (the inner action table)
            re.DOTALL
        )
        # Find the LAST occurrence (action items table is the inner table)
        matches = list(action_table_pattern.finditer(content))
        if matches:
            match = matches[-1]
            new_rows = []
            for i, a in enumerate(actions):
                no = a.get("no", f"M{i+1:02d}")
                new_rows.append(build_action_row(
                    no,
                    a.get("text", ""),
                    a.get("responsible", ""),
                    a.get("planned_date", ""),
                    odd_band=(i % 2 == 0)
                ))
            content = content[:match.end(1)] + "\n" + "\n".join(new_rows) + "\n          " + content[match.start(3):]

    # Step 6: Replace Hazırlayan (prepared by)
    prepared_by = data.get("prepared_by", "")
    if prepared_by:
        # "Merve Nur Yıldırım" appears twice in template: once in participants table (row 12)
        # and once in the Hazırlayan cell (last cell before </w:tbl>).
        # Participants table is already replaced in Step 3, but the newly generated participant
        # rows also include Merve Nur Yıldırım, so replace_field would hit that first.
        # Use a specific lookahead that only matches the Hazırlayan occurrence.
        hazirlayan_pattern = re.compile(
            r'(<w:t[^>]*>)' + re.escape(TEMPLATE_MARKERS["prepared_by_value"]) + r'(</w:t>)'
            r'(?=</w:r></w:p></w:tc></w:tr></w:tbl>)'
        )
        content = hazirlayan_pattern.sub(
            r'\g<1>' + escape_xml(prepared_by) + r'\g<2>', content, count=1
        )

    # Write modified XML
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(content)

    # Step 7: Pack (repack directory back into a docx/zip)
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(unpacked_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, unpacked_dir)
                z.write(file_path, arcname)

    # Cleanup
    shutil.rmtree(work_dir)

    print(f"Meeting minutes generated: {args.output}")


if __name__ == "__main__":
    main()
