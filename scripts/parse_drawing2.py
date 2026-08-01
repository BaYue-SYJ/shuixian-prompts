import zipfile
import xml.etree.ElementTree as ET

fpath = r"C:\Users\lianxiang\Desktop\split_by_style\split_by_style\6大类\06_其他综合.xlsx"

with zipfile.ZipFile(fpath, 'r') as z:
    drawing_xml = z.read('xl/drawings/drawing1.xml').decode('utf-8')

# Print first 2000 chars of drawing XML to understand structure
print("=== Drawing XML (first 3000 chars) ===")
print(drawing_xml[:3000])

print("\n\n=== All child elements of root ===")
ns = {
    'xdr': 'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
}

root = ET.fromstring(drawing_xml)
print(f"Root tag: {root.tag}")
for child in root:
    print(f"  Child: {child.tag} (attribs: {dict(child.attrib)})")
    # Look for any 'from' element at any level
    for elem in child.iter():
        if 'from' in elem.tag.lower() or 'to' in elem.tag.lower() or 'anchor' in elem.tag.lower():
            print(f"    -> {elem.tag}")
            for sub in elem:
                print(f"       -> {sub.tag}: {sub.text}")
            break  # just first one
