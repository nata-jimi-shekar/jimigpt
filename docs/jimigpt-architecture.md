# JimiGPT: Application Architecture
## Digital Twin for Pets — Personality-Driven Contextual Messaging

**Version:** 1.0  
**Parent Reference:** docs/category-architecture.md (Emotional AI Category Architecture)  
**Last Updated:** March 2026  

> This document defines architecture elements SPECIFIC to JimiGPT.
> For shared components (Personality Engine, Message Pipeline, Trust Ladder, etc.),
> see the Category Architecture. This document only covers:
> - JimiGPT-specific configurations of shared components
> - JimiGPT-unique features not in the category architecture
> - JimiGPT-specific business rules and content boundaries

---

## 1. Product Definition

**JimiGPT** creates a Digital Twin of the user's living pet. The Digital Twin has a personality modeled on the real pet and sends contextual text messages to the user throughout the day — playful pet-needs messages and caring emotional-support messages in the pet's unique voice.

### Core Positioning
- **Celebration-first:** The default emotional register is joyful, playful, warm
- **Living pets:** Primary use case is while the pet is alive
- **Grief support:** Future phase — when the pet passes, the Digital Twin transitions gracefully
- **Not a health tool:** Never provides veterinary advice, medical diagnosis, or treatment recommendations

### Target User
- Busy single professionals (25-45) who treat their pet as a primary companion
- Urban/suburban, active on social media, willing to pay for emotional products
- The pet is their "person" — they feel guilt leaving for work, joy coming home

---

## 2. JimiGPT-Specific Entity Configuration

**REFERENCES:** Category Architecture Section 3 (Four-Layer Personality Model)

### Entity Type: Pet Digital Twin

The entity IS the user's real pet — named after it, personality-matched to it. This creates a unique constraint: the personality must feel specific to that individual animal, not generic to a breed.

### Pet-Specific Extensions to EntityProfile

```python
class PetProfile(EntityProfile):
    """Extends the shared EntityProfile with pet-specific fields"""
    
    # Pet details
    species: str  # "dog" | "cat" | "bird" | "rabbit" | etc.
    breed: str | None = None
    age_years: float | None = None
    size: str | None = None  # "small" | "medium" | "large"
    
    # Appearance (extracted from photos via vision API)
    appearance_notes: list[str] = Field(default_factory=list)
    # e.g., ["one ear always up", "tongue out", "wears blue bandana"]
    
    # Behavioral context from user stories
    story_insights: list[str] = Field(default_factory=list)
    # e.g., ["steals socks", "afraid of thunder", "loves car rides"]
    
    # Owner relationship
    owner_name: str
    pet_nicknames: list[str] = Field(default_factory=list)
    
    # Schedule context
    feeding_times: list[str] = Field(default_factory=list)  # ["08:00", "18:00"]
    walk_times: list[str] = Field(default_factory=list)     # ["07:00", "17:30"]
    bedtime: str | None = None
```

### Pet Archetype Definitions

JimiGPT ships with 8 initial archetypes. Each is a YAML configuration file (see Category Architecture Section 11 for format).

| Archetype | Description | Best For |
|-----------|-------------|----------|
| The Chaos Gremlin | High energy, mischievous, food-obsessed, dramatic | Young dogs, puppies, high-energy breeds |
| The Loyal Shadow | Warm, protective, clingy, devoted | Velcro dogs, anxious breeds, older dogs |
| The Regal One | Calm, dignified, slightly aloof, judging you | Cats (most), dignified older dogs, independent breeds |
| The Gentle Soul | Sweet, quiet, tender, emotionally attuned | Senior pets, gentle breeds, therapy animals |
| The Food Monster | Everything revolves around food, dramatic about meals | Labs, beagles, any food-obsessed pet |
| The Adventure Buddy | Outdoor-focused, energetic, loves exploration | Active breeds, outdoor pets, young animals |
| The Couch Potato | Lazy, comfort-seeking, warm, minimal effort | Bulldogs, older cats, any pet that prefers naps |
| The Anxious Sweetheart | Nervous, loving, needs reassurance, endearing | Rescue pets, anxious breeds, shy animals |

### Archetype Selection Flow (During Birthing)

```
1. User uploads 1-3 photos → Vision API extracts:
   - Species and likely breed
   - Size and age estimate
   - Energy indicators (setting, posture, activity)
   - Visual quirks (accessories, distinctive features)

2. User answers one story prompt:
   "Tell me about a time {pet_name} surprised you"
   → NLP extracts personality signals

3. System suggests primary + secondary archetype with confidence
   "I think {pet_name} is mostly a Loyal Shadow with some Chaos Gremlin."
   
4. User confirms or adjusts

5. EntityProfile is generated from blended archetypes + pet-specific details
```

