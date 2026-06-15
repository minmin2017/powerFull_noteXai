// listen.js - Polling script to monitor Powerfull Note inbox
// This script checks for new messages from the user every 2 seconds.

const PORT = process.env.PORT || 4321;
const URL = `http://localhost:${PORT}/api/inbox?drain=true`;

console.log(`\n  👂 Listening for messages from Powerfull Note...`);
console.log(`  Target: ${URL}\n`);

async function poll() {
  try {
    const res = await fetch(URL);
    if (res.ok) {
      const { items } = await res.json();
      if (items && items.length > 0) {
        items.forEach(item => {
          const time = new Date(item.ts).toLocaleTimeString();
          console.log(`\x1b[36m[${time}] User:\x1b[0m ${item.text}`);
        });
      }
    }
  } catch (err) {
    if (err.code === 'ECONNREFUSED') {
      // Server not running yet, just wait silently
    } else {
      console.error('Error polling inbox:', err.message);
    }
  }
  setTimeout(poll, 2000);
}

poll();
