# User Testing Strategy
## Working Backward from Experience Moments

**Version:** 1.0  
**Applies to:** JimiGPT (primary), adaptable to all Emotional AI products  

> This document defines how to validate JimiGPT from the user's perspective,
> not just from the feature perspective. The core question is not "does this
> feature work?" but "does this moment land emotionally?"
>
> Standard TDD catches code bugs. This strategy catches experience bugs —
> moments where the code works perfectly but the user feels nothing.

---

## 1. The Five Experience Moments

Everything in JimiGPT serves one of five moments. Testing must validate
each moment independently. Features are the means; moments are the ends.

| Moment | User Feels | What Must Work | When to Test |
|--------|-----------|---------------|-------------|
| M1: "I want to try this" | Curiosity, emotional pull | Landing page, first impression, founder story | Before launch |
| M2: "That's my pet!" | Recognition, emotional accuracy | Birthing ceremony, personality detection, archetype match | After F01 + F06 |
| M3: "This message made me smile" | Delight, surprise, warmth | Message generation, tone calibration, personality voice | After F02 (most critical) |
| M4: "I look forward to these" | Habitual anticipation, daily comfort | Message timing, variety, contextual relevance | After 2+ weeks of use |
| M5: "You have to try this" | Pride, excitement to share | Birth certificate, shareable moments, referral ease | After F07 |

---

## 2. Testing Levels

### Level 1: Technical Testing (TDD — Already in Place)
**What it catches:** Code bugs, type errors, logic failures  
**When:** Every micro-task, every commit  
**How:** pytest, mypy, ruff — automated, in CI/CD  
**Covers Moments:** None directly. Technical correctness is necessary but not sufficient.

### Level 2: Message Quality Testing (New — Build Into F02)
**What it catches:** Messages that are technically valid but emotionally flat,
tone-deaf, or out of character  
**When:** After completing F02, and ongoing  
**How:** Generate 50 messages per archetype across different contexts. Read them
yourself. Answer these questions for each:

```
Message Quality Rubric:
1. CHARACTER: Would I know which archetype sent this without being told? (Y/N)
2. INTENT: Does this message accomplish its intended emotional purpose? (Y/N)
3. CONTEXT: Does this message feel aware of time/situation? (Y/N)
4. TONE: Does the warmth/humor/energy feel right for this moment? (Y/N)
5. SMILE: Did this message make me smile, think, or feel something? (Y/N)
6. CRINGE: Is there anything that feels fake, generic, or robotic? (Y/N)

Score: Count of Y on 1-5, minus Y on 6. Target: 4+ out of 5, 0 cringe.
```

**Practical process:**
1. After F02 is complete, generate 50 messages (10 per message category)
   for chaos_gremlin archetype across: morning, midday, evening, rainy day,
   user-just-replied-negatively, user-been-silent-3-days
2. Print them or put in a spreadsheet
3. Score each with the rubric above
4. Messages scoring < 3: analyze why. Is it the prompt? The tone rules? The intent?
5. Adjust and regenerate. Repeat until 80%+ score 4+.

**This is your most important pre-launch gate. If messages don't score well
here, real users won't retain.**

### Level 3: Self-Dogfooding (You Are User #1)
**What it catches:** Experience gaps that only show up with real daily use  
**When:** After F03 (delivery working) — send messages to YOUR phone  
**How:** Set up your own Digital Twin. Receive messages for 2 weeks minimum.
Live with it. Notice:

- Which messages made you feel something?
- Which messages felt interruptive or annoying?
- Did the timing feel right?
- Did the personality stay consistent across days?
- Did you start ignoring messages? When? Why?
- Was there a moment you wanted to reply? What triggered it?

**Journal template (fill out daily for 2 weeks):**
```
Day: ___
Messages received today: ___
Message that landed best: "___"
  Why it worked: ___
Message that fell flat: "___"  
  Why it failed: ___
Overall feeling today: ___
Would I have paid for this today? Y/N
```

