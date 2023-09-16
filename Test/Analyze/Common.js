//Table表示関数----------------------------------------
    // 辞書形式のリストをテーブル形式で表示する
    function displayTable(dictionary_data_list, element, flag_search_id, browser_IE) {
      var table = createTable(dictionary_data_list, browser_IE);
      //var table = createTable(dictionary_data_list, true);
      var display_element = flag_search_id ? document.getElementById(element) : document.getElementsByTagName(element)[0];
      display_element.innerHTML = "";
      display_element.appendChild(table);
    }

    // 辞書形式のリストからテーブルを作成する
    function createTable(data, browser_IE) {
      var table = document.createElement("table");
      var keys = getKeysIE(data);
      keys.sort();
      var headerRow = document.createElement("tr");
      
      for (var i = 0; i < keys.length; i++) {
        var headerCell = document.createElement("th");
        headerCell.innerText = keys[i];
        headerRow.appendChild(headerCell);
      }

      if (browser_IE) {
        // IEの場合はtbodyを使用する
        var tbody = document.createElement("tbody");
        tbody.appendChild(headerRow);
      } else {
        // IE以外の場合はtbodyを使用しない
        table.appendChild(headerRow);
      }

      if (isArray(data)) {
        for (var j = 0; j < data.length; j++) {
          array_read_data = data[j];
          dataRow =createRowByDictionary(array_read_data,keys);
          if (browser_IE) {
            // IEの場合はtbodyを使用する
            tbody.appendChild(dataRow);
          } else {
            // IE以外の場合はtbodyを使用しない
            table.appendChild(dataRow);
          }
        }
      } else if (typeof data === "object" && data !== null) {
        dataRow =createRowByDictionary(data,keys)

        if (browser_IE) {
          // IEの場合はtbodyを使用する
          tbody.appendChild(dataRow);
        } else {
          // IE以外の場合はtbodyを使用しない
          table.appendChild(dataRow);
        }
      } else {
        var dataRow = document.createElement("tr");
        var dataCell = document.createElement("td");
        dataCell.colSpan = keys.length;
        dataCell.innerText = data;
        dataRow.appendChild(dataCell);

        if (browser_IE) {
          // IEの場合はtbodyを使用する
          tbody.appendChild(dataRow);
        } else {
          // IE以外の場合はtbodyを使用しない
          table.appendChild(dataRow);
        }
      }
      if (browser_IE) {
        table.appendChild(tbody);
      }
      return table;
    }
    function createRowByDictionary(data,keys){
      var dataRow = document.createElement("tr");
      for (var k = 0; k < keys.length; k++) {
        var dataCell = document.createElement("td");
        var value = data[keys[k]];
        if (typeof value === "object" && value !== null) {
          var subTable = createTable(value);
          dataCell.appendChild(subTable);
        } else {
          dataCell.innerText = value;
        }
        dataRow.appendChild(dataCell);
      }
    return dataRow;
  }

