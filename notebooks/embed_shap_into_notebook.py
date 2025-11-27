import os
import json
import base64

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
notebook_path = os.path.join(ROOT, 'notebooks', 'demo_shap.ipynb')
png_path = os.path.join(ROOT, 'backend-python', 'models', 'shap_summary.png')

if not os.path.exists(notebook_path):
    raise SystemExit('Notebook not found: ' + notebook_path)
if not os.path.exists(png_path):
    raise SystemExit('SHAP PNG not found: ' + png_path)

with open(png_path, 'rb') as f:
    b = f.read()
b64 = base64.b64encode(b).decode('ascii')
data_uri = 'data:image/png;base64,' + b64

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find the index of the cell that displays the saved SHAP image (search by the comment text)
insert_at = None
for i, cell in enumerate(nb.get('cells', [])):
    src = '\n'.join(cell.get('source', []))
    if 'Display the saved SHAP image inline' in src or 'display(Image(filename=' in src:
        insert_at = i + 1
        break

if insert_at is None:
    # append at end
    insert_at = len(nb.get('cells', []))

md_cell = {
    'cell_type': 'markdown',
    'metadata': {'language': 'markdown'},
    'source': [
        '### Embedded SHAP summary image',
        f'<img src="{data_uri}" alt="SHAP summary"/>'
    ]
}

nb['cells'].insert(insert_at, md_cell)

with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=2)

print('Embedded SHAP image into notebook at cell index', insert_at)
