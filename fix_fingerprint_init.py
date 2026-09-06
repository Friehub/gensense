import os
import re

files = [
    'frensense-engine/src/fingerprint.rs',
    'frensense-engine/src/rust_hir_provider.rs',
    'frensense-engine/src/pattern/scorer.rs',
    'frensense-engine/src/oxc_provider.rs',
    'frensense-engine/src/semantic.rs',
    'frensense-engine/src/function_role.rs'
]

for filepath in files:
    if not os.path.exists(filepath): continue
    with open(filepath, 'r') as f:
        content = f.read()
    
    # We want to insert `region: None,` after `function_name: ...,` 
    # OR we can just insert `region: None,` after `FunctionFingerprint {`
    # Let's insert it right after `FunctionFingerprint {`
    
    # regex for `FunctionFingerprint {`
    content = re.sub(r'FunctionFingerprint\s*\{', 'FunctionFingerprint {\n            region: None,', content)
    
    with open(filepath, 'w') as f:
        f.write(content)

