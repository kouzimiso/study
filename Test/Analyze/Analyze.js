function analyzeStringLineBySettings(string_data, analyze_setting) {
    //var keywords = Object.keys(analyze_setting);
    var keywords = [];
    for (var keyword in analyze_setting) {
      if (analyze_setting.hasOwnProperty(keyword)) {
        keywords.push(keyword);
      }
    }
    for (var i = 0; i < keywords.length; i++) {
      var keyword = keywords[i];
      var temp_setting = analyze_setting[keyword]["settings"];
      var ignore_list = temp_setting.ignore_list;
      if (string_data.indexOf(keyword) !== -1) {
        if (containsAny(string_data, ignore_list)) {
          return {};
        }
        dictionary_data = analyzeStringLineBySettingsHelper(string_data, keyword, temp_setting);
        return dictionary_data;
      }
    }
    return {};
  }
  function analyzeStringLineBySettingsHelper(string_data, keyword, analyze_setting) {
    split_text_to_dictionary = new splitTextToDictionary(analyze_setting[keyword]);
    split_text_to_dictionary.result_dictionary = analyze_setting.default_dictionary;
    split_text_to_dictionary.dictionary_format = analyze_setting.format_dictionary;
    element = Object.keys(split_text_to_dictionary.dictionary_format);
    dictionary_data = split_text_to_dictionary.execute(string_data, " ", keyword, element);
    if (dictionary_data["PortID"] <= 0 || dictionary_data["SlotID"] < 0) {
      //ポートIDが0以下またはスロットIDが0未満の場合は対象外
      return {};
    }
    //日付の追加
    dictionary_data = extractAndAddToDictionary(string_data, dictionary_data, "DateTime", extractDateTime);
    //余った文字列の追加(廃止）
    //未処理の前後文は処理の上で大切だが、観る人には不要なので廃止。
    //pre_text = split_text_to_dictionary.getPreviousText();
    //if(pre_text !==""){dictionary_data["PreText"] = pre_text;}
    //after_text = split_text_to_dictionary.getAfterText();
    //if(after_text !==""){dictionary_data["AfterText"] = after_text;}
    //全文の追加
    dictionary_data["AllText"] = string_data;
    return dictionary_data;
  }
  function extractAndAddToDictionary(string_data, dictionary_data, data_name, extract_function) {
    extract_data = extract_function(string_data);
    if (extract_data !== null) {
      dictionary_data[data_name] = extract_data;
    }
    return dictionary_data;
  }

  function extractDateTime(string_data) {
    // 正規表現を使用して日付と時刻を抽出
    //var regex = /\s*(\d{1,2}\/\d{1,2}\s+\d{1,2}:\s*\d{1,2})\s+(\d+)/;
    var regex = /\s*(\d{1,2}\/\d{1,2}(?:\/\d{2,4})?)\s+(\d{1,2}:\s*\d{1,2}(?::\s*\d{1,2})?)(?:\s+(\d+))?/;
    var match = regex.exec(string_data);
    if (match && match.length >= 3) {
      var date = match[1]; // 日付の部分
      var time = match[2]; // 時刻の部分

      // 秒数を取得
      var seconds = match[3] ? match[3] : '00';
      var datetime = date + ' ' + time + ":" + seconds;
      return datetime;
    }
    return null; // 日付と時刻が見つからない場合はnullを返す
  }

  function extractNumbers(text) {
    // 正規表現で数字のみを抽出
    var numbers = text.match(/\b\d+\b/g);
    return numbers;
  }

  function containsAny(string_data, substrings) {
    for (var i = 0; i < substrings.length; i++) {
      if (string_data.indexOf(substrings[i]) !== -1) {
        return true;
      }
    }
    return false;
  }

      // 文字列を分割して辞書形式で保存するクラス
    // クラスのインスタンス化後、executeメソッドを呼び出すことでテキストの処理が実行されます
    // 結果は各プロパティやメソッドを通じて取得できます
    function splitTextToDictionary(dictionary_data) {
      this.previous_text = "";
      this.after_text = "";
      this.element_count = 0;
      this.result_dictionary = dictionary_data;
      this.dictionary_format = dictionary_data;
      this.element_count = 0;
      this.execute = function (text, delimiter, start_text, element_list) {
        var start_index = text.indexOf(start_text);
        if (start_index === -1) {
          this.previous_text = text;
          return this.result_dictionary;
        }
        this.previous_text = text.substring(0, start_index);
        var end_index = start_index + start_text.length;
        var next_delimiter_index = text.indexOf(delimiter, start_index + start_text.length);
        this.result_dictionary[element_list[0]] = text.substring(start_index, next_delimiter_index).trim();
        var element_index = 1;
        end_index = next_delimiter_index + delimiter.length;
        while (element_index <= element_list.length && end_index < text.length) {
          var current_element = element_list[element_index];
          next_delimiter_index = text.indexOf(delimiter, end_index);
          if (next_delimiter_index === -1) {
            //console.log("Element not found.");
            //break;
            next_delimiter_index = text.length;
          }
          var value = text.substring(end_index, next_delimiter_index).trim();
          if (current_element in this.dictionary_format && !isNaN(this.dictionary_format[current_element])) {
            var numeric_value = parseFloat(value);
            if (isNaN(numeric_value)) {
              var numeric_value_string = extractNumbers(value);
              var numeric_value_string_index = text.indexOf(numeric_value_string, end_index);
              numeric_value = parseFloat(numeric_value_string);
              if (isNaN(numeric_value)) {
                break;
              }
              end_index = numeric_value_string_index + numeric_value_string.length - 1;
            } else {
              value = numeric_value;
              end_index = next_delimiter_index + delimiter.length;
            }
          } else {
            end_index = next_delimiter_index + delimiter.length;
          }
          this.result_dictionary[current_element] = value;
          element_index++;
        }
        this.element_count = element_index;
        if (element_index < element_list.length) {
          this.after_text = "";
        } else {
          this.after_text = text.substring(end_index).replace(/^\s+|\s+$/g, '');//.trim();
        }
        return this.result_dictionary;
      };
      this.setResultDictionary = function (dictionary_data) {
        this.result_dictionary = dictionary_data;
      };
      this.setDictionaryFormat = function (dictionary_data) {
        this.dictionary_format = dictionary_data;
      };
      this.getPreviousText = function () {
        return this.previous_text;
      };
      this.getAfterText = function () {
        return this.after_text;
      };
      this.getElementCount = function () {
        return this.element_count;
      };
      this.getResultDictionary = function () {
        return this.result_dictionary;
      };
    }

