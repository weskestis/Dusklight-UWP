# Dusklight 2 UWP clean build controls

This branch builds a separate Xbox/UWP x64 app from exact upstream Dusklight
commit `e9b120544cb75e81b5aa36777f1688fa61f2d9e8`.

It applies only the reviewed Dusklight/Aurora UWP compatibility patches. The
upstream Randomizer, Cosmetics, and Luau Runtime modules are kept at the exact
revisions pinned by Dusklight 2.0. None of the private
`TwilightPrincessRandomizer` feature checkpoints are applied.

The package identity is `Dusklight2UWP`, so it installs beside the customized
`TwilightPrincessRandomizer` app with isolated LocalState.

This is an unofficial community UWP port and is not affiliated with
TwilitRealm. Official Dusklight information is at https://twilitrealm.dev/.
No game image or copyrighted game data is included.

See `CLEAN-BASELINE.md` for the exact pins and boundary, and
`INSTALL_XBOX.md` for installation.