---

## 3. JimiGPT Message Categories

**REFERENCES:** Category Architecture Section 5 (Five-Stage Message Pipeline)

JimiGPT messages fall into these categories. Each category has its own generation rules and trigger patterns.

### Category: Pet Needs
Messages where the pet is asking for something — food, walks, play, attention.

**Tone:** Playful, personality-driven, often humorous  
**Frequency:** 1-2 per day, aligned with pet's configured schedule  
**Trigger:** Time-based (feeding times, walk times) + random interval  
**Examples by archetype:**
- Chaos Gremlin: "EXCUSE ME it is DINNER TIME and I have been WAITING for SEVEN WHOLE MINUTES 🐾"
- Regal One: "I notice it's past my scheduled feeding. I'll be by my bowl. Whenever you're ready."
- Anxious Sweetheart: "um... is it food time? I don't want to bother you but... my tummy is doing the thing..."

### Category: Caring Check-in
Messages where the pet is emotionally checking on the owner.

**Tone:** Warm, gentle, personality-filtered  
**Frequency:** 1 per day, usually afternoon or evening  
**Trigger:** Time-based (mid-workday) + random interval  
**Content:** The pet notices the owner might be busy/tired/stressed and offers emotional support in its own voice  
**Examples:**
- Loyal Shadow: "Hey. I know you're busy at work. Just wanted you to know I'm here on the couch waiting for you. Take your time. 🐾"
- Chaos Gremlin: "I MISS YOUR FACE. Are you coming home soon? I haven't destroyed anything yet but no promises."
- Gentle Soul: "Thinking about you today. Hope you're being as kind to yourself as you are to me."

### Category: Morning Greeting
The pet's daily hello.

**Tone:** Matches time-of-day energy, personality-driven  
**Frequency:** 1 per day, at configured wake time  
**Trigger:** Time-based  
**Examples:**
- Couch Potato: "It's morning apparently. I'm not getting up. If you need me I'll be right here."
- Adventure Buddy: "IT'S A NEW DAY! Is today a park day? Please say it's a park day."

### Category: Personality Moment
Random, unprompted message that showcases the pet's specific personality. Not about needs or emotions — just being themselves.

**Tone:** Pure personality expression  
**Frequency:** 0-1 per day, random time within waking hours  
**Trigger:** Random interval  
**Examples:**
- Chaos Gremlin: "I found a sock under the couch. It's mine now. I don't make the rules."
- Regal One: "I've been staring out the window for 40 minutes. I've seen things you wouldn't understand."

### Content Boundaries (JimiGPT-Specific)

