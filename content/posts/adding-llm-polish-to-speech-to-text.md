---
title: "Adding LLM Polish to a Speech-to-Text App"
date: 2025-12-22
tags: [rust, macos, llm, speech-to-text, groq]
summary: "How I added an optional LLM post-processing step to clean up voice transcriptions, with lessons on prompt engineering and graceful degradation."
---

Voice transcription is messy. Even the best models like Whisper faithfully reproduce every "um", "uh", and rambling run-on sentence. That's correct behavior for transcription, but not what you want when texting someone.

I added a "polish mode" to my macOS speech-to-text app that optionally sends Whisper's output through an LLM to clean it up. The interaction model: hold Fn to record, tap Ctrl anytime during recording to enable polish, release to transcribe and paste.

## The Modifier Key Challenge

The obvious approach - require Ctrl held simultaneously with Fn - felt clunky in testing. You'd have to coordinate two fingers before speaking, and the physical position is awkward.

A "latch" pattern works better: pressing Ctrl anytime while Fn is held latches the polish flag. You can press Ctrl before speaking, during, or just before release. The flag resets when you start a new recording.

```rust
let ctrl_latched = Arc::new(AtomicBool::new(false));

// In the event tap callback:
if key_pressed && !prev_pressed {
    // Recording started - reset latch
    ctrl_latched.store(false, Ordering::SeqCst);
    start_recording(&state);
} else if !key_pressed && prev_pressed {
    // Recording stopped - check if Ctrl was ever pressed
    let polish = ctrl_latched.load(Ordering::SeqCst);
    stop_recording(&state, polish);
}

// Latch Ctrl if pressed anytime during recording
if key_pressed && ctrl_pressed {
    ctrl_latched.store(true, Ordering::SeqCst);
}
```

The macOS `CGEventFlags` expose modifier state as bitmasks. Control is `0x40000`:

```rust
const CONTROL_KEY_FLAG: u64 = 0x40000;

let flags = event.get_flags().bits();
let ctrl_pressed = (flags & CONTROL_KEY_FLAG) != 0;
```

## The Polish Function

The polish step is a straightforward LLM API call. I'm using Groq's hosted llama-3.3-70b-versatile because I'm already using Groq for Whisper transcription - one API key, one vendor.

```rust
fn polish_text(text: &str, api_key: &str) -> Option<String> {
    let client = reqwest::blocking::Client::new();

    let body = serde_json::json!({
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "system",
                "content": "Clean up this voice message for texting. Remove filler words (um, uh, like, you know). Fix punctuation and sentence structure. Break up run-on sentences. Keep it casual. No trailing period. Output ONLY the cleaned text - no explanations, no quotes."
            },
            {
                "role": "user",
                "content": text
            }
        ],
        "temperature": 0.2
    });

    let response = client
        .post("https://api.groq.com/openai/v1/chat/completions")
        .header("Authorization", format!("Bearer {}", api_key))
        .header("Content-Type", "application/json")
        .json(&body)
        .timeout(Duration::from_secs(30))
        .send()
        .ok()?;

    if !response.status().is_success() {
        return None;
    }

    let chat_response: ChatResponse = response.json().ok()?;
    chat_response.choices.first().map(|c| c.message.content.clone())
}
```

The function returns `Option<String>` - this matters for the fallback logic.

## Parsing the Response

Groq uses the OpenAI-compatible chat completions format. The response structure:

```rust
#[derive(serde::Deserialize)]
struct ChatResponse {
    choices: Vec<ChatChoice>,
}

#[derive(serde::Deserialize)]
struct ChatChoice {
    message: ChatMessage,
}

#[derive(serde::Deserialize)]
struct ChatMessage {
    content: String,
}
```

Using `serde` to parse into typed structs catches malformed responses at parse time rather than panicking on field access later.

## Prompt Engineering Lessons

The system prompt went through several iterations:

**First attempt:** "Clean up this transcription."

Problem: The LLM would respond conversationally. "Sure! Here's the cleaned up version: ..."

**Second attempt:** "Output only the cleaned text."

Problem: It would wrap the output in quotes: `"Here's what I meant to say"`

**Third attempt:** Added explicit prohibitions.

```
Output ONLY the cleaned text - no explanations, no quotes.
```

This worked. The key insight: LLMs default to being helpful and conversational. For tool use, you need to explicitly tell them to suppress that behavior.

Other prompt decisions:

- **"Keep it casual"** - prevents the LLM from making the text overly formal
- **"No trailing period"** - texting convention; a period at the end feels curt
- **"Break up run-on sentences"** - spoken language naturally runs together

Low temperature (0.2) keeps output consistent. Higher temperatures occasionally produced creative reinterpretations of what I said.

## Graceful Degradation

The polish step can fail: network issues, rate limits, API changes. The user still expects their transcription to paste.

```rust
let final_text = if polish {
    polish_text(text, api_key).unwrap_or_else(|| text.to_string())
} else {
    text.to_string()
};
```

`Option::unwrap_or_else` is the right pattern here. If polish fails for any reason, fall back to the raw Whisper transcription. The user gets something rather than nothing.

This is a general principle for LLM features: treat them as enhancements, not requirements. The core functionality should work without them.

## Latency Considerations

Polish adds a second API call, roughly 200-400ms on Groq. For a texting use case, this is acceptable - you're not in a real-time conversation. For live captioning or dictation into a text field, it would be too slow.

The transcription already happens in a background thread:

```rust
thread::spawn(move || {
    transcribe_and_paste(audio_data, sample_rate, &api_key, polish);
});
```

Both the Whisper call and the polish call happen sequentially in this thread. The UI remains responsive; the user just waits slightly longer for paste.

## Trade-offs

**When polish helps:**
- Texting, where filler words and run-ons look sloppy
- Drafting messages you want to sound more coherent
- Quick notes that benefit from basic cleanup

**When to skip it:**
- Dictating into forms or code comments
- When you want exact transcription (quotes, interviews)
- Low-latency scenarios

**What polish can break:**
- Proper nouns and technical terms may get "corrected"
- The LLM might misinterpret intent on ambiguous input
- Short inputs ("ok", "yes") sometimes get expanded unnecessarily

The latch pattern makes this an explicit user choice. Default is raw transcription; polish is opt-in.

## Conclusion

- **Latch pattern beats simultaneous press** - let users enable modes at any point during an action
- **Explicit prompt constraints** - tell the LLM what NOT to do (no explanations, no quotes)
- **Low temperature for tools** - you want consistency, not creativity
- **Graceful fallback is mandatory** - LLM features should enhance, not gate, core functionality
- **Choose your latency budget** - 200-400ms is fine for async use cases, not for real-time
