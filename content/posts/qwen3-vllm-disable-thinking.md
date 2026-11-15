---
title: "Qwen3 Disable Thinking in vLLM: enable_thinking false"
date: 2026-11-15
draft: false
tags: [vllm, qwen3, llm, inference]
summary: "Qwen3 on vLLM puts <think> blocks in replies. Disable thinking with enable_thinking false in chat_template_kwargs, or split it out with a reasoning parser."
---

Qwen 3 thinks by default, so on vLLM the reply comes back with a `<think>...</think>` block inside `content`. To disable thinking, send `"chat_template_kwargs": {"enable_thinking": false}` with every request. To keep the thinking and move it out of `content`, start the server with `--reasoning-parser qwen3` and read the `reasoning` field.

I hit this while serving Qwen3-8B and Qwen3-32B (FP8) with vLLM on a GCE A100. My client code stripped `<think>` blocks before it showed a reply. A long thought often ran out of tokens before it closed. After the strip, nothing was left, and the user got an empty reply. The cause was one missing field in the request.

Where the facts come from. Flag names, fields and defaults are quoted from the vLLM docs for v0.33.0, the newest release (2 November 2026), and from the Qwen model cards on Hugging Face. The symptoms and token budgets come from my own runs on the `vllm/vllm-openai:v0.17.0` image. I had no GPU while writing this post. So I checked the requests below against the docs and did not rerun them.

## Disable Qwen3 thinking in vLLM with enable_thinking false

Add `chat_template_kwargs` to the request body:

```bash
curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3-8B",
    "messages": [{"role": "user", "content": "Name three uses of Redis."}],
    "max_tokens": 1024,
    "chat_template_kwargs": {"enable_thinking": false}
  }'
```

The OpenAI Python client has no `chat_template_kwargs` argument. Qwen's vLLM guide says so plainly: "passing `enable_thinking` is not OpenAI API compatible." The vLLM docs send fields like this through `extra_body`:

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="EMPTY")

response = client.chat.completions.create(
    model="Qwen/Qwen3-8B",
    messages=[{"role": "user", "content": "Name three uses of Redis."}],
    max_tokens=1024,
    temperature=0.7,
    top_p=0.8,
    extra_body={
        "top_k": 20,
        "chat_template_kwargs": {"enable_thinking": False},
    },
)
print(response.choices[0].message.content)
```

The sampling values are Qwen's suggestion for non-thinking mode: `Temperature=0.7`, `TopP=0.8`, `TopK=20`, `MinP=0`. `top_k` is not an OpenAI parameter either, so it also goes in `extra_body`.

Here is why the field matters. This is the end of the Qwen3-8B chat template:

```jinja
{%- if add_generation_prompt %}
    {{- '<|im_start|>assistant\n' }}
    {%- if enable_thinking is defined and enable_thinking is false %}
        {{- '<think>\n\n</think>\n\n' }}
    {%- endif %}
{%- endif %}
```

Only an explicit `false` changes the prompt. Then the template writes an empty think block after the assistant tag, and the model goes straight to the answer. A missing field means thinking is on. The model card says the same: "By default, Qwen3 has thinking capabilities enabled." Without a reasoning parser, vLLM hands you the raw text, tags included.

So send the field on every request, `true` or `false`. My rule after this bug was simple. Every code path sets `enable_thinking` itself and never relies on the default.

Recent vLLM has a second way. The docs say `reasoning_effort="none"` makes vLLM inject `enable_thinking = false` into the template kwargs. `reasoning_effort` is a standard OpenAI parameter, so it needs no `extra_body`:

```python
response = client.chat.completions.create(
    model="Qwen/Qwen3-8B",
    messages=[{"role": "user", "content": "Name three uses of Redis."}],
    reasoning_effort="none",
)
```

This is in the vLLM docs from v0.22.0 on. If you also set `enable_thinking` in `chat_template_kwargs`, your value wins.

## Turn thinking off for the whole server

Use `vllm serve` with a default for every request:

```bash
vllm serve Qwen/Qwen3-8B \
    --reasoning-parser qwen3 \
    --default-chat-template-kwargs '{"enable_thinking": false}'