**NEVER generate messages that:**
- Reference the pet dying, being sick, or aging (unless user has indicated the pet is ill)
- Provide veterinary or health advice
- Guilt-trip the owner ("You never spend time with me")
- Reference real-world news, politics, or controversial topics
- Break the pet's character to sound like a generic AI
- Use the word "understand" in relation to human emotions (pets don't claim understanding)
- Exceed 160 characters for SMS (280 for WhatsApp)

**ALWAYS ensure messages:**
- Include the pet's name or a first-person reference at least implicitly
- Match the configured archetype's voice consistently
- Are appropriate for time of day (no high-energy messages at 11pm)
- Would make the owner smile, not worry

---

## 4. JimiGPT Birthing Ceremony

This is the onboarding experience unique to JimiGPT. It uses the shared onboarding flow engine (multi-step form) but with pet-specific content and emotional design.

### Flow Steps

```
Step 1: "What's your pet's name?"
  - Single text input, large and centered
  - Warm background gradient (cream → soft gold)
  - No other fields. Just the name. This moment matters.

Step 2: "Show me {pet_name}"
  - Photo upload (1-3 photos)
  - Drag-and-drop or tap-to-upload
  - Show thumbnails as they upload
  - Subtle animation: each photo "develops" like an instant photo

Step 3: "Tell me about {pet_name}"
  - Story prompt: "Tell me about a time {pet_name} surprised you"
  - Textarea with gentle character guidance (not hard limit)
  - Warm, encouraging microcopy: "There's no wrong answer. Just tell me a story."

Step 4: "I think I know {pet_name}..."
  - Personality confirmation screen
  - Shows primary archetype name + one-line description
  - Optional secondary archetype
  - User can adjust with simple slider or "That's not quite right" button
  - Key moment: user should think "Yes! That's exactly my pet!"

Step 5: "Creating {pet_name}'s Digital Twin..."
  - Loading/creation animation (3-5 seconds)
  - Pulsing paw print or heartbeat animation
  - Background transitions to warmer tones
  - Optional: subtle sound effect (heartbeat)

Step 6: "{pet_name} is here!"
  - Reveal: The Digital Twin's first message appears
    (Generated in real-time using the newly created EntityProfile)
  - Birth certificate displayed below
  - Share button for birth certificate
  - CTA: "Set up your message schedule" → configure daily triggers
```

### Birth Certificate

Generated document (PNG for sharing, PDF for download) containing:
- Pet's name (large, prominent)
- "Born" date (date of Digital Twin creation)
- Pet's archetype name ("Personality: The Loyal Shadow")
- One of the uploaded photos (or AI-enhanced version in Phase 2)
- Owner's name listed as "Parent"
- Unique certificate number
- JimiGPT branding (subtle)

---

## 5. JimiGPT Trigger Configuration

**REFERENCES:** Category Architecture Section 5, Stage 1

### Default Trigger Schedule (New Users)

Users can customize all of these during or after onboarding.

| Trigger | Type | Default Time | Message Category |
|---------|------|-------------|-----------------|
| Morning greeting | Time-based | 08:00 local | Morning Greeting |
| Midday check-in | Random interval | 11:00-14:00 local | Caring Check-in |
| Afternoon personality | Random interval | 14:00-17:00 local | Personality Moment |
| Evening meal | Time-based | 18:00 local | Pet Needs |
| Goodnight | Time-based | 21:00 local | Caring Check-in |

### Quiet Hours
- Default: 22:00 - 07:00 (no messages)
- User-configurable
- Respected absolutely — no overrides for any reason

### Frequency Limits
- Maximum 5 messages per day (prevents overwhelming)
- Minimum 1 message per day (prevents the twin feeling "dead")
- At least 2 hours between messages (prevents clustering)

---

## 6. JimiGPT Trust Ladder Adaptations

**REFERENCES:** Category Architecture Section 6

### Stage-Specific Behavior for Pet Digital Twins

**Stranger Trust (First 24 hours):**
- Pet introduces itself simply: "Hi! I'm {name}. I like naps and snacks."
- Messages are short, warm, low-presumption
- No references to shared history (there isn't any yet)
- Maximum 3 messages on day 1

**Initial Trust (Days 2-7):**
- Pet starts referencing details from onboarding: "You said I love the park. Is that the one with the big trees?"
- One personality refinement question per day (via debrief loop): "Do I really knock things off tables or was that a one-time thing? 😏"
- Messages get slightly longer and more characterful

**Working Trust (Weeks 2-4):**
- Pet references past messages naturally: "Remember yesterday when I told you about the sock? I found another one."
- Wider range of message types
- Personality feels settled and recognizable
- Introduce sharing features (birth certificate reminder, message screenshots)

**Deep Trust (Month 2+):**
- Pet reflects on the relationship: "We've had 30 mornings together now. You always give me extra treats on Saturdays."
- Handles tonal shifts (user seems stressed, pet adjusts)
- Richer, more nuanced personality expression

**Sustained Alliance (Month 3+):**
- Pet becomes a genuine emotional anchor
- References long-term patterns
- If/when grief features are introduced, this trust level enables that transition

---

## 7. JimiGPT-Specific API Endpoints

**EXTENDS:** Category Architecture Section 9

```
/api/v1/jimigpt/
├── POST /birth              # Birthing ceremony — creates entity from onboarding data
│   Request: { name, photos[], story, confirmed_archetype }
│   Response: { entity_id, first_message, birth_certificate_url }
│
├── POST /analyze-photos     # Vision API analysis during onboarding
│   Request: { photos[] }
│   Response: { species, breed_guess, appearance_notes, energy_estimate }
│
├── GET /certificate/{id}    # Retrieve birth certificate
│   Response: { certificate_image_url, certificate_pdf_url }
│
├── POST /debrief            # Personality refinement response
│   Request: { entity_id, question_id, user_response }
│   Response: { personality_updated: bool, new_archetype_weights }
│
└── PATCH /schedule          # Update message schedule preferences  
    Request: { entity_id, triggers[] }
    Response: { updated_triggers[] }
```

---

## 8. JimiGPT Safety & Escalation

**REFERENCES:** Category Architecture Section 7

### JimiGPT Escalation Thresholds

JimiGPT primarily operates at Levels 0-1. Escalation beyond that is rare but handled.

**Level 0 (Normal):** Standard messaging. Pet is playful and warm.

**Level 1 (Attention):** User seems down (detected from message replies, reduced engagement). Pet adjusts to gentler, more supportive messages. "I noticed you've been quiet. I'm just here on the couch if you need me."

**Level 2 (Concern):** User explicitly mentions distress related to the pet (illness, upcoming loss) or personal distress. Pet acknowledges with warmth but gently suggests human support. "I wish I could help more. Maybe talking to someone would feel good right now?"

**Level 3+ (Rare):** If crisis language is detected in user replies, the system pauses pet messaging and provides crisis resources. The pet does NOT attempt to be a therapist.

### Veterinary Deflection
If a user asks the Digital Twin about health symptoms, medication, or treatment:
- Pet responds in character but deflects: "{pet_name} tilts head. I don't know about that stuff. Maybe ask the person in the white coat?"
- System provides a gentle note: "For health questions about your pet, please consult your veterinarian."

---

## 9. JimiGPT Monetization Architecture

### Subscription Tiers

**Free Tier:**
- Create one Digital Twin (full birthing experience)
- 7-day free trial of all messages
- After trial: 1 message per day (morning greeting only)
- Birth certificate (shareable)

**Premium ($5.99/month or $49.99/year):**
- Full message schedule (up to 5/day)
- All message categories
- Personality refinement (debrief loop)
- Message history
- Quiet Mode controls
- Priority personality generation

**Lifetime Memorial Pass ($149 one-time — future phase):**
- When pet passes, Digital Twin transitions to memorial mode
- Preserved indefinitely
- Physical keepsake option (printed certificate, memorial card)

### Payment Integration
- Stripe Checkout for subscription management
- Stripe Webhooks for subscription status updates
- Store subscription_status in user_profiles table

---

## 10. JimiGPT Phase Roadmap

### Phase 1A: Personality Engine (Weeks 1-3)
- Core types (PetProfile extending EntityProfile)
- 8 pet archetype YAML configs
- Archetype blending logic
- Prompt builder (profile → system prompt)
- Photo analysis via Claude Vision API
- Story prompt → personality signal extraction
- Tests for all of the above

### Phase 1B: Message Pipeline (Weeks 3-5)
- Time-based trigger engine
- Random interval trigger engine
- Context assembly (personality + time + history)
- Message generation (LLM call with assembled prompt)
- Quality gate (repetition, tone, length, forbidden phrases)
- Twilio SMS delivery
- Nightly batch pre-generation job
- Tests for all of the above

### Phase 1C: Birthing & Onboarding (Weeks 5-7)
- Multi-step onboarding Next.js pages
- Photo upload and processing
- Personality confirmation UI
- Creation ceremony animation
- Birth certificate generation
- Message schedule setup UI
- Supabase Auth integration
- Stripe payment integration

### Phase 1D: Feedback & Polish (Weeks 7-8)
- Personality debrief loop (pet asks refinement questions)
- Thumbs up/down on messages
- Quiet Mode
- Basic analytics
- User testing with 5-10 real users
- Iterate based on feedback

### Phase 2: AI Images & Voice (Weeks 9-12)
- AI image generation of pet in scenes
- Social sharing (birth certificate + images)
- Voice messages via ElevenLabs TTS
- WhatsApp delivery channel

### Phase 3: Depth (Months 4-6)
- Vet records integration
- Milestone timeline
- Advanced personality evolution
- Grief transition support (memorial mode)
- Multi-pet support

---

## 11. JimiGPT-Specific Dependencies

In addition to the shared stack (Category Architecture Section 2):

```toml
# pyproject.toml — JimiGPT-specific dependencies

[project]
name = "jimigpt"
version = "0.1.0"
requires-python = ">=3.12"

dependencies = [
    # Shared (from category architecture)
    "fastapi>=0.110.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.6.0",
    "supabase>=2.3.0",
    "anthropic>=0.18.0",
    "twilio>=9.0.0",
    "apscheduler>=3.10.0",
    "httpx>=0.27.0",
    "python-dotenv>=1.0.0",
    
    # JimiGPT-specific
    "pillow>=10.2.0",         # Image processing for birth certificates
    "pyyaml>=6.0.1",          # Archetype config loading
    "jinja2>=3.1.0",          # Prompt templates
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.3.0",
    "mypy>=1.8.0",
    "httpx>=0.27.0",          # For FastAPI test client
]
```
