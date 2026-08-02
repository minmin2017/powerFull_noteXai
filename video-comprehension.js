// Video comprehension: fetch YouTube pages + analyze hardware content via Claude API
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic();

const CHAT_URL = 'http://localhost:4321/api/chat';
const SECTION = 'main';

const VIDEOS = [
  // Robotic Arm
  { url: 'https://www.youtube.com/watch?v=nTJsVvWFUVE', label: 'Robot Arm Ultimate Guide (5 Builds)' },
  { url: 'https://www.youtube.com/watch?v=UF73iIe3LsY', label: 'ROS 2 3-DOF Robotic Arm Digital Twin' },
  { url: 'https://www.youtube.com/watch?v=p6YIkDhPNyo', label: 'AI Robot Arm Beginner Full Course' },
  { url: 'https://www.youtube.com/watch?v=F0ZvF-FbCr0', label: 'DIY Arduino Robot Arm (Hand Gestures)' },
  { url: 'https://www.youtube.com/watch?v=OiQKw0lZ5Rw', label: '3D Printed Robot Arm Arduino' },
  // Drone
  { url: 'https://www.youtube.com/watch?v=kpuY1lb3BE8', label: 'Build FPV Drone 2024' },
  { url: 'https://www.youtube.com/watch?v=8ZU2RFVAdU0', label: 'Introduction to Drone Components' },
  { url: 'https://www.youtube.com/watch?v=ndUVyEo2URM', label: 'FPV Drone Parts Explained Simply' },
  { url: 'https://www.youtube.com/watch?v=zj90LK8XR68', label: 'Build 5-Inch FPV Drone GEPRC Mark5' },
];

async function postChat(text) {
  try {
    const res = await fetch(CHAT_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ section: SECTION, text }),
    });
    if (!res.ok) console.error('chat post failed:', res.status);
  } catch (e) {
    console.error('chat post error:', e.message);
  }
}

async function analyzeVideo(video) {
  const stream = await client.messages.stream({
    model: 'claude-opus-4-8',
    max_tokens: 4096,
    thinking: { type: 'adaptive' },
    tools: [{ type: 'web_fetch_20260209', name: 'web_fetch' }],
    messages: [
      {
        role: 'user',
        content: `Fetch this YouTube video page and analyze the hardware content:\n${video.url}\n\nExtract and report in Thai:\n1. ชื่อวิดีโอและช่องที่โพสต์\n2. Hardware components ที่กล่าวถึง (ชิ้นส่วน, อุปกรณ์, บอร์ด, เซ็นเซอร์)\n3. Software/firmware/libraries ที่ใช้\n4. Code snippets หรือ commands ที่ปรากฏในคำอธิบาย\n5. ขั้นตอนการประกอบหรือ workflow หลัก\n6. ลิงก์เพิ่มเติมที่น่าสนใจจาก description\n\nสรุปให้กระชับและเป็นประโยชน์สำหรับนักพัฒนาที่ต้องการสร้าง hardware จริง`,
      },
    ],
  });

  const finalMsg = await stream.finalMessage();

  let result = '';
  for (const block of finalMsg.content) {
    if (block.type === 'text') result += block.text;
  }
  return result || '(ไม่มีข้อความ)';
}

async function main() {
  await postChat('🤖 เริ่มวิเคราะห์ video hardware ทั้งหมด 9 คลิป (แขนกล 5 + Drone 4)...\nกำลังใช้ Claude API + web_fetch อาจใช้เวลาสักครู่');

  const robotArmResults = [];
  const droneResults = [];

  for (let i = 0; i < VIDEOS.length; i++) {
    const v = VIDEOS[i];
    const category = i < 5 ? 'แขนกล' : 'Drone';
    console.log(`[${i+1}/9] Analyzing: ${v.label}`);
    await postChat(`⏳ [${i+1}/9] กำลังวิเคราะห์ ${category}: ${v.label}`);

    try {
      const analysis = await analyzeVideo(v);
      const formatted = `\n### ${i+1}. ${v.label}\n${v.url}\n\n${analysis}`;
      if (i < 5) {
        robotArmResults.push(formatted);
      } else {
        droneResults.push(formatted);
      }
      await postChat(`✅ [${i+1}/9] เสร็จ: ${v.label}`);
    } catch (err) {
      console.error(`Error analyzing ${v.label}:`, err.message);
      const errMsg = `❌ วิเคราะห์ไม่ได้: ${v.label} — ${err.message}`;
      if (i < 5) robotArmResults.push(errMsg);
      else droneResults.push(errMsg);
    }
  }

  // Send full robot arm summary
  const robotSummary = `## 🦾 สรุป Video แขนกล (Robotic Arm)\n${robotArmResults.join('\n\n---\n')}`;
  await postChat(robotSummary);

  // Send full drone summary
  const droneSummary = `## 🚁 สรุป Video Drone\n${droneResults.join('\n\n---\n')}`;
  await postChat(droneSummary);

  await postChat('✨ วิเคราะห์ครบทั้ง 9 คลิปแล้ว! ข้อมูล hardware ครบทั้ง แขนกล และ Drone อยู่ด้านบน');
  console.log('Done!');
}

main().catch(async (err) => {
  console.error('Fatal error:', err);
  await postChat(`❌ เกิดข้อผิดพลาด: ${err.message}`);
  process.exit(1);
});
