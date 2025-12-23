---
title: "Preserve macOS App Permissions Across Rebuilds with Self-Signed Certificates"
date: 2025-12-21
tags: [macos, code-signing, development, security]
summary: "Stop re-granting Accessibility permissions after every rebuild by creating a stable self-signed certificate."
---

macOS ties permissions (Accessibility, Input Monitoring, etc.) to an app's code signature. When you sign with `codesign --sign -` (ad-hoc signing), macOS generates a different signature each rebuild. Your carefully granted permissions vanish. You re-add the app to System Settings. Again. And again.

The fix: a self-signed certificate that stays consistent across builds.

## Create the Certificate

Generate a code signing certificate with proper extensions:

```bash
# Generate key and certificate
openssl req -x509 -newkey rsa:2048 -days 3650 \
  -keyout dev.key -out dev.crt -nodes \
  -subj "/CN=MyApp Dev" \
  -addext "keyUsage=critical,digitalSignature" \
  -addext "extendedKeyUsage=codeSigning"

# Convert to p12 (macOS import format)
# -legacy flag required for macOS Keychain compatibility
openssl pkcs12 -export -legacy \
  -in dev.crt -inkey dev.key \
  -out dev.p12 -password pass:dev

# Import to login keychain
security import dev.p12 -k ~/Library/Keychains/login.keychain-db \
  -P dev -T /usr/bin/codesign

# Cleanup
rm dev.key dev.crt dev.p12
```

## Trust the Certificate

The certificate exists but macOS does not trust it for code signing yet.

1. Open **Keychain Access**
2. Find your certificate (search "MyApp Dev")
3. Double-click it
4. Expand **Trust**
5. Set **Code Signing** to **Always Trust**
6. Close and authenticate

## Update Your Build Script

Replace ad-hoc signing:

```bash
# Before: different signature every build
codesign --force --sign - MyApp.app

# After: stable signature
codesign --force --sign "MyApp Dev" MyApp.app
```

The certificate name in `--sign` must match the Common Name (CN) from the certificate.

## Verify

```bash
codesign -dv --verbose=4 MyApp.app 2>&1 | grep Authority
# Should show: Authority=MyApp Dev
```

Rebuild your app. Permissions persist.

## Trade-offs

This approach works for local development only. The certificate is self-signed and untrusted by other machines. For distribution, you still need an Apple Developer certificate.

The `-legacy` flag in the p12 conversion is required because macOS Keychain uses an older PKCS#12 format. Without it, the import silently fails to make the certificate usable for signing.

## Takeaways

- Ad-hoc signing (`--sign -`) generates unique signatures per build
- Self-signed certificates provide stable signatures across rebuilds
- Trust must be explicitly set in Keychain Access for code signing
- Use `-legacy` flag when creating p12 files for macOS import

---

**Related:** [iTerm2 + tmux -CC: The Remote Development Setup](/posts/iterm2-tmux-control-mode/) - Streamline your remote macOS development workflow.
