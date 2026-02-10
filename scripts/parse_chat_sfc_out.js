const fs = require('fs');
const path = require('path');
const { parse } = require('@vue/compiler-sfc');
const file = path.join(__dirname, '..', 'frontend', 'src', 'views', 'Chat.vue');
const out = path.join(__dirname, 'parse_result.json');
const content = fs.readFileSync(file, 'utf8');
let result = { ok: false };
try {
  const res = parse(content);
  result.ok = true;
  result.descriptor = {
    template: !!res.descriptor.template,
    script: !!res.descriptor.script,
    styles: res.descriptor.styles.length
  };
} catch (e) {
  result.ok = false;
  result.error = e && (e.message || String(e));
  if (e && e.loc) result.loc = e.loc;
}
fs.writeFileSync(out, JSON.stringify(result, null, 2), 'utf8');
console.log('WROTE', out);
