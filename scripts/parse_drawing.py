import zipfile
import xml.etree.ElementTree as ET

fpath = r"C:\Users\lianxiang\Desktop\split_by_style\split_by_style\6大类\06_其他综合.xlsx"

with zipfile.ZipFile(fpath, 'r') as z:
    # Read drawing1.xml
    drawing_xml = z.read('xl/drawings/drawing1.xml').decode('utf-8')
    # Read rels
    rels_xml = z.read('xl/drawings/_rels/drawing1.xml.rels').decode('utf-8')

# Parse drawing XML to get anchor positions
# Namespace
ns = {
    'xdr': 'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
}

root = ET.fromstring(drawing_xml)

# Find all anchors (twoCellAnchor is the common type)
anchors = root.findall('.//xdr:twoCellAnchor', ns)
print(f"Total anchors: {len(anchors)}")

for i, anchor in enumerate(anchors[:10]):
    from_el = anchor.find('xdr:from', ns)
    to_el = anchor.find('xdr:to', ns)
    pic = anchor.find('xdr:pic', ns)
    
    if from_el is not None:
        col = from_el.find('xdr:col', ns)
        row = from_el.find('xdr:row', ns)
        col_val = col.text if col is not None else '?'
        row_val = row.text if row is not None else '?'
    else:
        col_val = '?'
        row_val = '?'
    
    # Get image relationship ID
    blip = None
    if pic is not None:
        blip = pic.find('.//a:blip', ns)
    rel_id = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed') if blip is not None else '?'
    
    print(f"  Anchor {i}: from col={col_val} row={row_val} -> relId={rel_id}")

# Parse rels to get image file mapping
print("\n=== Relationship mapping ===")
rels_root = ET.fromstring(rels_xml)
for rel in rels_root:
    rid = rel.get('Id')
    target = rel.get('Target')
    print(f"  {rid} -> {target}")
