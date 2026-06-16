import fs from 'node:fs';
const env = fs.readFileSync('.env', 'utf8');
const key = env.split('\n').find(l => l.startsWith('GOOGLE_API_KEY')).split('=')[1].trim();

async function list() {
  const url = `https://generativelanguage.googleapis.com/v1/models?key=${key}`;
  try {
    const res = await fetch(url);
    const data = await res.json();
    console.log(JSON.stringify(data, null, 2));
  } catch (e) {
    console.error(e.message);
  }
}
list();
