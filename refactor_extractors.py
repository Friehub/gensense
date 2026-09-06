import re
import os

filepath = 'frensense-engine/src/fingerprint.rs'
with open(filepath, 'r') as f:
    content = f.read()

# 1. count_comment_bytes
# Original: fn count_comment_bytes(node: Node<'_>, source: &str) -> usize {
#     let start = node.start_byte();
#     let end = node.end_byte();
# ...
repl1 = """fn count_comment_bytes(nodes: &[Node<'_>], source: &str) -> usize {
    let mut total = 0;
    for &node in nodes {
        let start = node.start_byte();
        let end = node.end_byte();
        let mut in_comment = false;
        let mut comment_bytes = 0;
        let mut i = start;
        let bytes = source.as_bytes();
        while i < end {
            if i + 1 < end && bytes[i] == b'/' && bytes[i + 1] == b'/' {
                in_comment = true;
                i += 2;
                comment_bytes += 2;
                continue;
            }
            if in_comment {
                if bytes[i] == b'\\n' {
                    in_comment = false;
                } else {
                    comment_bytes += 1;
                }
            }
            i += 1;
        }
        total += comment_bytes;
    }
    total
}"""
content = re.sub(r'fn count_comment_bytes\(node: Node<\'_>, source: &str\) -> usize \{.*?(?=\nfn |\n\n)', repl1, content, flags=re.DOTALL)


# 2. extract_control_flow
repl2 = """fn extract_control_flow(nodes: &[Node<'_>], source: &str) -> Vec<u64> {
    let mut hashes = FxHashSet::default();
    for &node in nodes {
        extract_cf_recursive(node, source, &mut hashes);
    }
    let mut vec: Vec<u64> = hashes.into_iter().collect();
    vec.sort_unstable();
    vec
}"""
content = re.sub(r'fn extract_control_flow\(node: Node<\'_>, source: &str\) -> Vec<u64> \{.*?vec\n\}', repl2, content, flags=re.DOTALL)

# 3. extract_cf_sequence
repl3 = """fn extract_cf_sequence(nodes: &[Node<'_>], source: &str) -> Vec<u64> {
    let mut events = Vec::new();
    for &node in nodes {
        collect_cf_seq_recursive(node, source, &mut events);
    }
    let mut hashes = Vec::with_capacity(events.len());
    for chunk in events.chunks(3) {
        let mut hasher = rustc_hash::FxHasher::default();
        for event in chunk {
            std::hash::Hash::hash(event, &mut hasher);
        }
        hashes.push(std::hash::Hasher::finish(&hasher));
    }
    hashes.sort_unstable();
    hashes
}"""
content = re.sub(r'fn extract_cf_sequence\(node: Node<\'_>, source: &str\) -> Vec<u64> \{.*?hashes\n\}', repl3, content, flags=re.DOTALL)

# 4. collect_raw_call_names
repl4 = """fn collect_raw_call_names(nodes: &[Node<'_>], source: &str) -> Vec<String> {
    let mut names = Vec::new();
    for &node in nodes {
        collect_raw_calls_recursive(node, source, &mut names);
    }
    names
}"""
content = re.sub(r'fn collect_raw_call_names\(node: Node<\'_>, source: &str\) -> Vec<String> \{.*?names\n\}', repl4, content, flags=re.DOTALL)

# 5. extract_property_accesses
repl5 = """fn extract_property_accesses(nodes: &[Node<'_>], source: &str) -> Vec<u64> {
    let mut accesses = FxHashSet::default();
    for &node in nodes {
        extract_properties_recursive(node, source, &mut accesses);
    }
    let mut vec: Vec<u64> = accesses.into_iter().collect();
    vec.sort_unstable();
    vec
}"""
content = re.sub(r'fn extract_property_accesses\(node: Node<\'_>, source: &str\) -> Vec<u64> \{.*?vec\n\}', repl5, content, flags=re.DOTALL)

# 6. extract_tainted_calls
repl6 = """fn extract_tainted_calls(nodes: &[Node<'_>], source: &str, param_names: &[String]) -> Vec<u64> {
    let mut calls = FxHashSet::default();
    for &node in nodes {
        extract_tainted_recursive(node, source, param_names, &mut calls);
    }
    let mut vec: Vec<u64> = calls.into_iter().collect();
    vec.sort_unstable();
    vec
}"""
content = re.sub(r'fn extract_tainted_calls\(node: Node<\'_>, source: &str, param_names: &\[String\]\) -> Vec<u64> \{.*?vec\n\}', repl6, content, flags=re.DOTALL)

# 7. extract_argument_call_types
repl7 = """fn extract_argument_call_types(nodes: &[Node<'_>], source: &str) -> Vec<u64> {
    let mut types = FxHashSet::default();
    for &node in nodes {
        extract_arg_types_recursive(node, source, &mut types);
    }
    let mut vec: Vec<u64> = types.into_iter().collect();
    vec.sort_unstable();
    vec
}"""
content = re.sub(r'fn extract_argument_call_types\(node: Node<\'_>, source: &str\) -> Vec<u64> \{.*?vec\n\}', repl7, content, flags=re.DOTALL)

# 8. extract_literal_patterns
repl8 = """fn extract_literal_patterns(nodes: &[Node<'_>], source: &str) -> Vec<u64> {
    let mut patterns = rustc_hash::FxHashSet::default();
    for &node in nodes {
        extract_literal_patterns_recursive(node, source, &mut patterns);
    }
    let mut vec: Vec<u64> = patterns.into_iter().collect();
    vec.sort_unstable();
    vec
}"""
content = re.sub(r'fn extract_literal_patterns\(node: Node<\'_>, source: &str\) -> Vec<u64> \{.*?vec\n\}', repl8, content, flags=re.DOTALL)


# 9. collect_type_usages
repl9 = """fn collect_type_usages(nodes: &[Node<'_>], source: &str) -> Vec<String> {
    let mut usages = rustc_hash::FxHashSet::default();
    for &node in nodes {
        collect_type_usages_recursive(node, source, &mut usages);
    }
    let mut vec: Vec<String> = usages.into_iter().collect();
    vec.sort();
    vec
}"""
# wait, let me check collect_type_usages first to ensure it has a recursive helper.

with open(filepath, 'w') as f:
    f.write(content)
