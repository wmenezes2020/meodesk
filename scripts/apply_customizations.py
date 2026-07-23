import json
import os
import re

def main():
    config_path = 'config.json'
    
    if not os.path.exists(config_path):
        print("config.json not found, skipping customization.")
        return

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    app_name = config.get("app_name", "MeoDesk")
    server_ip = config.get("server_ip", "")
    server_key = config.get("server_key", "")

    print(f"Applying customizations for App: {app_name}, IP: {server_ip}")

    # 1. Modify libs/hbb_common/src/config.rs
    config_rs_path = 'libs/hbb_common/src/config.rs'
    if os.path.exists(config_rs_path):
        with open(config_rs_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Replace RENDEZVOUS_SERVERS
        content = re.sub(
            r'pub const RENDEZVOUS_SERVERS:\s*&\[&str\]\s*=\s*&\[".*?"\];',
            f'pub const RENDEZVOUS_SERVERS: &[&str] = &["{server_ip}"];',
            content
        )

        # Replace RS_PUB_KEY
        content = re.sub(
            r'pub const RS_PUB_KEY:\s*&str\s*=\s*".*?";',
            f'pub const RS_PUB_KEY: &str = "{server_key}";',
            content
        )

        # Replace APP_NAME
        content = re.sub(
            r'pub static ref APP_NAME:\s*RwLock<String>\s*=\s*RwLock::new\(".*?"\.to_owned\(\)\);',
            f'pub static ref APP_NAME: RwLock<String> = RwLock::new("{app_name}".to_owned());',
            content
        )

        # Replace OVERWRITE_SETTINGS to hide server settings and enforce credentials
        old_overwrite = r'pub static ref OVERWRITE_SETTINGS:\s*RwLock<HashMap<String,\s*String>>\s*=\s*Default::default\(\);'
        new_overwrite = f"""pub static ref OVERWRITE_SETTINGS: RwLock<HashMap<String, String>> = {{
        let mut map = std::collections::HashMap::new();
        map.insert("hide-server-settings".to_string(), "Y".to_string());
        map.insert("custom-rendezvous-server".to_string(), "{server_ip}".to_string());
        map.insert("key".to_string(), "{server_key}".to_string());
        std::sync::RwLock::new(map)
    }};"""
        content = re.sub(old_overwrite, new_overwrite, content)

        with open(config_rs_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Updated libs/hbb_common/src/config.rs")

    # 1.5 Modify AndroidManifest.xml
    android_manifest_path = 'flutter/android/app/src/main/AndroidManifest.xml'
    if os.path.exists(android_manifest_path):
        with open(android_manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = re.sub(
            r'android:label="RustDesk"',
            f'android:label="{app_name}"',
            content
        )

        with open(android_manifest_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Updated flutter/android/app/src/main/AndroidManifest.xml")

    # 2. Modify flutter/android/app/src/main/res/values/strings.xml
    android_strings_path = 'flutter/android/app/src/main/res/values/strings.xml'
    if os.path.exists(android_strings_path):
        with open(android_strings_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = re.sub(
            r'<string name="app_name">.*?</string>',
            f'<string name="app_name">{app_name}</string>',
            content
        )

        with open(android_strings_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Updated flutter/android/app/src/main/res/values/strings.xml")

    # 3. Windows Runner.rc
    windows_runner_path = 'flutter/windows/runner/Runner.rc'
    if os.path.exists(windows_runner_path):
        with open(windows_runner_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        content = re.sub(
            r'VALUE "FileDescription",\s*".*?"',
            f'VALUE "FileDescription", "{app_name}"',
            content
        )
        content = re.sub(
            r'VALUE "InternalName",\s*".*?"',
            f'VALUE "InternalName", "{app_name}"',
            content
        )
        content = re.sub(
            r'VALUE "ProductName",\s*".*?"',
            f'VALUE "ProductName", "{app_name}"',
            content
        )

        with open(windows_runner_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Updated flutter/windows/runner/Runner.rc")

if __name__ == "__main__":
    main()
