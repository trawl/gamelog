# Changelog

## [2.5.0](https://github.com/trawl/gamelog/compare/v2.4.0...v2.5.0) (2026-11-04)


### Features

* Android support, database import/export and window modes ([ec2793d](https://github.com/trawl/gamelog/commit/ec2793d4bd644762dd773669ff37752b53259342))
* **android:** fix theme, language icons, dismissable popups and glyphs ([c45adb5](https://github.com/trawl/gamelog/commit/c45adb53415fc2e8a02f34bd6a1ce746aaeb1680))
* **android:** guard desktop-only code and add main.py entry ([9f2731e](https://github.com/trawl/gamelog/commit/9f2731e0162ec872e73a95e9e4b101a6d69b6b91))
* **android:** long-press gestures on the player lists ([db61a3f](https://github.com/trawl/gamelog/commit/db61a3f7386b9ce828499ded509e5ce933b7b2d6))
* **android:** working import/export, window mode setting and export naming ([480319a](https://github.com/trawl/gamelog/commit/480319ad11d97f0707c0259b34249cadecc2b30b))
* import and export the whole database ([fdffb29](https://github.com/trawl/gamelog/commit/fdffb297f2b652d7ca37a3a32b12bc563f939b66))
* **ui:** drop the menu bar off macOS and move About into Settings ([fdfa70a](https://github.com/trawl/gamelog/commit/fdfa70ab850a02889e8842c18a2309c1edf6e035))
* **ui:** make full screen the default window mode ([644866d](https://github.com/trawl/gamelog/commit/644866d41597e5e2c9b797ea8b0583d8688de457))
* **ui:** show the quit button on every platform in two rows of three ([8c7e128](https://github.com/trawl/gamelog/commit/8c7e1287e078869a4b00548873575f29c60138c8))
* **ui:** use emoji icons on all platforms and fade them when disabled ([9c46dc2](https://github.com/trawl/gamelog/commit/9c46dc24eeec331b6aed63e5ceff5ba6f95aac3d))
* window mode setting and F11 full screen on every platform ([a63d341](https://github.com/trawl/gamelog/commit/a63d341228f294e2d71e5eba216b4657d481df2f))


### Bug Fixes

* **scrabble:** clear dealer marker when a match finishes ([12d4ec2](https://github.com/trawl/gamelog/commit/12d4ec2b2c6e553a695828342772ee7aa0adbd55))
* **ui:** reserve title space for group boxes on Windows ([3f000c0](https://github.com/trawl/gamelog/commit/3f000c0a467ae93447bf6b27a03729a000d7d377))
* **ui:** reserve title space for group boxes on Windows ([3cc1ad7](https://github.com/trawl/gamelog/commit/3cc1ad720ec54ef8135c5c4c805362b0ef026e68))
* **ui:** stop untitled group boxes reserving title room on Windows ([e59c1a5](https://github.com/trawl/gamelog/commit/e59c1a53f3ba8396f66ed46d3938232e8005d029))


### Documentation

* document Android support and bring the developer notes up to date ([bfcad9a](https://github.com/trawl/gamelog/commit/bfcad9a7e6510e13aa4eb26eb2b140646b90261c))

## [2.4.0](https://github.com/trawl/gamelog/compare/v2.3.0...v2.4.0) (2026-10-30)


### Features

* nemesis and favourite victim tiles, content-sized tables ([2fcd5d8](https://github.com/trawl/gamelog/commit/2fcd5d8dbd69753c4eb4990f82c500d58eee6086))
* per-game player statistics and a richer player stats screen ([0e2da63](https://github.com/trawl/gamelog/commit/0e2da637d839296fe20db02bb30b2251551da387))
* performance index in game statistics ([7ab8bd8](https://github.com/trawl/gamelog/commit/7ab8bd8c9f6ac341b2a83f1f8ecda8c3fe2e40d6))
* player statistics engine ([14228d4](https://github.com/trawl/gamelog/commit/14228d4d99eb09ae9a928733fca21a7fbe0786e0))
* player statistics screen ([2ecb1f5](https://github.com/trawl/gamelog/commit/2ecb1f563aba5a707337e69128285e15056ad3ca))
* player statistics screen and developer notes ([b4c519d](https://github.com/trawl/gamelog/commit/b4c519dbb2a9c888f464bd9c1629c7eefc778f44))


### Bug Fixes

* fit quick statistics headers without squashing or scrolling ([25707ba](https://github.com/trawl/gamelog/commit/25707bababad5a2e275f6ed10690ff2d33a23b1d))
* honour the player list in particular statistics updates ([8ba0b04](https://github.com/trawl/gamelog/commit/8ba0b04ebc403868f9382abe05ab27e42f67d7ef))
* nemesis and favourite victim need a losing or winning record ([beabc07](https://github.com/trawl/gamelog/commit/beabc072df808261261e59036ee4ec897ef8a293))


### Documentation

* add AGENTS.md agent guide ([042d505](https://github.com/trawl/gamelog/commit/042d50523971595f5529fc611389c77c64b82a1d))
* mention player statistics in the README ([ba8c635](https://github.com/trawl/gamelog/commit/ba8c635d23b849ba14aa2df3c458d528c4293155))
* player statistics design ([55de9b9](https://github.com/trawl/gamelog/commit/55de9b9bd7eb7c72e6a1a91a9f21b688ee2d820b))
* replace the player statistics design doc with developer notes ([4f1745e](https://github.com/trawl/gamelog/commit/4f1745e94a6b0700d359596bb398f0382971e041))

## [2.3.0](https://github.com/trawl/gamelog/compare/v2.2.0...v2.3.0) (2026-10-27)


### Features

* History browser plus some small fixes ([#26](https://github.com/trawl/gamelog/issues/26)) ([ba4063f](https://github.com/trawl/gamelog/commit/ba4063f529b01bc69fde62d9cc38851675227cd3))

## [2.2.0](https://github.com/trawl/gamelog/compare/v2.1.1...v2.2.0) (2026-10-13)


### Features

* New games and rules ([#24](https://github.com/trawl/gamelog/issues/24)) ([3f004cb](https://github.com/trawl/gamelog/commit/3f004cb9650fbb6953c5d2cfcf6e31093b4c1c99))

## [2.1.1](https://github.com/trawl/gamelog/compare/v2.1.0...v2.1.1) (2026-09-17)


### Bug Fixes

* missed updating version on the code ([#18](https://github.com/trawl/gamelog/issues/18)) ([763d14e](https://github.com/trawl/gamelog/commit/763d14e540c423bd36856a0ff72b3e2196ccc7f9))
* release-please version fix ([#22](https://github.com/trawl/gamelog/issues/22)) ([f16aaab](https://github.com/trawl/gamelog/commit/f16aaab6b7419ad54b90e2c286a5c08d368d64c5))
* updated release-please config to update _version.py ([#20](https://github.com/trawl/gamelog/issues/20)) ([dd4871e](https://github.com/trawl/gamelog/commit/dd4871e65e38b4d1e268cf69ca530013bf343ad6))

## [2.1.0](https://github.com/trawl/gamelog/compare/v2.0.0...v2.1.0) (2026-09-17)


### Features

* better python packaging ([#16](https://github.com/trawl/gamelog/issues/16)) ([1e86da5](https://github.com/trawl/gamelog/commit/1e86da5f6106528b23393d5f4fdfab577dfd28e3))

## [2.0.0] - 2026-09-16

Initial tracked release. See git history for prior changes.