```

Request-level `chat_template_kwargs` still win, so one call can turn thinking back on. The flag is in the docs from v0.14.0 on.

Qwen's vLLM guide offers a harder switch. Start the server with their `qwen3_nonthinking.jinja` file passed to `--chat-template`. Qwen says that template "prevents the model from generating thinking content, even if the user instructs the model to do so with `/think`."

## Split the thinking out with --reasoning-parser qwen3

Sometimes you want the thinking, because it helps on hard questions. You just don't want it in `content`. Start vLLM with the parser:

```bash
vllm serve Qwen/Qwen3-8B --reasoning-parser qwen3
```

The thinking now arrives in its own field. From the vLLM docs: "The `reasoning` field contains the reasoning steps that led to the final conclusion, while the `content` field contains the final conclusion."

```python
response = client.chat.completions.create(
    model="Qwen/Qwen3-8B",
    messages=[{"role": "user", "content": "9.11 and 9.8, which is greater?"}],
    max_tokens=4096,
    extra_body={"chat_template_kwargs": {"enable_thinking": True}},
)
msg = response.choices[0].message
print("reasoning:", msg.reasoning)
print("content:", msg.content)
```

Older guides show other flags. The Qwen3-8B model card still has `vllm serve Qwen/Qwen3-8B --enable-reasoning --reasoning-parser deepseek_r1`. The current vLLM docs use only `--reasoning-parser qwen3`. Qwen's vLLM guide also warns that on vLLM 0.8.5, `enable_thinking=False` did not work together with reasoning parsing. It says vLLM 0.9.0 fixed this with the `qwen3` parser.

You may want the model to think without sending the text back. Then add `"include_reasoning": false` to the request. The docs say "reasoning tokens are still generated (so model quality is unaffected) but excluded from the response." This is in the docs from v0.26.0 on.

### If you cannot change the server flags

Split the text on the last `</think>` in your client. The Qwen3 model card does the same thing in its Transformers example. It looks for the last `</think>` token.

```python
def split_thinking(text: str) -> tuple[str, str]:
    """Split raw Qwen output into (thinking, answer)."""
    head, sep, tail = text.rpartition("</think>")
    if sep:
        return head.replace("<think>", "").strip(), tail.strip()
    if text.lstrip().startswith("<think>"):
        return text, ""  # cut off before the thinking ended
    return "", text.strip()
```

When the answer comes back empty, return an error to the caller. Do not show an empty reply. That was my original bug.

## vLLM reasoning vs reasoning_content

The field changed its name. The vLLM docs warn: "`reasoning` used to be called `reasoning_content`. To migrate, directly replace `reasoning_content` with `reasoning`." They add that old client code "could silently read an empty `reasoning_content`, even when `reasoning` is populated."

The warning is in the docs from v0.12.0 on. Many guides still use `reasoning_content`, Qwen's own vLLM page among them. If one client talks to servers of different ages, read both names:

```python
msg = response.choices[0].message
thinking = getattr(msg, "reasoning", None) or getattr(msg, "reasoning_content", None)
```

## Use /no_think to skip thinking for one turn

Qwen 3 also has a soft switch inside the prompt. The model card says "you can add `/think` and `/no_think` to user prompts or system messages to switch the model's thinking mode from turn to turn."

```bash
curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3-8B",
    "messages": [{"role": "user", "content": "Name three uses of Redis. /no_think"}],
    "max_tokens": 1024,
    "chat_template_kwargs": {"enable_thinking": true}
  }'
```

The soft switch does not remove the tags. The card says that with `enable_thinking=True`, the model "will always output a block wrapped in `<think>...</think>`." It adds that "the content inside this block may be empty." So without a parser, an empty `<think></think>` pair still sits in `content`. With `enable_thinking=False`, "the soft switches are not valid." Use the soft switch for a choice per turn in a chat. Use the flag when code reads the output.

## Disable thinking on Qwen3.6 in vLLM

Qwen 3.6 changes three things.

The soft switch is gone. The Qwen3.6-27B card says: "Qwen3.6 does not officially support the soft switch of Qwen3, i.e., `/think` and `/nothink`." The flag is what remains. The card's own non-thinking example sends `"chat_template_kwargs": {"enable_thinking": False}` in `extra_body`, the same as above.

The opening tag moves into the prompt. This is the end of the 3.6 chat template:

```jinja
    {%- if enable_thinking is defined and enable_thinking is false %}
        {{- '<think>\n\n</think>\n\n' }}
    {%- else %}
        {{- '<think>\n' }}
    {%- endif %}
