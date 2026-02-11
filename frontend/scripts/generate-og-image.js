/**
 * Open Graph Image Generator
 *
 * Generates social media preview images (og-image.png, twitter-card.png)
 * using Canvas API
 *
 * Requirements:
 *   npm install canvas
 *
 * Usage:
 *   node scripts/generate-og-image.js
 */

const { createCanvas, loadImage, registerFont } = require('canvas');
const fs = require('fs');
const path = require('path');

// Configuration
const config = {
  ogImage: {
    width: 1200,
    height: 630,
    output: 'public/og-image.png'
  },
  twitterCard: {
    width: 1200,
    height: 600,
    output: 'public/twitter-card.png'
  }
};

// Colors (matching the brand)
const colors = {
  background: '#0f172a',  // slate-950
  primary: '#4f46e5',     // indigo-600
  secondary: '#10b981',   // emerald-500
  text: '#ffffff',
  textSecondary: '#94a3b8' // slate-400
};

async function generateOGImage() {
  console.log('🎨 Generating Open Graph image...\n');

  try {
    // Create canvas
    const canvas = createCanvas(config.ogImage.width, config.ogImage.height);
    const ctx = canvas.getContext('2d');

    // Background
    ctx.fillStyle = colors.background;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Gradient overlay
    const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
    gradient.addColorStop(0, 'rgba(79, 70, 229, 0.1)');
    gradient.addColorStop(1, 'rgba(16, 185, 129, 0.1)');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw decorative elements (abstract flow diagram)
    drawDecorativeFlow(ctx);

    // Title
    ctx.fillStyle = colors.text;
    ctx.font = 'bold 72px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Archboard', canvas.width / 2, 240);

    // Subtitle
    ctx.fillStyle = colors.textSecondary;
    ctx.font = '36px sans-serif';
    ctx.fillText('AI-Powered Architecture Design Platform', canvas.width / 2, 310);

    // Features
    ctx.font = '28px sans-serif';
    ctx.fillStyle = colors.primary;
    const features = [
      '✨ Natural Language to Diagram',
      '🎨 React Flow + Excalidraw',
      '🤖 Multi-Provider AI Integration'
    ];

    features.forEach((feature, index) => {
      ctx.fillText(feature, canvas.width / 2, 400 + index * 50);
    });

    // Save
    const buffer = canvas.toBuffer('image/png');
    fs.writeFileSync(path.join(__dirname, '..', config.ogImage.output), buffer);
    console.log(`✅ Generated: ${config.ogImage.output} (${config.ogImage.width}x${config.ogImage.height})`);

  } catch (error) {
    console.error('❌ Error generating Open Graph image:', error);
  }
}

async function generateTwitterCard() {
  console.log('🐦 Generating Twitter Card image...\n');

  try {
    // Create canvas
    const canvas = createCanvas(config.twitterCard.width, config.twitterCard.height);
    const ctx = canvas.getContext('2d');

    // Background
    ctx.fillStyle = colors.background;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Gradient overlay
    const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
    gradient.addColorStop(0, 'rgba(79, 70, 229, 0.15)');
    gradient.addColorStop(1, 'rgba(16, 185, 129, 0.15)');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw decorative elements
    drawDecorativeFlow(ctx, 0.95);

    // Title
    ctx.fillStyle = colors.text;
    ctx.font = 'bold 64px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Archboard', canvas.width / 2, 220);

    // Subtitle
    ctx.fillStyle = colors.textSecondary;
    ctx.font = '32px sans-serif';
    ctx.fillText('Transform diagrams into code with AI', canvas.width / 2, 280);

    // Badge
    ctx.fillStyle = colors.primary;
    ctx.fillRect(canvas.width / 2 - 150, 360, 300, 60);
    ctx.fillStyle = colors.text;
    ctx.font = 'bold 28px sans-serif';
    ctx.fillText('Try it Free', canvas.width / 2, 400);

    // Save
    const buffer = canvas.toBuffer('image/png');
    fs.writeFileSync(path.join(__dirname, '..', config.twitterCard.output), buffer);
    console.log(`✅ Generated: ${config.twitterCard.output} (${config.twitterCard.width}x${config.twitterCard.height})`);

  } catch (error) {
    console.error('❌ Error generating Twitter Card:', error);
  }
}

function drawDecorativeFlow(ctx, scale = 1) {
  const centerX = ctx.canvas.width / 2;
  const centerY = ctx.canvas.height / 2;

  ctx.save();
  ctx.globalAlpha = 0.15;

  // Draw abstract nodes
  const nodes = [
    { x: centerX - 400 * scale, y: centerY - 100, w: 120, h: 60, color: colors.primary },
    { x: centerX - 200 * scale, y: centerY, w: 140, h: 70, color: colors.secondary },
    { x: centerX + 200 * scale, y: centerY - 50, w: 130, h: 65, color: colors.primary },
    { x: centerX + 400 * scale, y: centerY + 50, w: 110, h: 55, color: colors.secondary }
  ];

  // Draw connections
  ctx.strokeStyle = colors.primary;
  ctx.lineWidth = 3;
  ctx.beginPath();
  for (let i = 0; i < nodes.length - 1; i++) {
    ctx.moveTo(nodes[i].x + nodes[i].w / 2, nodes[i].y + nodes[i].h / 2);
    ctx.lineTo(nodes[i + 1].x + nodes[i + 1].w / 2, nodes[i + 1].y + nodes[i + 1].h / 2);
  }
  ctx.stroke();

  // Draw nodes
  nodes.forEach(node => {
    ctx.fillStyle = node.color;
    ctx.fillRect(node.x, node.y, node.w, node.h);

    // Highlight
    ctx.strokeStyle = colors.text;
    ctx.lineWidth = 2;
    ctx.strokeRect(node.x, node.y, node.w, node.h);
  });

  // Draw glow points
  ctx.globalAlpha = 0.8;
  const glowPoints = [
    { x: centerX - 300 * scale, y: centerY - 150, r: 8 },
    { x: centerX, y: centerY - 100, r: 12 },
    { x: centerX + 300 * scale, y: centerY, r: 10 }
  ];

  glowPoints.forEach(point => {
    const glow = ctx.createRadialGradient(point.x, point.y, 0, point.x, point.y, point.r * 3);
    glow.addColorStop(0, colors.secondary);
    glow.addColorStop(1, 'rgba(16, 185, 129, 0)');
    ctx.fillStyle = glow;
    ctx.fillRect(point.x - point.r * 3, point.y - point.r * 3, point.r * 6, point.r * 6);
  });

  ctx.restore();
}

async function main() {
  console.log('🚀 Starting social media image generation...\n');

  // Check if public directory exists
  const publicDir = path.join(__dirname, '..', 'public');
  if (!fs.existsSync(publicDir)) {
    fs.mkdirSync(publicDir, { recursive: true });
  }

  await generateOGImage();
  await generateTwitterCard();

  console.log('\n✨ Social media images generated successfully!');
  console.log('\n📋 Next steps:');
  console.log('   1. Review images in public/ directory');
  console.log('   2. Test sharing on Facebook/Twitter');
  console.log('   3. Use Facebook Sharing Debugger to verify');
  console.log('   4. Update absolute URLs in layout.tsx for production');
  console.log('\n📚 Validation tools:');
  console.log('   - Facebook: https://developers.facebook.com/tools/debug/');
  console.log('   - Twitter: https://cards-dev.twitter.com/validator');
}

// Run the generation
main().catch(error => {
  console.error('❌ Fatal error:', error);
  process.exit(1);
});
