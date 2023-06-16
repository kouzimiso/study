function testFunction(){
  var expected_result = "x == 5;y == 6;";
  var test_code ="x == 5;y == 6;";
  var result = test_code.substring(0);
  testDisplay("result-output","substring(0)"+test_code,expected_result,result);
  expected_result = " == 5;y == 6;";
  test_code ="x == 5;y == 6;";
  result = test_code.substring(1);
  testDisplay("result-output","substring(1)"+test_code,expected_result,result);
  expected_result = ";y == 6;";
  test_code ="x == 5;y == 6;";
  result = test_code.substring(6);
  testDisplay("result-output","substring(6)"+test_code,expected_result,result);


  parser =new Parser();
  test_code="  test"
  expected_result = "test";
  parser.input = test_code;
  parser.position = 0;

  parser.parseSkipWhitespace();
  result = parser.getUnprocessedInput();
  testDisplay("result-output","parseSkipWhitespace_"+test_code,expected_result,result);
  var test_parse_setting = {
      "parsed_result":{"type":"IfStatement"},
      "parsing_rules":[
        {"type":"key","key":"if", "must_element":true},
        {"type":"key","key":"(", "must_element":false},
        {"type":"condition_expression", "must_element":true ,"end_element_list":[")"]},
        {"type":"key","key":")", "must_element":false},
        /*
        {
          "type":"parts",
          "parsing_rules":[
            {"type":"key","key":"(", "must_element":false},
            {"type":"condition_expression", "must_element":true ,"end_element_list":[")"]},
            {"type":"key","key":")", "must_element":false}
          ],
          "must_element":true
        },
        */
        {"type":"key","key":"{", "must_element":true},
        {"type":"statement_expression" ,"end_element_list":["}"]},
        {"type":"key","key":"}", "must_element":true}
      ]

    }
  test_code="if(a = 2){}"
  expected_result = {
    "token": [
      "if",
      "(",
      ")",
      "{",
      "}"
    ]
  };
  parser.input = test_code;
  parser.position = 0;

  result = parser.parseWithParseSetting(test_parse_setting);
  expected_result = JSON.stringify(expected_result, null, 2);
  result = JSON.stringify(result, null, 2);
  testDisplay("result-output","parseWithParseSetting_"+test_code,expected_result,result);

  testFunction2();
}

    function testFunction2() {
      // Test cases
        const testCases = [
        {
          code: "abc",
          expected: true,
          test_function: "matchString",
          arguments: ["abc"]
        },
        {
          code: "123",
          expected: true,
          test_function: "matchStringList",
          arguments: [0, ["123", "456"]]
        },
        {
          code: " ",
          expected: true,
          test_function: "matchWhiteSpace",
          arguments: [0]
        },
        {
          code: ";",
          expected: true,
          test_function: "matchExpressionEnd",
          arguments: [0]
        },
        {
          code: "\n",
          expected: true,
          test_function: "matchLineEnd",
          arguments: [0]
        },
        {
          code: "abc 123",
          expected:  "abc",
          test_function: "parseToken",
          arguments: [0]
        },
        {
          code: "x == 5;y == 6;",
          expected: {
            type: "Expression",
            tokens: ["x","==","5"],
            endPos: 6
          },
          test_function: "parseCondition",
          arguments: []
        },
        {
          code: "if (x == 5) { return 1; }",
          expected: {
            type: "IfStatement",
            condition: {
              type: "Expression",
              tokens: ["x","==","5"],
              endPos: 10
            },
            statement: {
              type: "MultipleStatements",
              statements: [
                {
                  type: "Expression",
                  tokens: ["return", "1"],
                  endPos: 21
                }
              ]
            }
          },
          test_function: "parseStatement",
          arguments: []
        }
      ];
      parser =new Parser();
      for (const testCase of testCases) {
        const { code, expected, test_function, arguments } = testCase;
        parser.input = code;
        parser.position = 0;
        let result = parser[test_function](...arguments);
        testDisplay(
          "result-output",
          `${test_function}_${code}`,
          JSON.stringify(expected),
          JSON.stringify(result)
        );

      }

    }
    function testDisplay(element_id,test_label,expected_result,result){
      var testResultsContainer = document.getElementById(element_id);
      var testResult = document.createElement('p');
      testResult.textContent = 'test_label: ' + test_label + ' | Expected: ' + expected_result + ' | Result: ' + result; 
      testResult.style.color = (result === expected_result )? 'green' : 'red'; 
      testResultsContainer.appendChild(testResult);
    }