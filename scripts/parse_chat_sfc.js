const fs = require('fs');
const path = require('path');
const { parse } = require('@vue/compiler-sfc');
const file = path.join(__dirname, '..', 'frontend', 'src', 'views', 'Chat.vue');
const content = fs.readFileSync(file, 'utf8');
try {
  const res = parse(content);
  console.log('PARSED_OK');
} catch (e) {
  console.error('PARSE_ERROR');
  console.error(e && e.message);
  if (e && e.loc) console.error('LOC', JSON.stringify(e.loc));
  process.exit(2);
}
