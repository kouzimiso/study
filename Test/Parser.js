    // パーサーコンビネータークラス
    class Parser {
        constructor(source) {
          this.source = source;
          this.position = 0;
          this.token_end_setting =      ["\n","\r\n",")","}","]","'","'",";"," ","　","\t"]
          this.expression_end_setting = [";","\n","\r\n"]
          this.line_end_setting = ["\n","\r\n"]
          this.statement_keyword_setting = ["if","for","while"]

          this.if_parse_setting = {
            "parsed_result":{"type":"IfStatement"},
            "parsing_rule_list":[
              {"type":"key","key":"if", "must_element":true},
              {
                "type":"parts",
                "parsing_rule_list":[
                  {"type":"key","key":"(", "must_element":false},
                  {"type":"condition_expression", "must_element":true ,"end_element_list":[")","{"]},
                  {"type":"key","key":")", "must_element":false}
                ],
                "must_element":true
              },
              {"type":"key","key":"{", "must_element":true},
              {"type":"statement_expression" ,"end_element_list":["}"]},
              {"type":"key","key":"}", "must_element":true}
            ]
  
          }
          this.for_parse_setting = {
            "parsed_result":{"type":"ForStatement"},
            "parsing_rule_list":[
              {"type":"key","key":"for", "must_element":true},
              {
                "type":"parts",
                "parsing_rule_list":[
                  {"type":"key","key":"(", "must_element":false},
                  {"type":"declaration_expression", "must_element":true,"end_element_list":[";"]},
                  {"type":"key","key":";", "must_element":false},
                  {"type":"condition_expression", "must_element":true,"end_element_list":[";"]},
                  {"type":"key","key":";", "must_element":false},
                  {"type":"incrementors_expression", "must_element":true,"end_element_list":[")","{"]},
                  {"type":"key","key":")", "must_element":false}
                ],
                "must_element":true
              },
              {"type":"key","key":"{", "must_element":true},
              {"type":"statement_expression","end_element_list":["}"]},
              {"type":"key","key":"}", "must_element":true}
            ]
  
          }
          this.parse_settings ={
            "type":"settings",
            "settings":{
                "if" :this.if_parse_setting,
                "for" :this.for_parse_setting
             }
          }

        }
        // ヘルパー関数：指定された文字列がマッチするかどうかをチェックする
        matchString(match_word) {
          if (this.source.substring(this.position, this.position + match_word.length) === match_word) {
            return true;
          }
          return false;
        }
        matchStringList(position, match_list) {
          const currentText = this.source.substring(position);
  
          for (const condition of match_list) {
            if (currentText.startsWith(condition)) {
              return true;
            }
          }
          return false;
        }
  
        // 空白の判定を行う関数
        matchWhiteSpace(position) {
          return /\s/.test(this.source[position]);
        }
        // 文章の終了判定を行う関数
        matchExpressionEnd(position) {
          // 設定した文字現れた場合、式の終わりとみなす
          return  this.matchStringList(position,this.expression_end_setting);
        }
  
        // 行の終了判定を行う関数
        matchLineEnd(position) {
          // 設定した文字が現れた場合、行の終わりとみなす
          return  this.matchStringList(position,this.line_end_setting);
        }
        getUnprocessedSource(){
          return this.source.substring(this.position);
        }
  
        // ヘルパー関数：空白文字を無視する
        parseSkipWhitespace() {
            while (this.position < this.source.length && /\s/.test(this.source[this.position])) {
              this.position++;
            }
        }
        parseTime() {
            const pattern = /(\d{1,2})\/(\d{1,2})\/(\d{1,2})|(\d{1,2})月(\d{1,2})日|(\d{1,2}):(\d{1,2}):(\d{1,2})/;
            const match = this.source.match(pattern);
          
            if (match) {
              const result = {};
          
              if (match[1] && match[2] && match[3]) {
                result.date = {
                  month: parseInt(match[1], 10),
                  day: parseInt(match[2], 10),
                  year: parseInt(match[3], 10)
                };
              } else if (match[4] && match[5]) {
                result.date = {
                  month: parseInt(match[4], 10),
                  day: parseInt(match[5], 10)
                };
              }
          
              if (match[6] && match[7] && match[8]) {
                result.time = {
                  hour: parseInt(match[6], 10),
                  minute: parseInt(match[7], 10),
                  second: parseInt(match[8], 10)
                };
              }
          
              const end_position = match.index + match[0].length;
              result.endPos = end_position;
          
              return result;
            }
          
            return null;
          }
        // トークンをパースするヘルパー関数
        parseToken() {
          this.parseSkipWhitespace();
          let start_position = this.position;
          let end_position = this.position;
          
          while (end_position < this.source.length && !this.matchStringList(end_position,this.token_end_setting)) {
            end_position++;
          }
          const token = this.source.substring(start_position, end_position);
          this.position = end_position;
          return token;
        }
        parseStringList(match_list) {
          this.parseSkipWhitespace();
          const currentText = this.source.substring(this.position);
  
          for (const condition of match_list) {
            if (currentText.startsWith(condition)) {
              const token = this.source.substring(this.position,this.position + condition.length);
              this.position = this.position + token.length;
              return token;
            }
          }
          return "";
        }
          
        // 条件文を解析するパーサー関数
        parseCondition(end_element_list = []) {
          this.parseSkipWhitespace();
          return this.parseExpression(end_element_list);
        }
  
        // 文を解析するパーサー関数
        parseStatement(end_element_list = []) {
          this.parseSkipWhitespace();
          // 現在はif文かfor文のどちらかのみをサポートしています
          var statement =this.parseIfStatement();
          if (statement) {return statement;}
  
          statement = this.parseForStatement();
          if (statement) {return statement;}
  
          // 仮作成 end_element_listに到達したら終了。
          if (end_element_list !== [] && this.matchStringList(this.position,end_element_list)) {
            return {};
          }
          return this.parseExpression(end_element_list);
        }
  
        // 式を解析するパーサー関数
        parseExpression(end_element_list = []) {
          let tokens = [];
          let start_position = this.position;
          while (this.position < this.source.length) {
            this.parseSkipWhitespace();
            if (this.matchStringList(this.position,end_element_list)){
              break;
            }
            if (this.matchExpressionEnd(this.position)) {
              break;
            }
            const token = this.parseToken();
            if( token == ""){ break;} 
            if( token == ''){ break;} 
            tokens.push(token);
          }
          this.parseSkipWhitespace();
          //文の終了文字(;,。等)は文の一部なのでtokenに加える。
          //ただし、それが文法要素の場合(for(a;b;c)等)tokenに加えない。
          if(this.matchStringList(this.position,end_element_list )==false){
            const token = this.parseStringList(this.expression_end_setting);
            if( token != ""){ tokens.push(token);}   
          }
          return {
            type: "Expression",
            tokens,
            endPos: this.position
          };
        }
        parseWithParseSetting(setting) {
          const start_position = this.position; 
          let parsed_result ={ ...(setting.parsed_result || {})};
          let flag_match = false;
          for (const element of setting.parsing_rule_list) {
              let end_element_list = [];
              if ("end_element_list" in element) {
                end_element_list = element.end_element_list
              } else {
                end_element_list =[];
              }
              this.parseSkipWhitespace();
              if (element.type === "key" ) {
                if (this.matchString(element.key)){
                  this.position += element.key.length;
                  if (!parsed_result.hasOwnProperty("tokens")) {
                    parsed_result["tokens"] = [];
                  }
                  parsed_result["tokens"].push(element.key);
                  flag_match=true;
                }else if( element.must_element) {
                  this.position = start_position;
                  if(flag_match ==true){
                    saveDictionaryToJSONFile("analyze_error.json",parsed_result,true);
                  }
                  return null; // 要素が見つからない場合はnullを返すなど適切な処理を行う
                }else{
                  this.position ++;
                }
              } else if (element.type === "declaration_expression") {
                const condition = this.parseCondition(end_element_list);
                if (condition){
                  parsed_result.declaration = condition;
                  flag_match=true;
                }else if(element.must_element) {
                  this.position = start_position;
                  if(flag_match ==true){
                    saveDictionaryToJSONFile("analyze_error.json",parsed_result,true);
                  }
                  return null; // 要素が見つからない場合はnullを返すなど適切な処理を行う
                }else{
                  this.position ++;
                }
              } else if (element.type === "condition_expression") {
                const condition = this.parseCondition(end_element_list);
                if (condition){
                  parsed_result.condition = condition;
                  flag_match=true;
                }else if(element.must_element) {
                  this.position = start_position;
                  if(flag_match ==true){
                    saveDictionaryToJSONFile("analyze_error.json",parsed_result,true);
                  }
                  return null; // 要素が見つからない場合はnullを返すなど適切な処理を行う
                }else{
                  this.position ++;
                }
              } else if (element.type === "incrementors_expression") {
                const condition = this.parseCondition(end_element_list);
                if (condition){
                  parsed_result.incrementors = condition;
                  flag_match=true;
                }else if(element.must_element) {
                  this.position = start_position;
                  if(flag_match ==true){
                    saveDictionaryToJSONFile("analyze_error.json",parsed_result,true);
                  }
                  return null; // 要素が見つからない場合はnullを返すなど適切な処理を行う
                }else{
                  this.position ++;
                }  
              } else if (element.type === "statement_expression") {
                const statement = this.parseStatement(end_element_list);
                if (statement ){
                  parsed_result.statement = statement;
                  flag_match=true;
                }
                else if(element.must_element) {
                  this.position = start_position;
                  if(flag_match ==true){
                    saveDictionaryToJSONFile("analyze_error.json",parsed_result,true);
                  }
                  return null; // 要素が見つからない場合はnullを返すなど適切な処理を行う
                }else{
                  this.position ++;
                }
  
              } else if (element.type === "parts") {
                const parts_result = this.parseWithParseSetting(element);
                if (parts_result){
                  //Object.assign(parsed_result, parts_result);
                  parsed_result = mergeDictionaries(parsed_result, parts_result)
                  flag_match=true;
                }
                else if(element.must_element) {
                  this.position = start_position;
                  saveDictionaryToJSONFile("analyze_error.json",parsed_result,true);
                  return null; // 要素が見つからない場合はnullを返すなど適切な処理を行う
                }else{
                  this.position ++;
                }
              }
          }
          return parsed_result;
        }
        parseIfStatement() {
          var start_position = this.position;
          //this.parseSkipWhitespace();
          var result = this.parseWithParseSetting(this.if_parse_setting);
  
          if (!result) {
            this.position = start_position;
  
            return null; // パース失敗時はnullを返すなど適切な処理を行う
          }
          return result;
        }
  
        // for文を解析するパーサー関数
        parseForStatement() {
          var start_position = this.position;
          //this.parseSkipWhitespace();
          var result = this.parseWithParseSetting(this.for_parse_setting);
  
          if (!result) {
            this.position = start_position;
            return null; // パース失敗時はnullを返すなど適切な処理を行う
          }
          return result;
        }
        // 複数の文を処理する関数
        parseMultipleStatements() {
          const statements = [];
  
          while (this.position < this.source.length) {
            const statement = this.parseStatement();
  
            // パース結果を文のリストに追加
            statements.push(statement);
  
            // 区切り文字（例: セミコロン）が現れたら次の文に進む
            if (this.matchString(";")) {
              this.position++;
              continue;
            }
            const current_char = this.source[this.position];
  
            // 文末文字が現れたら次の文に進む
            if (this.matchExpressionEnd(this.position)) {
              this.position++;
              continue;
            }
  
            // 改行文字が現れたら次の文に進む
            if (this.matchLineEnd(this.position)) {
              this.position++;
              continue;
            }
            //仮対応
            this.position++;
  
            // それ以外の場合は文の区切りが終わったとみなし、処理を終了
            //break;
          }
  
          return {
            type: "MultipleStatements",
            statements
          };
        }
        // パースを開始する関数
        parse() {
          try {
            const ast = this.parseMultipleStatements();
            return {
              success: true,
              ast: ast
            };
          } catch (error) {
            return {
              success: false,
              error: error.message
            };
          }
        }
      }