```

With thinking on, the prompt already ends in `<think>`. So the raw output has a closing `</think>` and no opening tag. A regex that looks for `<think>...</think>` finds nothing, and the whole thought stays in front of the answer. The `qwen3` parser copes with this. In the v0.33 source, it treats output as reasoning until `</think>` arrives. The `split_thinking` function above also copes, because it splits on the last `</think>`.

The card asks for a newer vLLM: "`vllm>=0.19.0` is recommended for Qwen3.6".

One thing I saw myself does not match the card. On a Qwen 3.6 model, my replies kept their thinking even with `enable_thinking: false`. That is why I raised the token budgets in the next section. The card says the flag turns thinking off, and the 3.6 template does handle the flag. I never found the cause, and I can't back my result with a source. Run the check in "Verify it worked" on your own server before you build around either claim.

## Give a thinking model enough max_tokens

When thinking is on, the thought and the answer share one `max_tokens` budget. A small budget runs out inside the thought. With the `qwen3` parser on, all the text then lands in `reasoning` and `content` comes back empty. Without the parser, you get an unclosed `<think>` block.

Qwen's model cards recommend "an output length of 32,768 tokens for most queries." That is far more than most API code sends. These are my own numbers from Qwen 3.6:

- A grading prompt capped at 1,024 tokens cut its answers off with no error. I raised it to 6,144.
- A JSON extraction job capped at 4,096 returned an empty result for every item. At 8,192 it worked.
- Short chat replies ran at 3,072.

Start at 4,096 and raise it when you see cut-offs. Check `finish_reason` on every reply. `"length"` means the model hit `max_tokens`. Treat that as a failure, even when `content` looks fine.

Newer vLLM can also cap the thought itself. Start the server with `--reasoning-parser qwen3` and send `thinking_token_budget`. Once the budget is spent, the docs say "vLLM forces the model to produce `reasoning_end_str`, effectively terminating the reasoning block."

```bash
curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3-8B",
    "messages": [{"role": "user", "content": "9.11 and 9.8, which is greater?"}],
    "max_tokens": 4096,
    "thinking_token_budget": 1024
  }'
```

`thinking_token_budget` is in the v0.20.0 docs and later. It is not in the v0.17.0 docs, the version I ran.

## Verify it worked

Ask a question with thinking off and look at three fields:

```bash
curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3-8B",
    "messages": [{"role": "user", "content": "Name three uses of Redis."}],
    "max_tokens": 1024,
    "chat_template_kwargs": {"enable_thinking": false}
  }' | jq '{
    finish: .choices[0].finish_reason,
    think_tags: ((.choices[0].message.content // "") | test("</?think>")),
    reasoning: .choices[0].message.reasoning
  }'
```

Going by the docs and the chat template, you should see:

```json
{
  "finish": "stop",
  "think_tags": false,
  "reasoning": null
}
```

Then set `enable_thinking` to `true` on a server started with `--reasoning-parser qwen3`. Now `reasoning` should hold text, and `think_tags` should stay `false`.

What a wrong result means:

- `think_tags: true` with thinking off. The flag never reached the template. Log the JSON your client really sends. With the OpenAI client, the field must sit inside `extra_body`.
- `think_tags: true` with thinking on. The server runs without `--reasoning-parser qwen3`.
- `finish: "length"`. Raise `max_tokens`.
- `reasoning: null` with thinking on and the parser set. The server may be older than v0.12.0. Read `.choices[0].message.reasoning_content` instead.

## Trade-offs

Thinking off costs quality on hard tasks. The model card says thinking mode uses "its reasoning abilities to enhance the quality of generated responses." I turned it off for short replies and JSON extraction. I left it on for checks where the reasoning was worth the wait. In my setup, thinking added 1 to 2 seconds before the first token.

A server-wide default hides the setting. The next person who restarts the server may drop the flag. Then every client gets `<think>` blocks back. Send the field with each request, even when the server has a default.

The parser changes the shape of the response. A client that reads only `content` never sees the thinking. The vLLM docs also say tool calling "only parses functions from the `content` field, not from the `reasoning`."

`chat_template_kwargs` is a vLLM field. Other backends spell it differently. The Qwen3.6 card says Alibaba Cloud Model Studio takes a top-level `"enable_thinking": False` instead. Code that talks to more than one backend needs to know which one it is calling.

In thinking mode, Qwen says "DO NOT use greedy decoding, as it can lead to performance degradation and endless repetitions." Their thinking settings are `Temperature=0.6`, `TopP=0.95`, `TopK=20` and `MinP=0`. Change the sampling when you change the mode.
