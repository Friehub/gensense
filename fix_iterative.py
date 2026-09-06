import re
import os

filepath = 'frensense-engine/src/fingerprint.rs'
with open(filepath, 'r') as f:
    content = f.read()

# Fix collect_structural_markers
repl1 = """fn collect_structural_markers(nodes: &[Node<'_>], _source: &str, language: Language) -> Vec<u64> {
    let mut markers = FxHashSet::default();
    for &node in nodes {
        collect_structural_recursive(node, language, &mut markers);
    }
    let mut vec: Vec<u64> = markers.into_iter().collect();
    vec.sort_unstable();
    vec
}

fn collect_structural_recursive(node: Node<'_>, language: Language, markers: &mut FxHashSet<u64>) {
    let kind = abstract_kind(node.kind(), language);
    if kind != AbstractKind::Other {
        let mut hasher = FxHasher::default();
        kind.hash(&mut hasher);
        markers.insert(hasher.finish());
    }
    let mut cursor = node.walk();
    for child in node.children(&mut cursor) {
        collect_structural_recursive(child, language, markers);
    }
}"""
content = re.sub(r'fn collect_structural_markers\(node: Node<\'_>, _source: &str, language: Language\) -> Vec<u64> \{.*?return vec;\n            \}\n        \}\n    \}\n\}', repl1, content, flags=re.DOTALL)

# Fix collect_type_usages
repl2 = """fn collect_type_usages(nodes: &[Node<'_>], source: &str) -> Vec<String> {
    let mut types = rustc_hash::FxHashSet::default();
    for &node in nodes {
        collect_type_usages_recursive(node, source, &mut types);
    }
    let mut vec: Vec<String> = types.into_iter().collect();
    vec.sort();
    vec
}

fn collect_type_usages_recursive(node: Node<'_>, source: &str, types: &mut rustc_hash::FxHashSet<String>) {
    if node.kind() == "type_identifier" || node.kind() == "predefined_type" {
        types.insert(source[node.start_byte()..node.end_byte()].to_string());
    }
    let mut cursor = node.walk();
    for child in node.children(&mut cursor) {
        collect_type_usages_recursive(child, source, types);
    }
}"""
# In the original, it returned a Vec directly with duplicates, let's use a HashSet to deduplicate then sort, just like other functions.
content = re.sub(r'fn collect_type_usages\(node: Node<\'_>, source: &str\) -> Vec<String> \{.*?return types;\n            \}\n        \}\n    \}\n\}', repl2, content, flags=re.DOTALL)

with open(filepath, 'w') as f:
    f.write(content)
