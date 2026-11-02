---
title: "Translating Volkov Commander from 8086 Assembly into Native C and WebAssembly"
date: 2026-11-02
draft: false
tags: [dos, c, webassembly, assembly, preservation, volkov-commander]
summary: "Old DOS software usually survives inside an emulator. With vc-linux, I translated Volkov Commander and other classic DOS programs from 8086 instructions into C ahead of time, checked every instruction against a CPU emulator, and compiled the result to native Linux and WebAssembly."
---

Old DOS software usually survives one way: inside an emulator. DOSBox and the Internet Archive's browser players keep a pretend 8086 running and interpret the original instructions at run time, forever. That works, but it never stops being a simulation of 1990s hardware.

I wanted to try something different. Translate the program once, ahead of time, into C, and let today's compilers and today's CPUs run it directly. No pretend CPU at run time. That is the idea behind [vc-linux](https://github.com/evoleinik/vc-linux), and you can run the result in a browser at [notanemulator.com](https://notanemulator.com/).

## Volkov Commander finally has open source to translate from

Volkov Commander is a DOS file manager from 1992, a Norton Commander clone written in 8086 assembly by Vsevolod V. Volkov, a student at Kyiv Polytechnic at the time. It first appeared in the Softpanorama Bulletin that December. It was popular for years across the former Soviet Union because it was small, fast, and handled Cyrillic filenames better than most of the competition.

For most of its life the source was not public. That changed in 2026, when the author released it under BSD-2. Danila Sukharev had already done the harder, less visible work of preserving the original sources and getting them to build again with JWasm, a modern assembler that understands the old syntax, at [github.com/ddanila/vc](https://github.com/ddanila/vc).

vc-linux starts from that work. Without it, there is no source to translate from.

## Keeping the source, the build, and the C side by side makes it preservation

For every program, vc-linux keeps three things, not one:

- the original source, unedited
- a reproducible build of that source
- a machine translation of the same program into C

The translation is never hand edited. If something is wrong, the fix goes into the translator, and the C is regenerated. That rule matters for preservation. It means the C is always a direct, mechanical function of the original bytes, not a rewrite that drifts further from the original every time someone touches it.

This is also why vc-linux is not a rewrite in the way Midnight Commander or far2l are rewrites. Those are new programs inspired by the old one. vc-linux is the old program's own instructions, carried across to a form a modern compiler can read. Each release of the project is archived on Zenodo with a DOI at [https://doi.org/10.5281/zenodo.23085585](https://doi.org/10.5281/zenodo.23085585).

## Every instruction is checked against a CPU emulator from 32 random states

The translator does not try to guess where instructions start and end by staring at raw bytes. x86 code is variable length, and old DOS binaries mix code and data in ways that make guessing unreliable.

Instead, instruction boundaries come from the assembler listing, the file JWasm produces when it assembles the source, which lines up every instruction with its address and its encoded bytes. The actual bytes used for translation come from the linked binary, so anything the linker resolved at link time is already in place.

Each translated instruction is checked, not assumed correct. For every distinct instruction found in the binary, the project runs the original bytes on the unicorn CPU emulator from 32 random starting states, runs the translated C from the same 32 states, and compares the results. If they ever disagree, the translation is wrong and gets fixed before anything else happens.

Only the CPU-level instructions are handled this way. DOS itself, the BIOS, the screen, the keyboard, the mouse, CGA graphics, and the PC speaker are reimplemented by hand, in C, around the translated code. That split is deliberate. Instructions get mechanical, checked translation. The machine around them gets a normal, hand-written implementation, the same way an emulator's device layer is hand-written even when its CPU core is not.

## Real DOS programs copy their own code and rely on odd DOS errors

Real DOS programs do things a clean instruction-set reference does not prepare you for.

First, part of Volkov Commander's own code is the literal text "RESIDENT". The bytes of that text double as valid 8086 instructions, and VC copies that block of its own code to a different address in memory and keeps running it from there. The translator cannot pin that code to one fixed address ahead of time. It finds the moved block by matching its bytes and the offset it was copied by, wherever it ends up.

Second, some DOS calls report errors without the carry flag. Set Date is one: real DOS returns AL=FFh for a date that cannot exist and leaves the carry flag alone. VC relies on that to detect DESQview, a DOS multitasking shell. It asks DOS to set the date to year 'DE', month and day 'SQ', then adds one to AX. Plain DOS answers FFh, which becomes zero. DESQview catches that exact call and answers with its version number, which does not. Our first DOS reported the error the modern way, through the carry flag, so VC concluded it was running under DESQview (`VCOVL.ASM`, `DetectDesqView`).

Neither trick is exotic by DOS standards. They are the kind of thing any translator of real, shipped DOS software eventually runs into, and any claim of correctness has to survive them.

## One body of C compiles to native Linux and WebAssembly

The payoff of doing the translation once is that the resulting C compiles anywhere a C compiler exists.

`gcc` turns it into a native Linux program, a static binary of about 23 MB that manages real files on a real filesystem. That includes long names and Cyrillic names, shown in code page 866, the encoding DOS used for Cyrillic, because that is still what Volkov Commander expects to draw.

The same C, compiled with Emscripten, becomes WebAssembly. The browser then compiles that WASM to native code for whatever CPU it is actually running on. At [notanemulator.com](https://notanemulator.com/), the page downloads 0.93 MB before its first screen, and fetches each other program the first time you run it. On a phone, the page shows the screen edge to edge with an on-screen keyboard that has the F-keys.

No part of this involves fetching an 8086 emulator and interpreting opcodes in a loop. The CPU work already happened, once, when the C was written.

## Launching other programs still matches on file bytes, not filenames

Volkov Commander is a file manager, and part of what it does is launch other programs. In the browser build, it still does this the DOS way.

Press Enter on a `.BAS` file and VC looks it up in its own extension file, which has an entry like `bas: gwbasic !.!`. That tells VC to run GWBASIC, found on the DOS PATH, with the original filename passed through. The real DOS EXEC call loads the real file, and the runtime matches those bytes against the translations it has on hand and runs the one that fits.

A renamed copy of the same file still runs correctly, because the match is on bytes, not on filename. A changed byte in the file gets a DOS error, the same error real DOS would have given, because nothing in the translation table matches it anymore.

## What runs today on Linux and in the browser

Each program now has its own page on the site, and its Play link starts that program directly. For example, [https://notanemulator.com/rogue/](https://notanemulator.com/rogue/) starts Rogue right away. Here is what works today on both Linux and the web:

| Program | Version / Year | Licence | Build and runtime notes |
|---------|----------------|---------|-------------------------|
| Volkov Commander | 4.99.09 and 4.05 (June 2000) | BSD-2 | JWasm builds 4.05 byte for byte identical to the original TASM 4.1 build, confirming the source really is the program. |
| Microsoft GW-BASIC | 1983 | MIT | Uses the OEM layer from TK Chia's fork. Runs twelve of David Ahl's public-domain BASIC Computer Games, including Super Star Trek and Hammurabi. |
| MS-DOS 2.0 COMMAND.COM, EDLIN, DEBUG, FIND, MORE, SORT, FC | 1983 | MIT | VC's browser command line runs through COMMAND.COM. The published source is a later OEM tree than the shipped 2.0 binaries, and the project records every difference. |
| VZ Editor | 1.6 | BSD-3 | Built byte-identical to the shipped VZUS.COM and wired up as VC's F4 editor. |
| Rogue and Hack | Rogue 5.4.4, Hack 1.0.3 | BSD-3 | Compiled from C with OpenWatcom into DOS executables, then translated from those binaries. |
| bootLogo, a 512-byte Logo | 2024 | BSD-2 | Written by Oscar Toledo G. Renders CGA graphics on a canvas in the browser and in Unicode braille in a terminal. |
| MS-DOS Kermit | 3.15 | BSD-3 (since 2011) | Includes a virtual Hayes modem: `ATDT 555-1992` dials a real BBS over a WebSocket in the browser or TCP on Linux. |

The same translated programs also run as doors on that BBS for anonymous callers, with each session confined by Landlock and seccomp. In the browser, a Source button shows the original 1991 assembly line the CPU is running, complete with Volkov's comments.

## Static recompilation is not a new idea, and it has clear limits

Static recompilation of old binaries is not new. Projects like OpenDUNE and masm2c, along with other DOS recompilation efforts, have done versions of this before. What I think is worth doing differently here is treating it as preservation first: the original source sits right next to the translation, unedited and buildable on its own, and the translation is checked, instruction by instruction, against the real CPU semantics rather than hand-ported and hoped correct.

The approach has strict limits:

- It only runs programs that have already been translated ahead of time.
- There is no fallback interpreter for anything untranslated.
- The screen is fixed at 80x25.
- For now, only 16-bit real-mode programs are supported.

vc-linux was built with Claude Code and OpenAI Codex.

## What I take away from building it

- Emulation keeps running a pretend CPU forever. Static recompilation runs the translation once and compiles it for whatever CPU exists today.
- Keeping the original source, a reproducible build, and the translation side by side, while never hand-editing the translated output, is what makes the translation trustworthy as preservation and not just a port.
- Differential testing against a real CPU emulator, instruction by instruction, from 32 random starting states, lets you claim a translation is correct instead of just hoping it is.
- The approach is not new. Applying it carefully to one specific, well-loved program, with the history and the source kept visible, is the point.

Links:

- Repository: [github.com/evoleinik/vc-linux](https://github.com/evoleinik/vc-linux)
- Original VC source preservation: [github.com/ddanila/vc](https://github.com/ddanila/vc)
- Live site: [notanemulator.com](https://notanemulator.com/) (and direct program pages like [notanemulator.com/rogue/](https://notanemulator.com/rogue/))
- Zenodo archive: [doi.org/10.5281/zenodo.23085585](https://doi.org/10.5281/zenodo.23085585)
