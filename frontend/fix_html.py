import os
import re

html_dir = r"d:\Assignment Works(Junior)\Shenuri\Job Workspace\frontend\pages"
files = [os.path.join(html_dir, f) for f in os.listdir(html_dir) if f.endswith('.html')]

script_code = """
    <!-- Google Translate Script -->
    <script type="text/javascript">
        function googleTranslateElementInit() {
            new google.translate.TranslateElement({
                pageLanguage: 'en',
                includedLanguages: 'en,si,ta',
                layout: google.translate.TranslateElement.InlineLayout.SIMPLE
            }, 'google_translate_element');
        }
    </script>
    <script type="text/javascript" src="//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit"></script>
</body>"""

widget_code = """
                <div class="language-selector">
                    <div id="google_translate_element"></div>
                </div>
"""

widget_code_dashboard = """
            <div id="google_translate_element" style="margin-right: 15px;"></div>
"""

for fp in files:
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()

    modified = False

    # 1. Remove i18n
    if '<script src="../js/i18n.js"></script>' in content:
        content = content.replace('<script src="../js/i18n.js"></script>', '')
        modified = True
    if '<script src="js/i18n.js"></script>' in content:
        content = content.replace('<script src="js/i18n.js"></script>', '')
        modified = True

    # Remove old dropdown if any exists
    old_dropdown = re.compile(r'<div class="language-selector">\s*<select id="languageSelect"[^>]*>.*?</select>\s*</div>', re.DOTALL)
    if old_dropdown.search(content):
        content = old_dropdown.sub('', content)
        modified = True

    # 2. Add scripts
    if 'googleTranslateElementInit' not in content:
        content = content.replace('</body>', script_code)
        modified = True

    # 3. Add Widget
    if 'id="google_translate_element"' not in content:
        if 'dashboard' in fp:
            # Add before notification-bell
            content = content.replace('<div class="notification-bell"', widget_code_dashboard + '            <div class="notification-bell"')
            modified = True
        else:
            # Add into nav-menu
            pattern = re.compile(r'(<div class="nav-menu"[^>]*>)(.*?)(</div>\s*</div>\s*</nav>)', re.DOTALL)
            match = pattern.search(content)
            if match:
                nav_content = match.group(2)
                # Ensure we don't duplicate
                if 'id="google_translate_element"' not in nav_content:
                    if '<div id="authLinks"' in nav_content:
                        nav_content = nav_content.replace('<div id="authLinks"', widget_code + '                <div id="authLinks"')
                    else:
                        nav_content = nav_content + widget_code
                    
                    content = content[:match.start(2)] + nav_content + content[match.end(2):]
                    modified = True

    if modified:
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Updated {os.path.basename(fp)}')
    else:
        print(f'Skipped {os.path.basename(fp)}')
