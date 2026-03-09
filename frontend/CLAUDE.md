# Frontend — JimiGPT

Next.js app for the JimiGPT user experience. Mobile-first design.

## Commands
- Install: npm install
- Dev: npm run dev
- Build: npm run build
- Test: npx vitest run
- Lint: npx next lint

## Stack
- Next.js 14+ with App Router
- TypeScript strict mode
- Tailwind CSS for styling
- Vitest + React Testing Library for tests

## Design Philosophy
- Mobile-first. Test on mobile viewport before desktop.
- "Describe, don't design" — use Tailwind utility classes, no custom CSS files.
- Warm, emotional aesthetic. Not corporate. Not clinical.
- Subtle animations. Pacing creates emotion more than flashiness.
- Accessible: proper ARIA labels, keyboard navigation, color contrast.

## API Integration
- Backend runs at http://localhost:8000 in development
- Use environment variable NEXT_PUBLIC_API_URL for backend URL
- All API calls use httpx or fetch with proper error handling
