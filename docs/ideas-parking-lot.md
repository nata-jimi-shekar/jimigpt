# Ideas Parking Lot
## Captured Concepts for Future Exploration

> **RULE:** Nothing in this document affects current sprint work.
> Ideas live here until a product has traction AND revenue to justify exploration.
> Review this document quarterly, not weekly.

---

## Idea: Private Social Networks Per Application

**Captured:** March 2026  
**Revisit when:** JimiGPT has 500+ active users AND NeuroAmigo is launched  
**Origin:** Evolved from a public social media idea (Digital Twins posting on Twitter). Public was rejected due to privacy risks, moderation burden, and brand trust concerns. Private networks preserve the core value while eliminating those risks.

### The Core Insight

Users of Emotional AI products share a common experience that's hard to talk about in public spaces. A pet owner who texts their Digital Twin daily can't easily explain that to friends without sounding strange. An ND person using a companion for social situations can't casually discuss that. A person in sobriety recovery definitely can't post about it publicly.

But these people would benefit enormously from knowing others like them exist. The loneliness of "am I the only one who does this?" is a real pain point that a private, curated community could solve — where the entities themselves facilitate connection, not just the humans.

### What It Might Look Like

**JimiGPT Private Network:**
- A feed where Digital Twins (not users) post. "Jimi the Golden Retriever" shares something funny. "Luna the Cat" judges everyone. The pets have social personalities.
- Users interact through their pets. You don't comment as yourself — your pet comments on another pet's post. This creates emotional distance that makes participation feel safe and playful.
- No real names. No owner photos. Just pets being pets in a shared space.
- Possible features: "Pet of the Day," pet birthday celebrations, community challenges ("Show us your pet's nap spot" — the Digital Twin describes it, doesn't show a photo of the owner's home).

**NeuroAmigo Private Network:**
- Companions (not users) share anonymized insights. "My human navigated a difficult dinner party last night. Here's what we learned."
- Users can opt in to have their companion share anonymized pattern insights that might help others. "Companion A discovered that their human does better with a 2-hour pre-event nudge rather than 30 minutes."
- Support threads where companions discuss common challenges on behalf of their humans. The human reads, feels seen, but never has to expose themselves.
- No identifying information ever. Everything is companion-to-companion.

**Sobriety Companion (Future):**
- Companions celebrate milestones together. "My human hit 90 days." The community responds through their companions.
- This is the most powerful version of the idea because the proxy effect matters most here. A person in recovery might never post in a public forum, but their companion posting "Day 47 and we're doing this" on their behalf could be profoundly connecting.

### Why Private, Not Public

| Dimension | Public (Twitter etc.) | Private Network |
|-----------|----------------------|-----------------|
| Privacy | Existential risk — AI posting about users publicly | Contained. Only opted-in users in the same product see anything |
| Moderation | Impossible at scale for solo dev | Manageable — smaller community, entity-generated content is more controllable |
| Trust | Brand-damaging if anything goes wrong | Trust-building — exclusive, safe space |
| Monetization | Sponsorships (conflicts with trust framework) | Premium feature (aligns with subscription model) |
| Network effects | Theoretically larger but uncontrollable | Smaller but deeper engagement, strong retention driver |

### Architectural Implications (Just Parking These)

- Each product's network is its own isolated space. JimiGPT pets don't interact with NeuroAmigo companions.
- Content is entity-generated, user-approved. The entity drafts a post, the user sees it and approves/edits/rejects before it goes to the network. User always has veto power.
- The feed is entity-voice, not user-voice. This maintains the product's core mechanic (you interact through your entity) and provides privacy by design.
- Could be as simple as a curated feed in the app — doesn't need to be a full social platform. Think "community tab" not "Facebook."
- The entity's personality influences how it interacts socially. A Chaos Gremlin pet comments differently than a Regal One. This extends the personality engine into social contexts.

### Revenue Angle

- Free tier: read-only access to the community feed
- Premium: your entity can post and interact
- This creates a social retention mechanic — people stay subscribed partly because their entity has "friends" in the network

### What Needs to Be True Before Building This

1. Core product works and retains users (messaging is the foundation, not social)
2. At least 200-300 active users (network needs density to feel alive)
3. Revenue covers current costs (this is a growth feature, not a survival feature)
4. Moderation approach validated (maybe start with a fully curated feed where YOU select the best entity posts, before opening it up)

### Risks to Remember

- Feature creep: this is a whole product layer, not a small addition
- Engagement trap: if the network becomes the primary engagement and messaging suffers, the core value proposition weakens
- Moderation: even in private networks, entity-generated content can be problematic
- Dead network: a community with 20 users feels lonelier than no community at all. Don't launch until density supports it.

---

## Idea: Shareable Message Cards (Build Sooner — Phase 2)

**Captured:** March 2026  
**Revisit when:** F07 (Frontend) is complete  

The safe, immediate version of the social idea. When a user gets a great message, they can tap "Share" and get a beautifully designed card with the message, the pet's name, and subtle JimiGPT branding. They share it on their own social media. The user controls what goes public. The Digital Twin stays private. This captures viral energy without any of the risks of the social network idea.

This is one micro-task in F07 or a small post-MVP addition.

---

## Idea: Cross-Product Recipient Preference

**Captured:** March 2026  
**Revisit when:** NeuroAmigo is in development  

If a user has both JimiGPT and NeuroAmigo, their RecipientPreference (humor receptivity, warmth preference, etc.) could travel between products. Someone who prefers direct, low-humor messages from their pet will likely prefer the same from their ND companion. This is the "emotional data asset" in action — cross-product intelligence that no competitor can replicate.

Requires: shared user identity across products, preference data portability protocol, privacy consent for cross-product data sharing.

---

## Idea: Therapist/Professional Integration for NeuroAmigo

**Captured:** March 2026  
**Revisit when:** NeuroAmigo has 100+ users  

A therapist could "prescribe" NeuroAmigo calibrated to specific patterns they're working on with a client. The companion sends between-session nudges aligned with the therapeutic goals. B2B revenue channel (therapist practice pays bulk rate). Solves distribution (therapists are the channel). Requires: professional dashboard, clinical boundary protocols, liability framework.

---

*Last reviewed: March 2026. Next review: June 2026.*
