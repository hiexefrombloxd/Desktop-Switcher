const { execSync } = require('child_process');
const path = require('path');

console.log('🚀 Starting Node.js build process for Tab Switcher...\n');

try {
    // 1. Ensure PyInstaller is installed
    console.log('📦 Checking for PyInstaller...');
    execSync('python -m pip install pyinstaller', { stdio: 'inherit' });

    // 2. Define path to your python script
    const scriptPath = path.join(__dirname, 'desktop_toggler.py');

    // 3. Compile into a single, silent .exe file
    console.log('\n🔨 Compiling script into an executable...');
    execSync(`python -m PyInstaller --onefile --noconsole "${scriptPath}"`, { stdio: 'inherit' });

    console.log('\n✅ Build completed successfully!');
    console.log(`📁 Your standalone ".exe" file is located in the "dist" folder inside: ${__dirname}`);

} catch (error) {
    console.error('\n❌ Build failed:', error.message);
}