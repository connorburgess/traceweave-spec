# Content profiles

The shared core handles exact subjects, private commitments, extraction configuration identity, and evidence interpretation. Matching algorithms and thresholds belong to versioned profiles with their own benchmarks.

| Profile | Status | Questions before implementation |
| --- | --- | --- |
| [Code](code.md) | First planned experiment | Scope normalization, partial fragments, generated code, AI refactoring |
| [TypeScript/JavaScript](typescript.md) | `ts-tokens` frozen; `tsx-tokens` deferred draft | Open decisions are listed in the profile |
| [Text](text.md) | `text-plain` frozen; `text-markdown` draft | Open decisions are listed in the profile; translations and paraphrases remain research only |
| Image | Research only | Decoding, orientation, crops, resizing, composites, near-identical independent images |
| Audio | Research only ([scoping note](../research/lanes/15-audio-video-scoping.md)) | Decoding, sample rate, channel mixing, alignment, short excerpts, pitch/speed changes |
| Binary | Research only | Architecture, compiler, packing, sections, relocation, shared runtime code |

Text normalization can erase distinguishing information. Image pHash is not a general crop/derivative detector. Chromaprint is designed for near-identical audio, not every audio-provenance problem. TLSH thresholds depend on the task and cannot independently assert compilation lineage. [Chromaprint](https://github.com/acoustid/chromaprint), [TLSH](https://github.com/trendmicro/tlsh).

No universal similarity threshold is defined for these profiles. Do not claim multimodal detection merely because the core record accepts several content kinds. Video and other formats need separate profiles rather than inheriting image/audio guarantees; see the [audio and video scoping note](../research/lanes/15-audio-video-scoping.md).
