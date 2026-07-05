---
name: mobile-design
description: Mobile-first design rules for iOS/Android. Touch, performance, platform conventions. React Native, Flutter, native.
priority: P2
---

## When to Activate

- Building mobile apps (React Native, Flutter, SwiftUI, Kotlin)
- Mobile-specific UI/UX decisions

# Mobile Design Rules

> AI model đã biết React Native, Flutter, mobile UI.
> File này = RULES + ROUTING to sub-files. Không tutorials.

---

## MUST ASK If Not Specified

| Aspect | Question |
|---|---|
| Platform | "iOS, Android, or both?" |
| Framework | "React Native, Flutter, or native?" |
| Offline | "Does this need offline support?" |
| Target devices | "Phone only, or tablet support?" |

## Framework Selection

| Need | Use |
|---|---|
| OTA updates + rapid iteration + web team | React Native + Expo |
| Pixel-perfect custom UI + performance critical | Flutter |
| Deep native features, single platform | SwiftUI (iOS) / Kotlin Compose (Android) |

## Sub-files (đọc theo nhu cầu)

| File | When |
|---|---|
| [mobile-design-thinking.md](mobile-design-thinking.md) | **FIRST** — anti-memorization, forces thinking |
| [touch-psychology.md](touch-psychology.md) | Touch targets, Fitts' Law, thumb zone |
| [mobile-performance.md](mobile-performance.md) | 60fps, memory, battery optimization |
| [mobile-backend.md](mobile-backend.md) | Push notifications, offline sync |
| [mobile-testing.md](mobile-testing.md) | Testing pyramid, E2E |
| [platform-ios.md](platform-ios.md) | iOS HIG, SF Pro, SwiftUI |
| [platform-android.md](platform-android.md) | Material Design 3, Roboto, Compose |
| [decision-trees.md](decision-trees.md) | Framework/state/storage selection |

## Hard Rules (Luôn Áp Dụng)

### Touch & UX
- ✅ Touch targets ≥ 44pt (iOS) / 48dp (Android). Spacing ≥ 8px
- ✅ Primary CTA in thumb zone (bottom of screen)
- ✅ Loading state, Error state with retry, Offline handling — ALWAYS
- ❌ CẤM gesture-only interactions (provide button alternative)
- ❌ CẤM ignore platform conventions (iOS feels iOS, Android feels Android)

### Performance
- ✅ `FlatList`/`FlashList`/`ListView.builder` for lists. CẤM ScrollView for >20 items
- ✅ `React.memo` + `useCallback` for renderItem. `const` constructors (Flutter)
- ✅ `useNativeDriver: true` for animations. Animate only transform/opacity
- ❌ CẤM `console.log` in production. CẤM inline renderItem
- ❌ CẤM CPU work on main/UI thread

### Security
- ✅ Tokens → `SecureStore`/`Keychain`/`EncryptedSharedPreferences`. CẤM AsyncStorage
- ✅ SSL pinning in production. CẤM hardcode API keys

### Architecture
- ✅ Business logic in service layer, NOT in UI components
- ✅ Deep linking planned from day one
- ✅ Clean up subscriptions/timers on unmount

### Platform Divergence

| Unify | Diverge |
|---|---|
| Business logic, Data layer, Core features | Navigation, Gestures, Icons, Date pickers, Modals, Typography |

| Element | iOS | Android |
|---|---|---|
| Min touch target | 44pt | 48dp |
| Back nav | Edge swipe | System back |
| Icons | SF Symbols | Material Symbols |

## Scripts

| Script | Usage |
|---|---|
| `scripts/mobile_audit.py` | `python scripts/mobile_audit.py <path>` |
