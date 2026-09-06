import re

filepath = 'frensense-engine/src/pattern/weight_learner.rs'
with open(filepath, 'r') as f:
    content = f.read()

repl = """pub(crate) const DEFAULT_WEIGHTS: FeatureVec = [
    0.08, 0.10, 0.08, 0.04, 0.03, 0.10, 0.10, 0.10, 0.14, 0.12, 0.16, 0.03, 0.02, 0.04, 0.04,
    0.05, 0.05, 0.01,
];"""
content = re.sub(r'pub\(crate\) const DEFAULT_WEIGHTS: FeatureVec = \[\n.*?\];\n//\n.*?\];', repl, content, flags=re.DOTALL)

with open(filepath, 'w') as f:
    f.write(content)
