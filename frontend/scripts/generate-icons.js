/**
 * Icon Generation Script
 *
 * Generates all required icon sizes from a source SVG
 *
 * Requirements:
 *   npm install sharp
 *
 * Usage:
 *   node scripts/generate-icons.js
 */

const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

// Create icons directory if it doesn't exist
const iconsDir = path.join(__dirname, '..', 'public', 'icons');
if (!fs.existsSync(iconsDir)) {
  fs.mkdirSync(iconsDir, { recursive: true });
}

// Source SVG file
const sourceSvg = path.join(__dirname, '..', 'app', 'icon.svg');

// Icon sizes to generate
const sizes = [
  { name: 'icon-192.png', size: 192 },
  { name: 'icon-512.png', size: 512 },
  { name: 'icon-maskable.png', size: 512, padding: 80 }, // Maskable needs padding
  { name: 'apple-icon.png', size: 180, output: path.join(__dirname, '..', 'app') },
  { name: 'favicon-32.png', size: 32 },
  { name: 'favicon-16.png', size: 16 }
];

async function generateIcons() {
  console.log('🎨 Starting icon generation...\n');

  try {
    // Check if source SVG exists
    if (!fs.existsSync(sourceSvg)) {
      console.error('❌ Source SVG not found:', sourceSvg);
      console.log('📝 Please create app/icon.svg first');
      process.exit(1);
    }

    // Generate each size
    for (const config of sizes) {
      const outputPath = config.output
        ? path.join(config.output, config.name)
        : path.join(iconsDir, config.name);

      let pipeline = sharp(sourceSvg);

      // Add padding for maskable icons
      if (config.padding) {
        pipeline = pipeline.extend({
          top: config.padding,
          bottom: config.padding,
          left: config.padding,
          right: config.padding,
          background: { r: 79, g: 70, b: 229, alpha: 1 } // #4F46E5
        });
      }

      // Resize and save
      await pipeline
        .resize(config.size, config.size)
        .png()
        .toFile(outputPath);

      console.log(`✅ Generated: ${config.name} (${config.size}x${config.size})`);
    }

    // Generate favicon.ico (multi-resolution)
    console.log('\n🔄 Generating favicon.ico...');
    const faviconSizes = [16, 32, 48];
    const faviconPngs = [];

    for (const size of faviconSizes) {
      const buffer = await sharp(sourceSvg)
        .resize(size, size)
        .png()
        .toBuffer();
      faviconPngs.push(buffer);
    }

    // Note: Converting PNG to ICO requires additional library
    console.log('⚠️  Note: favicon.ico generation requires manual conversion');
    console.log('    Visit: https://www.icoconverter.com/ to convert favicon-32.png');
    console.log('    Or use: npm install -g png-to-ico');
    console.log('           png-to-ico public/icons/favicon-32.png > app/favicon.ico');

    console.log('\n✨ Icon generation complete!');
    console.log('\n📋 Next steps:');
    console.log('   1. Convert favicon-32.png to favicon.ico');
    console.log('   2. Update app/layout.tsx with metadata');
    console.log('   3. Test icons in browser and mobile devices');

  } catch (error) {
    console.error('❌ Error generating icons:', error);
    process.exit(1);
  }
}

// Run the generation
generateIcons();
