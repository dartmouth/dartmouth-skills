---
type: Reference
title: Images with Clef and Jev on the Dartmouth Chat API
description: How to send images to cloudflare.clef and typesafe.jev through the Dartmouth Chat decision endpoints (https://chat.dartmouth.edu/api), with each model's request format, limits and Box questions.
tags: [decision-models, clef, jev, images, multimodal, box, dartmouth-chat, litellm]
generated: { by: claude-code/claude-opus-5-5, at: 2026-11-09T16:30:00-05:00 }
stale_after: 2027-01-09T00:00:00Z
status: draft
sources:
  - id: typesafe-images
    resource: https://docs.typesafe.ai/images.md
    title: TypeSafe docs — Images
  - id: typesafe-models
    resource: https://docs.typesafe.ai/models.md
    title: TypeSafe docs — Models
  - id: litellm-jev-images
    resource: https://docs.litellm.ai/blog/typesafe_jev_images
    title: LiteLLM — Day 0 support for TypeSafe Jev 1.14 (images, box questions, long context)
---

# Images with Clef and Jev

Both decision models on `https://chat.dartmouth.edu/api` accept images, on
`POST /api/v1/systemone` and `POST /api/v1/decisions`. The two models take them
in **different fields**, and sending one model's format to the other returns 400.

While building an image feature, add a control question ("Is an image
attached?"). If it comes back near 0, the image never reached the model.

## Clef: `images` list

```json
{
  "model": "cloudflare.clef",
  "state": "Answer about the attached image.",
  "images": ["data:image/png;base64,iVBORw0KGgo..."],
  "questions": {"word": {"type": "choice", "instructions": "What word is written in the image?",
                         "criteria": {"STOP": null, "GO": null, "none": null}}}
}
```

- Each entry is a `data:image/...;base64,` URL or an `http(s)` URL. Plain base64 returns 400.
- PNG, JPEG and WebP work.
- **At most 2 images per request** (vLLM limit on the Dartmouth deployment). Images keep their order, so "the first image" and "the second image" work in `instructions`.
- One small image added about 70 input tokens in testing.

## Jev: `assets` map

Jev takes images as named `assets`. Each name must appear somewhere in `state`,
a question's `instructions` or its `criteria`, or the request fails with 400.[^typesafe-images]

```json
{
  "model": "typesafe.jev",
  "state": "Look at photo.png.",
  "assets": {"photo.png": {"data_base64": "iVBORw0KGgo...", "format": "png"}},
  "questions": {"word": {"type": "choice", "instructions": "What word is written in photo.png?",
                         "criteria": {"STOP": null, "GO": null, "none": null}}}
}
```

- `data_base64` is plain base64 with no `data:` prefix. `format` is `png`, `jpg` or `jpeg`.
- **PNG or JPEG stills only.** Convert WebP, GIF and HEIC first.[^typesafe-images]
- **280 to 1568 px per side**, up to 16 MiB per file and 32 MiB per request. A smaller image returns 400 `Invalid image dimensions.`[^typesafe-images]
- There is no fixed image count; the limit is size and context.[^typesafe-images]
- Images bill as input tokens. A 512×512 image cost about 3,300 input tokens per request in testing.[^typesafe-models]
- Images are an experimental TypeSafe feature ("Dreamer-ready"), and the format, answers and limits can change between releases.[^typesafe-images]
- Upstream, each request needs the header `TypeSafe-Danger-Zone-Images: true`.
  The Dartmouth gateway adds it for you, but sending it does no harm.[^litellm-jev-images]

### Box questions (Jev 1.14)

A `box` question finds one thing in an image and returns its edges as fractions
of the image width and height, measured from the top-left corner.[^typesafe-images]

```json
"where": {"type": "box", "instructions": "Where is the red square in photo.png?"}
```

returns

```json
{"type": "box", "box": {"top": 0.09, "bottom": 0.41, "left": 0.09, "right": 0.41}, "confidence": 0.95}
```

In testing, the box landed within about 0.03 of the true edges.

## OpenAI Decisions format (`/api/v1/decisions`)

On `/api/v1/decisions`, send images as OpenAI-style `input_image` parts. The
gateway converts them to `assets` for Jev.[^litellm-jev-images] Tested with Jev:

```json
{
  "model": "typesafe.jev",
  "input": [{"role": "user", "content": [
    {"type": "input_text", "text": "Look at the image."},
    {"type": "input_image", "image_url": "data:image/png;base64,iVBORw0KGgo..."}
  ]}],
  "questions": [{"name": "word", "type": "choice", "instructions": "What word is written in the image?",
                 "choices": [{"value": "STOP"}, {"value": "GO"}, {"value": "none"}]}]
}
```

## The `decide` MCP

Pass `image_paths` to `decide`. The server sends `images` to Clef. For any model
whose name contains `jev`, it converts them to `assets` named `image_1.png`,
`image_2.png` and so on, and lists those names in `state`:

- appended as text to a string `state`
- as an `attached_images` key on an object `state`
- as an extra item on an array `state`

Refer to the images as "the attached image" or by those names in `instructions`.

[^typesafe-images]: TypeSafe docs — Images
[^typesafe-models]: TypeSafe docs — Models
[^litellm-jev-images]: LiteLLM — Day 0 support for TypeSafe Jev 1.14 (images, box questions, long context)