**This is not optional. You must dogfood for 2 weeks before any external user
touches the product. Your CPTSD-informed sensitivity to emotional authenticity
is actually an asset here — if it feels fake to you, it will feel fake to
everyone.**

### Level 4: Closed Alpha Testing (5-10 Real Users)
**What it catches:** Assumptions that only your perspective reveals  
**When:** After Phase 1D (all features working, 2 weeks of self-dogfooding complete)  
**Who:** 5-10 real pet owners, recruited from:
- Personal network (friends, family with pets)
- Reddit r/pets, r/dogs, r/cats (ask for beta testers, not customers)
- Pet-focused Discord servers

**How to run:**
1. Each tester gets a personal onboarding call (15 min video or voice).
   Walk them through the birthing ceremony. Watch their face during the
   personality reveal — that reaction tells you everything about M2.
2. They use JimiGPT for 2 weeks minimum.
3. After 1 week, send a simple survey:

```
Alpha Tester Week 1 Survey:
1. Does your Digital Twin sound like your actual pet? (1-5 scale)
2. Favorite message so far? (paste it)
3. Worst message so far? (paste it)
4. How many messages per day feels right? (1/2/3/4/5/too many)
5. When do you look forward to messages most? (morning/afternoon/evening)
6. Would you pay $5.99/month for this? (Yes/No/Maybe)
7. What's missing? (open text)
```

4. After 2 weeks, a closing interview (15 min):
   - "Tell me about your favorite moment with your Digital Twin"
   - "Was there a moment it felt wrong or off?"
   - "Did you tell anyone about it?" (M5 test)
   - "If it disappeared tomorrow, would you miss it?" (retention signal)

**Key metrics from alpha:**
- Personality accuracy score (Survey Q1, target: 4.0+ average)
- Day 14 retention (still reading messages? target: 70%+)
- Willingness to pay (Survey Q6, target: 40%+ yes or maybe)
- Net Promoter: "Would you tell a friend?" (target: 60%+ yes)

### Level 5: Message A/B Cadence Testing (After Alpha)
**What it catches:** Optimization opportunities in message composition  
**When:** After alpha feedback incorporated, before public launch  
**How:** With a slightly larger group (20-30 users), test variations:

- **Intent variation:** Same time slot, different intents. Does ENERGIZE or
  ACCOMPANY get better reactions at 8am?
- **Tone variation:** Same intent, different tone calibrations. Does high-humor
  or medium-humor land better for caring check-ins?
- **Frequency variation:** 3 messages/day vs 5 messages/day. Which retains better?
- **Timing variation:** Fixed schedule vs. random intervals. Which feels more natural?

Track via effectiveness scores (message-modeling.md Section 8).
This is where the message modeling architecture pays off — you can isolate
which dimension drives engagement.

---

## 3. User-Backward Design Process

When building any new feature or message type, start with this template:

```
USER-BACKWARD DESIGN TEMPLATE

1. THE MOMENT: What experience moment does this serve? (M1-M5)

2. THE FEELING: What should the user feel?
   (Examples: "smiled and thought of their dog", "felt seen on a rough day",
   "laughed and screenshot it for a friend")

3. THE MESSAGE: Write 3 example messages that would create this feeling.
   Not generated by AI — written by you, as if you were the pet.

4. THE COMPOSITION: What intent, tone, and context signals produce
   messages like those examples?
   - Intent: ___
   - Tone: warmth ___, humor ___, energy ___, gravity ___
   - Context that matters: ___
   - Context that doesn't matter: ___

5. THE TEST: How will you know this works?
   - Technical: What does the unit test verify?
   - Quality: What does the message rubric score?
   - User: What question do you ask the alpha tester?

6. THE FAILURE MODE: What does this look like when it goes wrong?
   - Too generic: ___
   - Too intense: ___
   - Wrong timing: ___
   - Wrong tone: ___
```

### Example: Designing a "Rainy Day Caring Message"

