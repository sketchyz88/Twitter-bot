# BallFlight AI (iPhone-first)

BallFlight AI is a premium React Native app concept focused only on golf ball tracking and tracer content creation.

## Implemented foundation
- Luxury dark-mode navigation shell
- Capture workflow stub with instant trace metrics
- SVG tracer overlay component
- Supabase client wiring
- Domain types for trace analytics and swing library

## Product architecture
1. **Capture + Import**
   - Expo camera module or native AVFoundation capture screen
   - Local import from media library
2. **AI Tracking Engine**
   - Native iOS module:
     - Frame extraction (AVAssetReader)
     - OpenCV detection/tracking
     - Optional CoreML model for impact + ball segmentation
   - Produces smooth polyline + shot metrics
3. **Editor**
   - Timeline scrubber, keyframe point adjustment, undo/redo
   - Tracer style controls (color, thickness, glow)
4. **Export + Social**
   - 9:16 vertical render pipeline
   - Watermark + reveal animations
5. **Cloud + Library (Supabase)**
   - Auth, clip metadata, favorites, club tagging

## Supabase bootstrap
Create `.env`:

```bash
EXPO_PUBLIC_SUPABASE_URL=your_url
EXPO_PUBLIC_SUPABASE_ANON_KEY=your_key
```

## Local run
```bash
npm install
npm run ios
```

## Next shipping milestones
- Replace mock tracking with real OpenCV bridge
- Implement real camera/import screens
- Build full editor and social export pipeline
- Add subscription/paywall and usage analytics
