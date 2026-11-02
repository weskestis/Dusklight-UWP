# Twilight Princess / Wind Waker crossover for Xbox UWP

The target is a separate UWP game that connects both worlds, shares selected
progression, and supports importing enemies, player abilities and characters
in both directions. This checkpoint implements the **Wind Waker platform port**.
It does not yet link Twilight Princess or implement crossover combat.

## Source and build

`sources.lock.json` pins WindowWaker, Aurora, the decompilation metadata,
Dolphin DSP source, SDL's UWP source fork and the Xbox UWP runtime depot. `tools/prepare.py` verifies
those revisions, applies the UWP patches, and generates empty asset declarations.
Real game data is read from the user's GZLE01 revision 0 disc at runtime.

The Windows workflow builds the game and SDK with clang-cl, then links them into
a Windows Store wrapper using the UWP SDL/Dawn/nod binaries. The wrapper creates
LocalState paths, checks the supplied disc and offers a controller-operated start
screen. Package checks reject the wrong application identity, non-x64 binaries,
missing application AppContainer flags and desktop imports in our executable.
SDL is built from source for Windows Store and must pass the same import checks
as our executable. Other inherited runtime DLLs must match the pinned depot byte
for byte. Several
of those DLLs lack AppContainer flags or import desktop APIs;
`package-validation.json` records each issue. This is an experimental Dev Mode
package, not Store certification or proof that those DLLs work on Xbox.

The original clean Dusklight build remains on `main`; this project lives on
`codex/tp-ww-crossover-uwp`. Its package identity is `ZeldaCrossoverUWP`.

## Bring-up order

1. Compile and package Wind Waker; validate startup, audio, controller, save/reload
   and room changes on Xbox.
2. Add a separate TP core with isolated symbols/state, then verify a round-trip
   transition with both saves intact.
3. Port one enemy in each direction, including collision, target selection,
   attacks, hit reactions, death, rewards and room-clear behavior.
4. Add player abilities and characters, shared progression and combined seed
   validation. Native, swapped and mixed rosters are the intended modes.

Before a cross-game enemy can be placed by the randomizer, its supported attacks,
defenses, required items, room restrictions and completion effects must be
declared and tested. Bosses and cutscene-dependent actors require dedicated
adapters. A host compilation is not proof of in-game compatibility.

## License provenance

The port preserves the upstream licenses: game decompilation CC0, WindowWaker
and Aurora MIT, and Dolphin DSP code GPL-2.0-or-later. See their pinned source
trees and WindowWaker's `THIRD_PARTY.md`. Any binary distribution must retain
the notices and corresponding source for applicable components. There is no
Nintendo disc image, extracted game executable, audio, model or texture here.