```
1. THE MOMENT: M3 ("This message made me smile")

2. THE FEELING: "My pet noticed it's a dreary day and is being extra cozy"

3. THE MESSAGES:
   - Chaos Gremlin: "It's raining which means COUCH TIME. Get home. I've 
     already claimed the good blanket."
   - Loyal Shadow: "Rainy days are the best days. You, me, the couch. 
     Take your time getting home. I'll keep it warm."
   - Regal One: "It's raining. I've positioned myself on the windowsill 
     to watch. Quite dramatic. You'd approve."

4. THE COMPOSITION:
   - Intent: ACCOMPANY (be present, cozy, no agenda)
   - Tone: warmth 0.85, humor per-archetype, energy 0.3, gravity 0.1
   - Context that matters: weather:rainy, time_of_day
   - Context that doesn't matter: calendar, location

5. THE TEST:
   - Technical: message generates, quality gate passes, under 160 chars
   - Quality: score 4+ on rubric, 0 cringe
   - User: "Did any messages feel like they noticed the weather?"

6. THE FAILURE MODE:
   - Too generic: "Hope you're having a nice day!" (no weather awareness)
   - Too intense: "I'm SO WORRIED about you in this STORM"
   - Wrong timing: Rainy message arrives on a sunny day (signal was stale)
   - Wrong tone: Serious/heavy when it should be cozy
```

---

## 4. When to Test What (Timeline)

| Phase | Level | What You Learn |
|-------|-------|---------------|
| F01 complete | L2: Generate + score 50 personality-only messages | "Can this voice be consistent?" |
| F02 complete | L2: Generate + score 50 fully-composed messages | "Do intent and tone make messages better?" |
| F03 complete | L3: Self-dogfood for 2 weeks | "Does this work as a daily product?" |
| Phase 1D complete | L4: Alpha test 5-10 users for 2 weeks | "Do real people value this?" |
| Pre-launch | L5: A/B test message variations with 20-30 users | "What message composition works best?" |
| Post-launch | Ongoing effectiveness tracking | "What's improving? What's degrading?" |

---

## 5. Feedback Integration Cadence

- **Daily (during self-dogfooding):** Journal one observation. Fix obvious issues immediately.
- **Weekly (during alpha):** Review alpha survey responses. Identify pattern: if 3+ testers flag the same issue, it's a priority fix.
- **Per-sprint:** Before starting a new sprint, review accumulated feedback. Adjust feature priorities based on what users actually need, not what was planned.
- **Monthly:** Step back. Review the effectiveness data. Are messages getting better over time? Are certain archetypes performing poorly? Does the message model need new tone rules?

---

## 6. The Honest Reality About Getting Messaging Right

You said "we are not going to get the messaging right the first time."
You are correct. Here's what will likely happen:

**First generated messages** (after F02): Technically correct, emotionally flat.
The personality will be recognizable but the messages will feel like a
personality doing an impression rather than being natural. This is normal.

**After self-dogfooding** (2 weeks): You'll identify 3-5 specific failure
patterns. Common ones: too many emojis, personality breaks during certain
intents, night messages too energetic, repetitive structure even when words
differ. You'll fix these by adjusting tone rules and prompt templates.

**After alpha testing** (2 more weeks): Users will surface things you can't
see yourself. "The messages are nice but they all feel the same length."
"My cat would never say that." "I love the morning messages but the
evening ones feel forced." These are gold — they tell you exactly which
dimensions of the message model need tuning.

**After 2-3 months of real use:** The effectiveness data will show clear
patterns. Certain intent + archetype + context combinations will score
high consistently. Others will score low. You'll be able to scientifically
optimize message composition based on data, not guesswork.

The message model is designed for this iterative improvement. Every
dimension (intent, tone, signals, recipient state) is independently
adjustable. When something doesn't work, you can isolate which dimension
is the problem without rebuilding the whole system.

**Build it, ship it, measure it, improve it. In that order.**
