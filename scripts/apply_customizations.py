import json
import os
import re


def replace_required(content, pattern, replacement, target):
    updated, count = re.subn(pattern, replacement, content)
    if count != 1:
        raise RuntimeError(
            f"Expected to customize {target} exactly once, found {count}."
        )
    return updated


def main():
    config_path = 'config.json'
    
    if not os.path.exists(config_path):
        print("config.json not found, skipping customization.")
        return

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    app_name = config.get("app_name", "MeuDesk")
    server_ip = config.get("server_ip", "")
    server_key = config.get("server_key", "")

    print(f"Applying customizations for App: {app_name}")

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

        # Replace OVERWRITE_SETTINGS to enforce credentials
        old_overwrite = r'pub static ref OVERWRITE_SETTINGS:\s*RwLock<HashMap<String,\s*String>>\s*=\s*Default::default\(\);'
        new_overwrite = f"""pub static ref OVERWRITE_SETTINGS: RwLock<HashMap<String, String>> = {{
        let mut map = std::collections::HashMap::new();
        map.insert("custom-rendezvous-server".to_string(), "{server_ip}".to_string());
        map.insert("key".to_string(), "{server_key}".to_string());
        std::sync::RwLock::new(map)
    }};"""
        content = replace_required(
            content, old_overwrite, new_overwrite, "OVERWRITE_SETTINGS"
        )

        # BUILTIN_SETTINGS controls whether Android and Windows render the form.
        # hide-powered-by-me also removes the upstream "Powered by" credit and
        # the external link that goes with it.
        old_builtin = r'pub static ref BUILTIN_SETTINGS:\s*RwLock<HashMap<String,\s*String>>\s*=\s*Default::default\(\);'
        new_builtin = """pub static ref BUILTIN_SETTINGS: RwLock<HashMap<String, String>> = {
        let mut map = std::collections::HashMap::new();
        map.insert("hide-server-settings".to_string(), "Y".to_string());
        map.insert("hide-powered-by-me".to_string(), "Y".to_string());
        std::sync::RwLock::new(map)
    };"""
        content = replace_required(
            content, old_builtin, new_builtin, "BUILTIN_SETTINGS"
        )

        # HARD_SETTINGS disables whole features. disable-account removes the
        # account/login UI on desktop and Android, plus the address book and
        # group panels that depend on being signed in.
        old_hard = r'pub static ref HARD_SETTINGS:\s*RwLock<HashMap<String,\s*String>>\s*=\s*Default::default\(\);'
        new_hard = """pub static ref HARD_SETTINGS: RwLock<HashMap<String, String>> = {
        let mut map = std::collections::HashMap::new();
        map.insert("disable-account".to_string(), "Y".to_string());
        std::sync::RwLock::new(map)
    };"""
        content = replace_required(
            content, old_hard, new_hard, "HARD_SETTINGS"
        )

        with open(config_rs_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Updated libs/hbb_common/src/config.rs")

    # 1.5 Modify AndroidManifest.xml
    android_manifest_path = 'flutter/android/app/src/main/AndroidManifest.xml'
    if os.path.exists(android_manifest_path):
        with open(android_manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # The accessibility service label is what Android shows under
        # Settings > Accessibility > Installed services.
        content = re.sub(
            r'android:label="RustDesk Input"',
            f'android:label="{app_name} Input"',
            content
        )
        content = re.sub(
            r'android:label="RustDesk"',
            f'android:label="{app_name}"',
            content
        )
        # Must match Rust's get_uri_prefix(), which lowercases APP_NAME.
        content = re.sub(
            r'android:scheme="rustdesk"',
            f'android:scheme="{app_name.lower()}"',
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
        # Shown by Android on the accessibility service consent screen.
        content = content.replace('RustDesk', app_name)

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
        # Must track BINARY_NAME below, otherwise Explorer's property sheet
        # still reports the upstream file name.
        content = re.sub(
            r'VALUE "OriginalFilename",\s*".*?"',
            f'VALUE "OriginalFilename", "{app_name.lower()}.exe"',
            content
        )

        with open(windows_runner_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Updated flutter/windows/runner/Runner.rc")

    # 3.5 macOS bundle. PRODUCT_NAME drives the .app name, the window title and
    # CFBundleName, so this is the macOS equivalent of Runner.rc.
    macos_appinfo_path = 'flutter/macos/Runner/Configs/AppInfo.xcconfig'
    if os.path.exists(macos_appinfo_path):
        with open(macos_appinfo_path, 'r', encoding='utf-8') as f:
            content = f.read()

        content = replace_required(
            content,
            r'PRODUCT_NAME = .*',
            f'PRODUCT_NAME = {app_name}',
            "macOS PRODUCT_NAME",
        )
        content = replace_required(
            content,
            r'PRODUCT_BUNDLE_IDENTIFIER = .*',
            'PRODUCT_BUNDLE_IDENTIFIER = com.meudesk.app',
            "macOS bundle identifier",
        )

        with open(macos_appinfo_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Updated flutter/macos/Runner/Configs/AppInfo.xcconfig")

    # 3.6 macOS deep-link scheme, same constraint as Android: it must match
    # Rust's get_uri_prefix(), which lowercases APP_NAME.
    macos_plist_path = 'flutter/macos/Runner/Info.plist'
    if os.path.exists(macos_plist_path):
        with open(macos_plist_path, 'r', encoding='utf-8') as f:
            content = f.read()

        content = replace_required(
            content,
            r'<string>rustdesk</string>',
            f'<string>{app_name.lower()}</string>',
            "macOS URL scheme",
        )
        content = content.replace(
            '<string>com.carriez.rustdesk</string>',
            '<string>com.meudesk.app</string>',
        )

        with open(macos_plist_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Updated flutter/macos/Runner/Info.plist")

    # 4. Windows executable name. The workflow ships the raw Release folder,
    # so the on-disk file name is visible to end users.
    windows_cmake_path = 'flutter/windows/CMakeLists.txt'
    if os.path.exists(windows_cmake_path):
        with open(windows_cmake_path, 'r', encoding='utf-8') as f:
            content = f.read()

        content = replace_required(
            content,
            r'set\(BINARY_NAME "rustdesk"\)',
            f'set(BINARY_NAME "{app_name.lower()}")',
            "BINARY_NAME",
        )

        with open(windows_cmake_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Updated flutter/windows/CMakeLists.txt")


if __name__ == "__main__":
    main()
