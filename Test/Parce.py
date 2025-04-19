import json
import re

def load_grammar(filepath):
    """JSON形式の文法定義ファイルを読み込む"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def tokenize(text, keywords, patterns):
    """テキストをトークンに分割する"""
    tokens = []
    remaining_text = text.strip()
    while remaining_text:
        matched = False
        # Whitespace のスキップ
        whitespace_match = re.match(r"^\s+", remaining_text)
        if whitespace_match:
            remaining_text = remaining_text[len(whitespace_match.group(0)):].strip()
            continue

        # キーワードのマッチング
        for keyword in keywords:
            if remaining_text.startswith(keyword):
                tokens.append({"type": "keyword", "value": keyword})
                remaining_text = remaining_text[len(keyword):].strip()
                matched = True
                break
        if matched:
            continue

        # パターンのマッチング (より具体的なものから順に試す)
        sorted_patterns = sorted(patterns, key=lambda p: len(p['regex']), reverse=True)
        for pattern in sorted_patterns:
            match = re.match(pattern['regex'], remaining_text)
            if match:
                tokens.append({"type": "pattern", "name": pattern['name'], "value": match.group(0)})
                remaining_text = remaining_text[len(match.group(0)):].strip()
                matched = True
                break

        # マッチングしなかった場合
        if not matched:
            raise ValueError(f"解析エラー: 不明なトークン '{remaining_text[:20]}...'")
            break
    return tokens

def parse_structure(tokens, structure_definition):
    """トークン列が定義された構造に合致するか検証する"""
    token_index = 0
    structure_index = 0
    while token_index < len(tokens) and structure_index < len(structure_definition):
        expected = structure_definition[structure_index]
        current_token = tokens[token_index]

        if expected['type'] == current_token['type']:
            match = True
            if 'value' in expected and expected['value'] != current_token.get('value'):
                match = False
            elif 'name' in expected and expected['name'] != current_token.get('name'):
                match = False

            if match:
                token_index += 1
                structure_index += 1
            elif expected.get('required', True) is False:
                structure_index += 1
            elif expected.get('repeatable', False) is True:
                # 同じ構造が繰り返されるか確認
                sub_structure = [expected]
                sub_structure_index = 0
                sub_token_index = token_index
                sub_match = True
                while sub_token_index < len(tokens) and sub_structure_index < len(sub_structure) and sub_match:
                    sub_expected = sub_structure[sub_structure_index]
                    sub_current_token = tokens[sub_token_index]
                    if sub_expected['type'] == sub_current_token['type']:
                        if 'value' in sub_expected and sub_expected['value'] != sub_current_token.get('value'):
                            sub_match = False
                        elif 'name' in sub_expected and sub_expected['name'] != sub_current_token.get('name'):
                            sub_match = False
                        if sub_match:
                            sub_token_index += 1
                            sub_structure_index += 1
                    else:
                        sub_match = False
                if sub_token_index > token_index:
                    token_index = sub_token_index
                structure_index += 1
            else:
                return False, f"予期しないトークン '{current_token['value']}' ({current_token['type']}) が出現しました。'{expected.get('value', expected.get('name', expected['type']))}' が期待されていました。"
        elif expected.get('required', True) is False:
            structure_index += 1
        elif expected.get('repeatable', False) is True:
            # repeatable な要素はスキップして次の構造要素へ進む
            structure_index += 1
        else:
            return False, f"予期しないトークン '{current_token['value']}' ({current_token['type']}) が出現しました。'{expected.get('value', expected.get('name', expected['type']))}' が期待されていました。"

    if token_index < len(tokens):
        return False, f"文末以降に予期しないトークン '{tokens[token_index]['value']}' があります。"

    # 必須要素が残っていないか確認 (repeatable な要素は除く)
    for i in range(structure_index, len(structure_definition)):
        if structure_definition[i].get('required', True) and not structure_definition[i].get('repeatable', False):
            return False, f"文末が予期せず終了しました。'{structure_definition[i].get('value', structure_definition[i].get('name', structure_definition[i]['type']))}' が期待されていました。"

    return True, "解析成功"
def parse_rule(tokens, rule, grammar):
    """特定のルールに基づいてトークン列を解析する"""
    remaining_tokens = list(tokens)  # コピーを作成して操作
    parsed_elements = []
    success = True
    message = "解析成功"

    if 'structure' in rule:
        structure = rule['structure']
        structure_index = 0
        while remaining_tokens and structure_index < len(structure):
            expected = structure[structure_index]

            if expected['type'] == 'rule':
                sub_rule_name = expected['name']
                sub_rule = next((r for r in grammar['rules'] if r['name'] == sub_rule_name), None)
                if sub_rule:
                    sub_success, sub_remaining, sub_message = parse_rule(remaining_tokens, sub_rule, grammar)
                    if sub_success:
                        parsed_elements.append({'type': 'rule', 'name': sub_rule_name, 'tokens': tokens[:len(tokens) - len(sub_remaining)]}) # 消費されたトークンを記録
                        remaining_tokens = sub_remaining
                        structure_index += 1
                    elif expected.get('required', True) is False:
                        structure_index += 1
                    elif expected.get('repeatable', False) is True:
                        # 繰り返し可能なルールは失敗しても次の構造要素を試す
                        structure_index += 1
                    else:
                        success = False
                        message = f"期待されたルール '{sub_rule_name}' にマッチしませんでした。"
                        break
                else:
                    success = False
                    message = f"ルール '{sub_rule_name}' が見つかりません。"
                    break
            elif expected['type'] == 'keyword' and remaining_tokens and remaining_tokens[0]['type'] == 'keyword' and remaining_tokens[0]['value'] == expected['value']:
                parsed_elements.append(remaining_tokens.pop(0))
                structure_index += 1
            elif expected['type'] == 'pattern' and remaining_tokens and remaining_tokens[0]['type'] == 'pattern' and remaining_tokens[0]['name'] == expected['name']:
                parsed_elements.append(remaining_tokens.pop(0))
                structure_index += 1
            elif expected.get('required', True) is False:
                structure_index += 1
            elif expected.get('repeatable', False) is True:
                # 繰り返し可能な非ルール要素はここでは単純にスキップして次へ (より複雑な繰り返しは個別のルールで)
                structure_index += 1
            else:
                success = False
                message = f"期待されたトークン '{expected.get('value', expected.get('name', expected['type']))}' にマッチしませんでした (現在のトークン: '{remaining_tokens[0]['value']}' if remaining_tokens else '文末')."
                break
        return success, remaining_tokens, message

    elif 'alternatives' in rule:
        for alternative in rule['alternatives']:
            alt_success, alt_remaining, alt_message = parse_rule(tokens, {'name': rule['name'], 'structure': [alternative]}, grammar)
            if alt_success:
                return True, alt_remaining, "解析成功"
        return False, tokens, f"'{rule['name']}' のいずれかの代替案にマッチしませんでした。"

    elif 'keywords' in rule:
        if tokens and tokens[0]['type'] == 'keyword' and tokens[0]['value'] in rule['keywords']:
            return True, tokens[1:], "解析成功"
        else:
            return False, tokens, f"期待されたキーワード ({', '.join(rule['keywords'])}) が見つかりません。"

    elif 'alternatives' in rule and 'elements' in rule:
        if tokens and tokens[0]['type'] in [alt['type'] for alt in rule['elements']]:
            element = next(alt for alt in rule['elements'] if alt['type'] == tokens[0]['type'])
            match = True
            if 'value' in element and element['value'] != tokens[0]['value']:
                match = False
            elif 'name' in element and element['name'] != tokens[0]['name']:
                match = False
            if match:
                return True, tokens[1:], "解析成功"
        return False, tokens, f"期待された代替要素が見つかりません。"

    return False, tokens, f"ルール '{rule['name']}' の解析方法が定義されていません。"

def analyze_sentence(sentence, grammar):
    """文章を解析するメイン関数"""
    try:
        tokens = tokenize(sentence, grammar.get('keywords', []), grammar.get('patterns', []))
        print("トークン:", tokens)

        if grammar['rules']:
            top_level_rule = grammar['rules'][0]
            remaining_tokens = list(tokens)
            all_parsed = True
            while remaining_tokens:
                success, new_remaining_tokens, message = parse_rule(remaining_tokens, top_level_rule, grammar)
                if success:
                    print(f"解析結果 (部分): {message}")
                    remaining_tokens = new_remaining_tokens
                else:
                    all_parsed = False
                    print(f"解析失敗 (部分): {message}")
                    print(f"未解析のトークン: {remaining_tokens}")
                    break

            if all_parsed:
                print("最終解析結果: 解析成功 (すべてのトークンを消費)")
            elif not remaining_tokens:
                print("最終解析結果: 解析成功 (すべてのトークンを消費)")
            else:
                print("最終解析結果: 解析失敗 (一部のトークンが未消費)")

        else:
            print("エラー: 文法規則が定義されていません。")

    except ValueError as e:
        print(f"エラー: {e}")
    except Exception as e:
        print(f"予期しないエラー: {e}")

if __name__ == "__main__":
    grammar_file = 'grammar.json' # 文法定義ファイルのパス
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
if __name__ == "__main__":
    grammar_file = 'grammar.json' # 文法定義ファイルのパス
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