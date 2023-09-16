// Import the babel parser package
// const babelParser = require("@babel/parser"); // これはエラーになる
requirejs(["@babel/parser"], function(babelParser) { // これならOK
    // Get the file input element and the output element
    const fileInput = document.getElementById("file-input");
    const output = document.getElementById("output");
  
    // Add an event listener for file selection
    fileInput.addEventListener("change", function() {
      // Get the selected file
      const file = fileInput.files[0];
      // Check if the file is a JavaScript file
      if (file && file.name.endsWith(".js")) {
        // Create a file reader
        const reader = new FileReader();
        // Add an event listener for file reading
        reader.addEventListener("load", function() {
          // Get the file content as a string
          const code = reader.result;
          // Generate the AST from the code
          const ast = generateAST(code);
          // Convert the AST to JSON format
          const json = convertToJSON(ast);
          // Display the JSON in the output element
          output.textContent = json;
        });
        // Read the file as text
        reader.readAsText(file);
      } else {
        // Clear the output element
        output.textContent = "";
      }
    });
  
    // Define a function to generate the AST from the code
    function generateAST(code) {
      // Parse the code using babel parser and return the AST
      return babelParser.parse(code);
    }
  
    // Define a function to convert the AST to JSON format
    function convertToJSON(ast) {
      // Stringify the AST with indentation and return the JSON string
      return JSON.stringify(ast, null, 2);
    }
  });
  