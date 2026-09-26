import re

with open('src/app.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Add a script to capture beforeinstallprompt ASAP
head_script = """		<script>
			// Tangkap event install seawal mungkin sebelum SvelteKit jalan!
			window.deferredPWAInstallPrompt = null;
			window.addEventListener('beforeinstallprompt', (e) => {
				e.preventDefault();
				window.deferredPWAInstallPrompt = e;
			});

			if ('serviceWorker' in navigator) {"""

content = content.replace("		<script>\n			if ('serviceWorker' in navigator) {", head_script)

with open('src/app.html', 'w', encoding='utf-8') as f:
    f.write(content)
