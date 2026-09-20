# Dusklight 2 UWP — Xbox installation

This is an unofficial community UWP port of Dusklight 2. It is not an official
TwilitRealm release. The official Dusklight site is https://twilitrealm.dev/.

The package identity is `Dusklight2UWP`. It installs separately from
`TwilightPrincessRandomizer`, so it will not replace that app or use its
LocalState, saves, configuration, mods, or textures.

1. Put the Xbox in Developer Mode.
2. Trust `Dusklight2UWP.cer` on the PC used for deployment.
3. In Xbox Device Portal, deploy `Dusklight2UWP_2.0.0.0_x64.msix` together
   with the included x64 Microsoft VCLibs dependency.
4. Launch Dusklight 2 UWP and select a supported Twilight Princess disc image
   dumped from a copy you own.

The package contains no game image or copyrighted game data. It includes only
the three modules bundled by the exact upstream Dusklight 2.0 source:
Luau Runtime, Cosmetics, and Randomizer. It does not contain the private
`.634-.660` feature patches.

Future packages using the same `Dusklight2UWP` identity may be installed over
this app to preserve this clean app's own LocalState. The included certificate
is self-signed for Developer Mode sideloading and is not a Microsoft Store
certificate.
