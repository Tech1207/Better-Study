import re

# 1. Read input file
with open("acce.txt", "r", encoding="utf-8") as f:
    data = f.read()

# 2. Regex to match "name" + role ("text leaf" or "cell")
pattern = r'"name": ".*?",[ \n][ \t]*"role": "(?:text leaf|cell)",'
matches = re.findall(pattern, data, re.DOTALL)

# 3. First pass: collect all valid text leaf names
text_leaf_names = set()
for m in matches:
    role_match = re.search(r'"role": "(.*?)"', m)
    name_match = re.search(r'"name": "(.*?)"', m, re.DOTALL)
    if name_match and role_match:
        name_value = name_match.group(1).strip()
        role_value = role_match.group(1).strip()

        # Skip standalone labels like A), 1)
        if re.fullmatch(r'[A-Za-z0-9]+\)', name_value):
            continue
        if re.search(r'\bchapter\s*\d+[:]?|\bquestion\s*\d+', name_value, re.IGNORECASE):
            continue
        if name_value == "Unselected" or name_value == "Correct Answer Unselected":
            continue
        if "\\" in name_value:
            continue

        if role_value == "text leaf":
            text_leaf_names.add(name_value)

# 4. Second pass: process all roles in order, applying rules
names = []
prepend_next = False

for m in matches:
    role_match = re.search(r'"role": "(.*?)"', m)
    name_match = re.search(r'"name": "(.*?)"', m, re.DOTALL)
    if name_match and role_match:
        name_value = name_match.group(1).strip()
        role_value = role_match.group(1).strip()

        # Skip standalone labels like A), 1)
        if re.fullmatch(r'[A-Za-z0-9]+\)', name_value):
            continue
        if re.search(r'\bchapter\s*\d+[:]?|\bquestion\s*\d+', name_value, re.IGNORECASE):
            continue
        if name_value == "Unselected":
            continue
        if "\\" in name_value:
            continue

        # Handle "Correct Answer Unselected"
        if name_value == "Correct Answer Unselected":
            prepend_next = True
            continue

        # Skip "cell" if duplicate of text leaf
        if role_value == "cell" and name_value in text_leaf_names:
            continue

        # Only prepend ">" to the first valid item after Correct Answer Unselected
        if prepend_next:
            name_value = ">" + name_value
            prepend_next = False

        names.append(name_value)

# 5. Save output
with open("output.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(names))

print(f"Extracted {len(names)} names (skipped {len(matches)-len(names)}) and saved them to output.txt")