import json
import re

def load_grammar(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def tokenize(text, keywords, patterns):
    tokens = []
    remaining = text.strip()
    while remaining:
        if re.match(r'^\s+', remaining):
            remaining = re.sub(r'^\s+', '', remaining)
            continue
        matched = False
        for keyword in keywords:
            if remaining.startswith(keyword):
                tokens.append({'type': 'keyword', 'value': keyword})
                remaining = remaining[len(keyword):].strip()
                matched = True
                break
        if matched:
            continue
        for pattern in sorted(patterns, key=lambda p: len(p['regex']), reverse=True):
            match = re.match(pattern['regex'], remaining)
            if match:
                tokens.append({'type': 'pattern', 'name': pattern['name'], 'value': match.group(0)})
                remaining = remaining[len(match.group(0)):].strip()
                matched = True
                break
        if not matched:
            raise ValueError(f"不明なトークン: {remaining[:20]}")
    return tokens

def parse_rule(tokens, rule, grammar):
    remaining = list(tokens)
    structure = rule.get('structure', [])
    structure_idx = 0
    while structure_idx < len(structure):
        expected = structure[structure_idx]
        if not remaining:
            if expected.get('required', True) and not expected.get('repeatable', False):
                return False, remaining, f"'{expected.get('value', expected.get('name', expected['type']))}' が期待されましたが文末に到達しました。"
            structure_idx += 1
            continue
        token = remaining[0]
        match = False
        if expected['type'] == 'rule':
            sub_rule = next((r for r in grammar['rules'] if r['name'] == expected['name']), None)
            if sub_rule:
                success, rem, msg = parse_rule(remaining, sub_rule, grammar)
                if success:
                    remaining = rem
                    match = True
                elif expected.get('required', True) is False:
                    match = True
            else:
                return False, remaining, f"ルール '{expected['name']}' が見つかりません"
        elif expected['type'] == token['type']:
            if expected.get('value') == token.get('value') or expected.get('name') == token.get('name') or ('value' not in expected and 'name' not in expected):
                remaining = remaining[1:]
                match = True
        if match:
            if expected.get('repeatable'):
                while True:
                    sub_match = False
                    if not remaining:
                        break
                    if expected['type'] == 'rule':
                        sub_rule = next((r for r in grammar['rules'] if r['name'] == expected['name']), None)
                        if sub_rule:
                            ok, rem, _ = parse_rule(remaining, sub_rule, grammar)
                            if ok:
                                remaining = rem
                                sub_match = True
                    elif expected['type'] == remaining[0]['type']:
                        if expected.get('value') == remaining[0].get('value') or expected.get('name') == remaining[0].get('name') or ('value' not in expected and 'name' not in expected):
                            remaining = remaining[1:]
                            sub_match = True
                    if not sub_match:
                        break
            structure_idx += 1
        else:
            if expected.get('required', True):
                return False, remaining, f"'{expected.get('value', expected.get('name', expected['type']))}' が期待されましたが '{token['value']}' が見つかりました。"
            else:
                structure_idx += 1
    return True, remaining, "解析成功"

def analyze_sentence(sentence, grammar):
    try:
        tokens = tokenize(sentence, grammar.get('keywords', []), grammar.get('patterns', []))
        print("トークン:", tokens)
        top_structure = grammar.get("structure", [])
        for element in top_structure:
            if element['type'] == 'rule':
                rule = next((r for r in grammar['rules'] if r['name'] == element['name']), None)
                if rule:
                    success, remaining, message = parse_rule(tokens, rule, grammar)
                    if success and not remaining:
                        print("解析成功:", message)
                        return
                    elif success:
                        print("部分的に解析成功:", message)
                        print("未解析トークン:", remaining)
                        return
                    else:
                        print("解析失敗:", message)
                        return
        print("構文エラー: トップレベルルールが不正です。")
    except Exception as e:
        print("エラー:", e)

if __name__ == "__main__":
    grammar_file = './Test/parse_grammar.json' # 文法定義ファイルのパス
    grammar = load_grammar(grammar_file)

    sentences_to_analyze = [
        "もし 変数1 == 10 ならば 表示 変数1 終了",
        "もし 数値A > 5 ならば 変数B = 15 終了",
        "もし count == 0 ならば 表示 'ゼロです' 終了",
        "もし flag != true ならば 終了",
        "もし a == b ならば 表示 a 終了",
        "もし value ならば 表示 value 終了"
    ]

    for sentence in sentences_to_analyze:
        print(f"\n解析対象: '{sentence}'")
        analyze_sentence(sentence, grammar)