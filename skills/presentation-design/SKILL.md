---
name: presentation-design
description: Design philosophy for slide decks that are presented live by a speaker. Use this skill whenever creating, revising, outlining, or critiquing slides, decks, or presentations in any tool (PowerPoint, Google Slides, Keynote, slide artifact types, HTML slides, Beamer), including single slides, talk outlines, lecture, workshop or conference decks, code walkthroughs, and requests to "make a slide about X." Covers how much goes on a slide, how slides relate to what the speaker says, the assertion-evidence slide form, sequencing, builds, code on slides, speaker notes, and decks that get shared afterward. Use it alongside whatever technical skill builds the file; this one decides what goes on the slides, that one decides how to build them.
type: Agent Skill
title: presentation-design — slides that support a speaker
tags: [presentation-design, slides, public-speaking, assertion-evidence, multimedia-learning, technical-presentations]
generated: { by: kilo/zai-org.glm-5.3-flash, at: 2026-11-11T10:50:00-05:00 }
status: stable
sources:
  - id: mayer-multimedia
    resource: https://www.jsu.edu/online/faculty/MULTIMEDIA%20LEARNING%20by%20Richard%20E.%20Mayer.pdf
    title: Richard E. Mayer — Multimedia Learning (research on redundancy and coherence principles)
  - id: alley-assertion-evidence
    resource: https://www.assertion-evidence.com/
    title: Assertion-Evidence slides — Michael Alley, Pennsylvania State University
  - id: simons-opinions
    resource: Simon Stone's personal opinions :-)
---

# Presentation design: slides that support a speaker

A deck for a live talk is not a set of posters. It's the visible half of a performance whose other half is the speaker's voice. Most generated decks get this wrong in a predictable way, and this skill exists to stop that.

## The core problem: two competing streams

The default failure looks like this. Each slide is designed as if it will be read alone: a grid of cards, several columns, a dozen labeled facts, a callout, a takeaway line. It looks finished in a thumbnail.

Then someone presents it. They don't read it out loud, and they don't cover all of it. They narrate the main point in their own words. The audience now gets two streams of words, spoken and written, that only partly overlap. Reading and listening draw on the same verbal channel, so people can't follow both. They lose the thread. (In Mayer's multimedia learning research this falls under the redundancy and coherence principles.[^mayer-multimedia])

The fix is to design every slide as a companion to speech, not a replacement for it.

## Principles

### 1. Everything visible is something the speaker is addressing right now

At any moment, everything on screen should be part of what the speaker is talking about. For a plain slide that works out to a practical limit: the speaker should be able to cover all of it in about 60 to 90 seconds. If they can't, split the slide.

Splitting is usually the right fix. Six concepts on one slide become six slides, or an intro slide plus six.

Builds are the exception that proves the rule. A slide can stay up for four minutes if it reveals in steps and each step is addressed as it appears: an architecture diagram assembled component by component, a pipeline drawn stage by stage, a chart whose series appear one at a time. Seeing the whole system grow is the point, and splitting it across eight slides would lose that. What fails is putting the finished, complex version on screen at once and talking about one corner of it.

The opposite failure exists too. Slides that flick past every 30 seconds fragment a talk just as badly. A slide should hold one complete thought, not half of one.

### 2. Slides hold anchors, the speaker holds sentences

On-screen words should echo the speech, not diverge from it and not duplicate it. Text that diverges creates the second stream. Text that duplicates the speech word for word causes its own problem: the audience reads ahead, finishes first, and then waits for the speaker to catch up. Research on redundancy finds that verbatim on-screen text plus identical narration hurts comprehension too.

What works is short anchors: a claim, a key term, a few words the audience will hear the speaker say and can find on the screen in a glance. The speaker supplies the full sentences, the explanation, the examples.

Test: every phrase on the slide should be something the speaker says or plainly refers to. No sentence on the slide (other than the headline and a quoted example) should be one the speaker simply reads aloud.

### 3. Default slide form: a claim and its evidence

