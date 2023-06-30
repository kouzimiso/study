const fs = require('fs');
const esprima = require('esprima');

const filename = 'analyze.js';

fs.readFile(filename, 'utf8', (err, code) => {
  if (err) {
    console.error('Error reading file:', err);
    return;
  }

  const ast = esprima.parse(code);
  const jsonData = JSON.stringify(ast, null, 2);

  fs.writeFile('analysis_result.json', jsonData, 'utf8', (err) => {
    if (err) {
      console.error('Error writing file:', err);
      return;
    }
    console.log('Analysis result saved as analysis_result.json');
  });
});
