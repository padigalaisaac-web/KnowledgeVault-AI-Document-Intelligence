# KnowledgeVault AI — Mobile Application Guide

KnowledgeVault AI is now fully converted into a **mobile-first application** supporting both **Progressive Web App (PWA) 1-tap installation** and **Native Android / iOS compilation via Capacitor**.

---

## 1. Instant Mobile Installation (PWA — Zero App Store Needed)

You can run KnowledgeVault AI as a full-screen, native-feeling mobile app on any smartphone right now from your Render URL: `https://knowledgevault-ai.onrender.com`.

### On iPhone / iPad (iOS):
1. Open your deployed URL in **Safari**.
2. Tap the **Share** button (the square with an arrow pointing up at the bottom of the screen).
3. Scroll down and tap **Add to Home Screen**.
4. Tap **Add**.
5. The **KnowledgeVault AI icon** will appear on your iPhone home screen!
6. Tapping it launches the app in **standalone fullscreen mode** (no browser address bar, no navigation buttons, native bottom tab bar, native status bar).

### On Android:
1. Open your deployed URL in **Google Chrome**.
2. Tap the three dots menu in the top right.
3. Tap **Install app** (or **Add to Home screen**).
4. Tap **Install**.
5. KnowledgeVault AI will be installed as an Android application with native app drawer integration and standalone windowing!

---

## 2. Mobile Touch & Responsive UX Features

- 📱 **Native Mobile Bottom Navigation Bar**: 3 touch-friendly tabs (`Research`, `Vault`, `Benchmarks`) with badge counters.
- 📂 **Mobile Drawer**: Slide-out navigation drawer on phones for switching threads and filtering knowledge sources with backdrop touch-to-dismiss.
- 📑 **Mobile Bottom Sheet Citations**: Clicking any citation chip `[1]` slides up a native-feeling bottom sheet displaying the exact source excerpt and page number.
- ⚡ **Offline Shell Caching**: Powered by `sw.js` (Service Worker) and `manifest.json`.
- 🛡️ **Safe Area Support**: Automatically handles dynamic islands, screen notches, and home indicator bars (`viewport-fit=cover`).

---

## 3. Compiling a Native Android APK (Using Capacitor)

If you want an installable `.apk` file for Android or want to publish to the Google Play Store:

### Prerequisites:
- Node.js 20+
- Android Studio installed on your computer

### Steps to Generate Android Project & APK:

1. **Install Capacitor Dependencies**:
   ```bash
   cd frontend
   npm install @capacitor/core @capacitor/cli @capacitor/android
   ```

2. **Build the Production Web Assets**:
   ```bash
   npm run build
   ```

3. **Initialize Android Platform**:
   ```bash
   npx cap add android
   npx cap sync
   ```

4. **Open in Android Studio**:
   ```bash
   npx cap open android
   ```

5. **Generate the APK**:
   - In Android Studio, go to the top menu: **Build ➔ Build Bundle(s) / APK(s) ➔ Build APK(s)**.
   - Android Studio will compile `app-debug.apk` located at:
     `frontend/android/app/build/outputs/apk/debug/app-debug.apk`.
   - Transfer this `.apk` to your Android phone to install directly!

---

## 4. Connecting Mobile to Your Deployed Backend

In `frontend/capacitor.config.json`, the app is configured to connect to your live backend:

```json
{
  "appId": "com.knowledgevault.ai",
  "appName": "KnowledgeVault AI",
  "webDir": "dist",
  "server": {
    "url": "https://knowledgevault-ai.onrender.com",
    "cleartext": true
  }
}
```
*(Replace `https://knowledgevault-ai.onrender.com` with your exact live Render URL).*
