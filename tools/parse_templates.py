import os
import re

TEMPLATES_DIR = '../www/templates'

for html_name in os.listdir(TEMPLATES_DIR):
    html_path = os.path.join(TEMPLATES_DIR, html_name)
    with open(html_path, 'r') as html_file:
        print re.sub('<%(.*?)%>', '', html_file.read(), flags=re.S)
