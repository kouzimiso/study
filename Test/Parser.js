    // パーサーコンビネータークラス
    class Parser {
        constructor(input) {
          this.input = input;
          this.position = 0;
          this.token_end_setting =      ["\n","\r\n",")","}","]","'","'",";"," ","　","\t"]
          this.expression_end_setting = ["\n","\r\n",")","}","]","'","'",";"]
          this.line_end_setting = ["\n","\r\n"]
          this.statement_keyword_setting = ["if","for","while"]
          this.if_parse_setting = {
            "parsed_result":{"type":"IfStatement"},
            "parsing_rules":[
              {"type":"key","key":"if", "must_element":true},
              {
                "type":"parts",
                "parsing_rules":[
                  {"type":"key","key":"(", "must_element":false},
                  {"type":"condition_expression", "must_element":true ,"end_element_list":[")"]},
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
            "parsing_rules":[
              {"type":"key","key":"for", "must_element":true},
              {
                "type":"parts",
                "parsing_rules":[
                  {"type":"key","key":"(", "must_element":false},
                  {"type":"declaration_expression", "must_element":true},
                  {"type":"key","key":";", "must_element":false},
                  {"type":"condition_expression", "must_element":true},
                  {"type":"key","key":";", "must_element":false},
                  {"type":"incrementors_expression", "must_element":true},
                  {"type":"key","key":")", "must_element":false}
  
                ],
                "must_element":true
              },
              {"type":"key","key":"{", "must_element":true},
              {"type":"statement_expression",},
              {"type":"key","key":"}", "must_element":true}
            ]
  
          }
        }
        // ヘルパー関数：指定された文字列がマッチするかどうかをチェックする
        matchString(match_word) {
          if (this.input.substring(this.position, this.position + match_word.length) === match_word) {
            return true;
          }
          return false;
        }
        matchStringList(position, match_list) {
          const currentText = this.input.substring(position);
  
          for (const condition of match_list) {
            if (currentText.startsWith(condition)) {
              return true;
            }
          }
          return false;
        }
  
        // 空白の判定を行う関数
        matchWhiteSpace(position) {
          return /\s/.test(this.input[position]);
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
        getUnprocessedInput(){
          return this.input.substring(this.position);
        }
  
        // ヘルパー関数：空白文字を無視する
        parseSkipWhitespace() {
            while (this.position < this.input.length && /\s/.test(this.input[this.position])) {
              this.position++;
            }
        }
  
        // トークンをパースするヘルパー関数
        parseToken() {
          this.parseSkipWhitespace();
          let start_position = this.position;
          let end_position = this.position;
          
          while (end_position < this.input.length && !this.matchStringList(end_position,this.token_end_setting)) {
            end_position++;
          }
          const token = this.input.substring(start_position, end_position);
          this.position = end_position;
          return token;
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
          while (this.position < this.input.length) {
            this.parseSkipWhitespace();
            if (this.matchStringList(this.position,end_element_list)){
              break;
            }
            if (this.matchExpressionEnd(this.position)) {
              break;
            }
            const token = this.parseToken();
            if( token.token === ""){ break;} 
            tokens.push(token);
          }
  
          return {
            type: "Expression",
            tokens,
            endPos: this.position
          };
        }
        parseWithParseSetting(setting) {
          const start_position = this.position; 
          let parsed_result = setting.parsed_result || {};
          for (const element of setting.parsing_rules) {
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
                  
                }else if( element.must_element) {
                  this.position = start_position;
                  return null; // 要素が見つからない場合はnullを返すなど適切な処理を行う
                }else{
                  this.position ++;
                }
              } else if (element.type === "condition_expression") {
                const condition = this.parseCondition(end_element_list);
                if (condition){
                  parsed_result.condition = condition;
                }else if(element.must_element) {
                  this.position = start_position;
                  saveDictionaryToJSONFile("analyze_error.json",parsed_result,true);
                  return null; // 要素が見つからない場合はnullを返すなど適切な処理を行う
                }else{
                  this.position ++;
                }
  
              } else if (element.type === "statement_expression") {
                const statement = this.parseStatement(end_element_list);
                if (statement ){
                  parsed_result.statement = statement;
                }
                else if(element.must_element) {
                  this.position = start_position;
                  saveDictionaryToJSONFile("analyze_error.json",parsed_result,true);
                  return null; // 要素が見つからない場合はnullを返すなど適切な処理を行う
                }else{
                  this.position ++;
                }
  
              } else if (element.type === "parts") {
                const parts_result = this.parseStatement();
                if (parts_result){
                  //Object.assign(parsed_result, parts_result);
                  parsed_result = mergeDictionaries(parsed_result, parts_result)
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
  
          while (this.position < this.input.length) {
            const statement = this.parseStatement();
  
            // パース結果を文のリストに追加
            statements.push(statement);
  
            // 区切り文字（例: セミコロン）が現れたら次の文に進む
            if (this.matchString(";")) {
              this.position++;
              continue;
            }
            const current_char = this.input[this.position];
  
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