import re

filepath = 'frensense-engine/src/pattern/scorer.rs'
with open(filepath, 'r') as f:
    content = f.read()

repl = """        let default_w = &[
            0.10, 0.20, 0.08, 0.04, 0.03, 0.10, 0.08, 0.06, 0.12, 0.06, 0.10, 0.03, 0.02, 0.04,
            0.04, 0.02, 0.02, 0.02, 0.01, 0.01,
        ];"""
content = re.sub(r'let default_w = &\[.*?\];', repl, content, flags=re.DOTALL)

with open(filepath, 'w') as f:
    f.write(content)

