# BSG Attendance — Mobile app (Flutter)

Mobile client for **admins** and **leaders**. Talks to the same FastAPI backend as
the web dashboard.

## Roles & screens

| Tab | Leader | Admin | What it does |
|-----|:------:|:-----:|--------------|
| **Today** | ✓ | ✓ | Present / Absent / New Visitors for the day — **image-first** (faces, not names) |
| **Visitors** | ✓ | — | Resolve unmatched faces: map to a member (with face suggestions), register new, or keep |
| **Test** | ✓ | ✓ | Run recognition on a camera/gallery photo (dry-run or save) |
| **Reports** | ✓ | ✓ | Attendance %, visitor stats, long-term absentees |

Admins pick the group from the top-right dropdown; leaders are pinned to their own group.

Faces (member photos, visitor crops) are loaded with the auth token attached, so
everything is compared **by image**. Recognition no longer discards low-quality faces —
anything it can't confidently match shows up under **Visitors** to mark manually.

## Run

Prereqs: Flutter 3.3+, and the backend running (see repo root README).

```bash
cd mobile
flutter pub get
flutter run            # choose a device/emulator
```

### Pointing at the backend (Server URL on the login screen)
- **Android emulator:** `http://10.0.2.2:8000` (default — reaches the host machine)
- **Physical phone (same Wi-Fi):** `http://<your-computer-LAN-IP>:8000`
- **Chrome/web (`flutter run -d chrome`):** `http://localhost:8000` — note the backend's
  CORS currently allows only `http://localhost:4200`; add your web origin to `CORS_ORIGINS`
  in `backend/.env` if you use the web target. (Not needed for the Android app.)

Plain HTTP is enabled for development via `usesCleartextTraffic` in the Android manifest.

## Login
Same credentials as the dashboard (mobile number + password). The admin/leader role is
detected automatically and the tabs adjust.

## Build an APK
```bash
flutter build apk --release
# output: build/app/outputs/flutter-apk/app-release.apk
```
