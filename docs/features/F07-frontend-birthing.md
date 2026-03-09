# F07: Frontend — Birthing Ceremony & Onboarding

**Phase:** 1C  
**Priority:** 7  
**Architecture Reference:** JimiGPT Architecture Section 4  
**Approach:** "Describe, don't design" — describe what you want to Claude Code  

## Feature Description

Build the user-facing birthing ceremony: multi-step onboarding flow in Next.js
with pet name entry, photo upload, story prompt, personality confirmation,
creation animation, reveal with first message, and birth certificate display.

## Dependencies
- F06 (Birthing Ceremony API) — backend endpoints must exist

## What "Done" Looks Like
- User can complete full birthing flow on mobile and desktop
- Photos upload and analyze correctly
- Personality confirmation feels accurate and emotionally resonant
- Creation animation creates a moment of anticipation
- First message from Digital Twin appears on reveal
- Birth certificate is shareable
- Flow works on mobile (primary device for target users)

---

## Micro-Tasks

### Task 1: Next.js Project Setup
**Time:** 20 min  
**Context:** CLAUDE.md tech stack (Next.js + TypeScript + Tailwind)  
**What to do:**
- Initialize Next.js project in frontend/ directory
- Configure TypeScript, Tailwind, and App Router
- Create frontend/CLAUDE.md with frontend-specific instructions
- Create a simple landing page with "Create Your Pet's Digital Twin" CTA
- Verify dev server runs and page renders  
**Done when:** Next.js dev server runs, landing page shows  
**Commit:** `chore(frontend): initialize Next.js project with Tailwind`

### Task 2: Step 1 — Pet Name Entry
**Time:** 20 min  
**Context:** JimiGPT Architecture Section 4 (Flow Steps)  
**What to do:**
- Create app/birth/page.tsx with multi-step form state management
- Step 1: Large centered text input for pet name
- Warm background gradient (cream → soft gold)
- "Next" button enabled only when name is entered
- Mobile-first responsive layout
- Write test: form validation, step progression  
**Done when:** Name entry step renders and validates  
**Commit:** `feat(frontend): add birthing step 1 — pet name entry`

### Task 3: Step 2 — Photo Upload
**Time:** 25 min  
**Context:** JimiGPT Architecture Section 4 (Flow Steps)  
**What to do:**
- Step 2: Photo upload area (drag-and-drop + tap-to-upload)
- Accept 1-3 photos, show thumbnails
- Upload photos to backend analyze-photos endpoint
- Show loading state during analysis
- Store analysis results in form state
- Write test: upload interaction, API call mocking  
**Done when:** Photos upload and analysis results stored  
**Commit:** `feat(frontend): add birthing step 2 — photo upload`

### Task 4: Step 3 — Story Prompt
**Time:** 20 min  
**Context:** JimiGPT Architecture Section 4 (Flow Steps)  
**What to do:**
- Step 3: Story prompt textarea
- Prompt text: "Tell me about a time {pet_name} surprised you"
- Warm, encouraging microcopy below
- Gentle character count guidance (not a hard limit)
- "Next" button after some text entered  
**Done when:** Story prompt captures text, progresses to next step  
**Commit:** `feat(frontend): add birthing step 3 — story prompt`

### Task 5: Step 4 — Personality Confirmation
**Time:** 25 min  
**Context:** JimiGPT Architecture Section 4 (Archetype Selection Flow)  
**What to do:**
- Step 4: Display suggested personality
- Shows archetype name + one-line description
- Optional secondary archetype shown
- "That's my pet!" confirmation button (primary, large)
- "Not quite right" button → shows all 8 archetypes to pick from
- Calls backend for archetype suggestion based on photos + story
- Write test: confirmation flow, archetype switching  
**Done when:** User can confirm or change personality  
**Commit:** `feat(frontend): add birthing step 4 — personality confirmation`

### Task 6: Step 5 — Creation Animation
**Time:** 25 min  
**Context:** JimiGPT Architecture Section 4 (Flow Steps)  
**What to do:**
- Step 5: 3-5 second creation animation
- Pulsing paw print or heartbeat animation (CSS/Tailwind)
- Background transitions to warmer tones
- Text progression: "Creating..." → "Almost there..." → "Meet {pet_name}!"
- Calls backend birth endpoint during animation
- This is an EMOTIONAL moment — pacing matters more than flashiness  
**Done when:** Animation plays while backend creates entity  
**Commit:** `feat(frontend): add birthing step 5 — creation animation`

### Task 7: Step 6 — Reveal & Certificate
**Time:** 25 min  
**Context:** JimiGPT Architecture Section 4 (Flow Steps)  
**What to do:**
- Step 6: The reveal
- First message from Digital Twin displayed in a chat bubble
- Birth certificate displayed below (fetched from backend)
- Share button for certificate (Web Share API or copy-link fallback)
- CTA: "Set up your message schedule" → leads to schedule page
- Celebration micro-animation (confetti? sparkles? keep it tasteful)  
**Done when:** Full reveal shows first message + certificate  
**Commit:** `feat(frontend): add birthing step 6 — reveal and certificate`

### Task 8: Message Schedule Setup
**Time:** 20 min  
**Context:** JimiGPT Architecture Section 5 (Default Trigger Schedule)  
**What to do:**
- Create app/settings/schedule/page.tsx
- Show default schedule (morning, midday, afternoon, evening, goodnight)
- Toggle each message type on/off
- Set wake time and quiet hours
- Save to backend trigger configuration
- Write test: schedule save and load  
**Done when:** User can configure their message schedule  
**Commit:** `feat(frontend): add message schedule setup page`

### Task 9: End-to-End Birthing Flow Test
**Time:** 25 min  
**Context:** All previous frontend tasks  
**What to do:**
- Manual testing: complete full birthing flow on mobile viewport
- Fix any responsive issues, transition glitches, or broken states
- Verify API integration end-to-end with running backend
- Test error states: what if photo upload fails? API timeout?  
**Done when:** Complete flow works smoothly on mobile and desktop  
**Commit:** `fix(frontend): polish birthing flow end-to-end`

---

## Task Summary

| # | Task | Time | Depends On |
|---|------|------|------------|
| 1 | Next.js setup | 20 min | F06 complete |
| 2 | Name entry step | 20 min | Task 1 |
| 3 | Photo upload step | 25 min | Task 2 |
| 4 | Story prompt step | 20 min | Task 2 |
| 5 | Personality confirmation | 25 min | Task 3, Task 4 |
| 6 | Creation animation | 25 min | Task 5 |
| 7 | Reveal & certificate | 25 min | Task 6 |
| 8 | Message schedule setup | 20 min | Task 7 |
| 9 | E2E testing & polish | 25 min | All above |

**Total estimated time:** ~3.5 hours (9 reps across 3 daily sessions)