Use the assertion-evidence form (from Michael Alley's work on technical presentations[^alley-assertion-evidence]) as the default:

- **Headline:** a short full-sentence claim stating the slide's one message. "Caching cut median latency in half," not "Caching results."
- **Body:** visual evidence for that claim. A chart, a diagram, a photo, a screenshot, one large example, a single big number. No bullets.

The visual is the main thing on the slide, not decoration added to fill space. It's also the part the audience absorbs while listening without competing for the verbal channel, which is why this form beats topic-plus-bullets.

Fall back to bullets only when there's no honest visual for the point (an abstract argument, a short list of recommendations, an agenda). When you do use them, keep them as anchors: two to four, each a few words. A clean bullet slide is still far better than an overloaded layout.

Rough targets:

- Headline: one or two lines, a claim the audience could repeat
- Body text, when there is any, large enough to read from the back (24pt or more on a widescreen slide)
- One focal element per slide

Multi-column grids, card layouts, and dashboards are for content that really is a side-by-side comparison, and only when the speaker will walk through each part (or reveal them one at a time).

### 4. Slides live in a sequence

A slide is never standalone. Something leads into it and something comes out of it.

- Plan the talk first, as spoken beats. Then cut it into slides. Don't design slides and then work out what to say over them.
- One message per slide. The headline states it.
- If a slide needs its own intro, summary, and conclusion to make sense, it's trying to be a poster.
- When asked for "a slide" on a topic with a lot of content, delivering a short sequence instead is usually correct. Say why in one line.

### 5. Concise should look deliberate, not empty

A slide that shows just enough is different from one that looks unfinished. Sparse content on a bare canvas reads as the second kind. The assertion-evidence form solves most of this on its own, because the visual fills the slide with something meaningful. Beyond that:

- **A light template frame.** A consistent header and footer orient the audience and make a sparse slide look intentional. Header: section name or a progress marker ("Part 2 of 4"). Footer: slide number, and maybe the talk title. Keep it light. Logos, event names, hashtags, and URLs repeated on every slide are just clutter moved to the edges. Put those on the title and closing slides.
- **Intentional whitespace inside the frame.** Whitespace looks designed when there's structure around it.

Avoid visuals that demand reading (charts with dense labels, diagrams with paragraphs in the boxes, screenshots of text) and graphics unconnected to the claim.

### 6. Code on slides

Code is the most common way technical slides get overloaded. A full function in 12pt mono is unreadable from the third row and competes with everything the speaker says.

- Show the fewest lines that make the point, often 3 to 10. Elide the rest with `...`.
- Make it big: 20pt or more.
- Highlight the line being discussed (dim the others, or use a box). If several lines matter in turn, step through them with builds.
- Use syntax highlighting the room can see. High contrast beats a pretty editor theme.
- Put the full code in a repo or gist and show the link once, usually at the end.
- For a live demo, have a static slide of the key result as a fallback.

### 7. The narration goes in the speaker notes

Everything the speaker will say goes in the notes, written to be spoken: the explanation, the context, the aside, the transition into the next slide. At normal speaking pace that's about 120 to 200 words for a 60 to 90 second slide. If one slide's notes run much longer, it probably holds more than one message: split it (or turn it into a build).

Notes should pick up where the previous slide's notes ended and should refer to every element on the slide.

## Decks have an afterlife

Most decks get shared after the talk: posted on a course site, emailed to people who missed it, kept as reference. Lean, speaker-dependent slides are close to useless on their own. Don't fix that by making the slides denser, which breaks them for the live talk. Instead:

- **Write the speaker notes as clean prose** a reader could follow without the speaker. Full sentences, no "[pause here]" scribbles. Then a notes-page export (slide plus notes, as PDF) works as a handout.
- **Or write a companion document** when the material warrants it: a short write-up, a README in the code repo, a reference page.
- Assertion-evidence slides help here, because a headline that states a claim still says something when nobody is presenting it.

When the deck will clearly be shared, write notes to that standard by default and mention the handout export.

## Adjust for the audience

The density limits are a dial, not a fixed number. Turn it toward a bit more on-screen text (fuller headlines, a key term or two more) when:

- many in the audience are non-native speakers of the talk's language
- people who are hard of hearing will attend and captions aren't guaranteed
- the talk is recorded or streamed and audio may be poor
- the room is large and the speaker is hard to hear

Turn it the other way for an expert audience in a small room. The principles stay the same; only the amount of anchoring changes.

## When the rules change

Some decks aren't presented:

- **Pre-reads** are read without a speaker, so they must carry the whole argument. A document is usually better than a dense deck. Offer that.
- **Reference slides** (agenda, resource list, contact slide left up during Q&A) can hold more, because the audience reads them while nobody is talking.

If it's unclear whether a deck will be presented or read, assume presented and mention the trade-off in one line.

## Worked example

A request to "create a slide showing typical AI tells in generated content."

**The poster version (wrong for a talk).** One widescreen slide: a title, a subtitle, a 2x3 grid of six cards (each with a numbered circle, a heading, a struck-through example, and a two-line description), and a takeaway line. Around 150 words and six concepts at once. Presented, the speaker summarizes it in a minute while the audience tries to read six cards.

**A better version.** Eight slides: an opener, one slide per tell, a close. Each tell slide has a title ("2. The fake reversal"), one example sentence set large and struck through in red, and two short bullets. Speaker notes for each run under a minute. This fixes the density problem, but the bullets mostly restate what the speaker says, and on a bare white canvas the slides look empty.

**The assertion-evidence version.** Same sequence, different slide form. Each tell slide:

- Headline as a claim: "Models invent a position just to correct it"
- Evidence filling the body: the example sentence, very large, struck through in red ("It's not just a tool, it's a mindset."), perhaps followed by a build that reveals a plain rewrite beneath it ("It's a useful tool.")
- No bullets. The definition and the "not only X but also Y" variant go in the notes, where the speaker says them.
- A light frame: "Tell 2 of 6" in the header, slide number in the footer.

The struck-through example was always the part doing the work: it tells the audience "this is the bad version" before the speaker says a word. This version makes it the whole slide. Notes are written as clean prose, so the notes-page PDF doubles as a handout.

## Checklist before delivering a deck

- Is everything visible at each moment something the speaker is addressing then? (For plain slides: coverable in 60 to 90 seconds.)
- Are on-screen words anchors rather than sentences the speaker will read aloud?
- Does each headline state a claim, and does the body show evidence for it?
- Where there are bullets, is there really no visual that would work instead?
- Does each slide follow from the previous one and lead into the next?
- Is the frame light, with logos and URLs kept to the title and closing slides?
- Is any code trimmed, large, and highlighted, with the full version linked?
- Would the notes make sense to someone reading the deck after the talk?
- Is the density right for this audience?

## Working with technical slide skills

Use this skill for what goes on the slides and how they're sequenced. Use the relevant technical skill (pptx, Google Slides, a slide artifact type) for building the file, including how to make builds and animations in that format. Where a technical skill's design advice pushes toward richer layouts on a single slide, this skill's density limits win: add evidence and framing, not more content. A light header and footer frame is wanted here even where a technical skill warns against decorative bars and stripes; the difference is that the frame carries information.

[^mayer-multimedia]: Mayer, *Multimedia Learning* — the redundancy principle (on-screen text duplicating narration hurts comprehension) and the coherence principle (exclude extraneous material).
[^alley-assertion-evidence]: Alley, M. — the assertion-evidence slide form: a full-sentence assertion as headline, visual evidence as body. See https://www.assertion-evidence.com/.