//汎用関数----------------------------------------
    // 辞書形式のリストからキーを取得する
    function getKeys(data) {
      var keys = [];
      if (Array.isArray(data)) {
        for (var i = 0; i < data.length; i++) {
          var objKeys = Object.keys(data[i]);
          keys = keys.concat(objKeys);
        }
      } else if (typeof data === "object" && data !== null) {
        keys = Object.keys(data);
      }
      keys = Array.from(new Set(keys));
      return keys;
    }
    function getKeysIE(data) {
      var keys = [];
      if (isArray(data)) {
        for (var i = 0; i < data.length; i++) {
          var objKeys = getObjectKeys(data[i]);
          keys = keys.concat(objKeys);
        }
      } else if (typeof data === "object" && data !== null) {
        keys = getObjectKeys(data);
      }
      keys = getUniqueArray(keys);
      return keys;
    }
    function isArray(obj) {
      return Object.prototype.toString.call(obj) === "[object Array]";
    }
    function getObjectKeys(obj) {
      var keys = [];
      for (var key in obj) {
        if (obj.hasOwnProperty(key)) {
          keys.push(key);
        }
      }
      return keys;
    }
    function getUniqueArray(arr) {
      var uniqueArr = [];
      for (var i = 0; i < arr.length; i++) {
        var isDuplicate = false;
        for (var j = 0; j < uniqueArr.length; j++) {
          if (arr[i] === uniqueArr[j]) {
            isDuplicate = true;
            break;
          }
        }
        if (!isDuplicate) {
          uniqueArr.push(arr[i]);
        }
      }
      return uniqueArr;
    }

      // オブジェクトが空かどうかをチェックする関数
      function isObjectEmpty(obj) {
        for (var key in obj) {
          if (obj.hasOwnProperty(key)) {
            return false;
          }
        }
        return true;
      }
      function isObjectExist(obj, browser_IE) {
        if (browser_IE) {
          for (var key in obj) {
            if (obj.hasOwnProperty(key)) {
              return true;
            }
          }
          return false;
        } else {
          return Object.keys(obj).length != 0;
        }
      }
      //文字列表示関数
      function displayString(line, element, flag_search_id) {
        var display_element = flag_search_id ? document.getElementById(element) : document.getElementsByTagName(element)[0];
        display_element.innerHTML = "<p>" + line + "</p>";
      }
      //文字列追記関数
      function displayAddString(line, element, flag_search_id) {
        var display_element = flag_search_id ? document.getElementById(element) : document.getElementsByTagName(element)[0];
        display_element.innerHTML += "<p>" + line + "</p>";
      }
      //文字列表示関数(配列の表示。配列を変更すればいいので追記の関数は用意しない。)
      function displayArray(lines, element, flag_search_id) {
        var display_element = flag_search_id ? document.getElementById(element) : document.getElementsByTagName(element)[0];
        var displayLines = lines.join('<br>');
        display_element.innerHTML = displayLines;
      }
  
      // リンク追記関数
      function displayLink(path, label_text, element, search_id) {
        var display_element = search_id ? document.getElementById(element) : document.getElementsByTagName(element)[0];
        var link = document.createElement('a');
        link.href = path;
        link.innerText = label_text;
        display_element.appendChild(link);
      }
      //ブラウザ種類判別関数
      function getBrowserType() {
        var browser_type = "";
        if (navigator.appName === "Microsoft Internet Explorer") {
          return browser_type = "Internet Explorer";
        }
        var agent = window.navigator.userAgent;
        agent = agent.toLowerCase();
        if (agent.indexOf("msie") != -1 || agent.indexOf("trident") != -1) {
          browser_type = "Internet Explorer";
        } else if (agent.indexOf("edg") != -1 || agent.indexOf("edge") != -1) {
          browser_type = "Edge";
        } else if (agent.indexOf("opr") != -1 || agent.indexOf("opera") != -1) {
          browser_type = "Opera";
        } else if (agent.indexOf("chrome") != -1) {
          browser_type = "Chrome";
        } else if (agent.indexOf("safari") != -1) {
          browser_type = "Safari";
        } else if (agent.indexOf("firefox") != -1) {
          browser_type = "FireFox";
        } else if (agent.indexOf("opr") != -1 || agent.indexOf("opera") != -1) {
          browser_type = "Opera";
        }
        return browser_type;
      }
      function parseJSON(jsonString) {
        if (typeof jsonString !== 'string' || jsonString === '') {
          return null;
        }
  
        // JSONをパースするためにevalを使用します
        // evalは注意が必要なので、信頼できるソースからのみ使用してください
        try {
          // JSON文字列をJavaScriptのオブジェクトに変換するため、
          // 先頭と末尾に括弧を追加してevalします
          return eval('(' + jsonString + ')');
        } catch (error) {
          console.error('JSONのパース中にエラーが発生しました:', error);
          return null;
        }
      }
  
      // 辞書のJSON文字列化関数
      function convertDictionaryToJSON(obj) {
        var json_string = '{';
        var is_first_property = true;
        for (var key in obj) {
          if (obj.hasOwnProperty(key)) {
            if (!is_first_property) {
              json_string += ',';
            }
            json_string += '"' + key + '":"' + obj[key] + '"';
            is_first_property = false;
          }
        }
        json_string += '}';
        return json_string;
      }
      function deepCopy(obj) {
        if (typeof obj !== 'object' || obj === null) {
          return obj;
        }
        var newObj = Array.isArray(obj) ? [] : {};
        for (var key in obj) {
          if (obj.hasOwnProperty(key)) {
            newObj[key] = deepCopy(obj[key]);
          }
        }
        return newObj;
      }
  
      // ファイル保存関数
      function saveToFile(file_name, content) {
        var downloadLink = document.createElement('a');
        downloadLink.href = 'data:text/plain;charset=utf-8,' + encodeURIComponent(content);
        downloadLink.download = file_name;
        downloadLink.style.display = 'none';
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);
      }
      // ファイル保存関数(IE専用)
      function saveToFileIE(file_name, content) {
        var file_system = new ActiveXObject("Scripting.FileSystemObject");
        var file_stream = file_system.CreateTextFile(file_name, true);
        file_stream.Write(content);
        file_stream.Close();
      }
