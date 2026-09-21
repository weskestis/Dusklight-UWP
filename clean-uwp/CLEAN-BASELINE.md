# Clean Dusklight 2.0.1 UWP baseline

This build is intentionally separate from the customized
`TwilightPrincessRandomizer` package line.

## Exact upstream source

- Dusklight: `422d7bb1b6c8d973cccf8b3d0b226a57ac3cc8c7`
- Aurora: `d0933b745abe0eb9815bedcea8047575da18698d`
- Borealis: `0bdba6c50a46409c4862474c72b4a3a631fbe0ec`
- Randomizer: `d0ceae8f18bbef4a40287a72a2791a3c06c9aca5`
- Cosmetics: `fd93491089fa95441789244f2b2fd22a451ecbcc`
- UWP dependency: `6ba4aad18b0f149151784f31fd339225544e24f2`

The Randomizer and Cosmetics submodules remain byte-for-byte at the revisions
pinned by Dusklight. No private Randomizer checkpoint or gameplay patch is
applied.

## Port-only changes

The only source changes are the reviewed Xbox/UWP portability layer:

- Windows Store entry point and process-restart guards
- static UWP feed and final Windows Store package wrapper
- final executable symbol-manifest generation for upstream code mods
- UWP filesystem, controller, graphics, card, and dependency adaptations
- removal of Funchook's desktop-only PSAPI diagnostics from the UWP binary
- isolated package identity `Dusklight2UWP`
- package artwork generated from the official upstream Dusklight icon, logo,
  and prelaunch background
- Store-native, AppContainer-compatible builds of only the three modules
  upstream marks `BUNDLE`: Luau Runtime, Cosmetics, and Randomizer; their
  signed directory bundles load in place from the package with
  `LoadPackagedLibrary`

The build does not apply any private `.634-.660` feature layer. A CI guard
fails if known private-only markers such as Enemy Souls, Boss Souls, or
Octosanity appear.

## Distribution note

This is an unofficial community UWP build and is not affiliated with
TwilitRealm. It contains no Twilight Princess disc image or copyrighted game
data; each user must supply a legally dumped supported disc.
