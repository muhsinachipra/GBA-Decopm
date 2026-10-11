# Dump Authenticity Verification (P0-05)

Date: 2026-10-11 (Session 002). Resolves open question Q1 from `RESEARCH_AND_PLAN.md` §8.5.

## Method

- Source of truth: No-Intro DAT for "Nintendo - Game Boy Advance".
- Acquired from the `Daily_Rebuild` release of `hugo19941994/auto-datfile-generator` (a daily mirror of official No-Intro data):
  - `https://github.com/hugo19941994/auto-datfile-generator/releases/download/Daily_Rebuild/no-intro.zip`
  - Inner file used: `Nintendo - Game Boy Advance (20260707-143610).dat`
- Local (uncommitted) copies under `work/recon/dat/`.
- Check executed by `tools/recon/rom_recon.py --nointro-dat work/recon/dat/nointro-gba.dat "Road Rash - Jailbreak (USA).gba"`.

## Result: MATCH

No-Intro entry:

```
<rom name="Road Rash - Jailbreak (USA).gba" size="4194304" crc="8834af99" md5="0a4da0bbdad29f2faa5584b49b0a4f5d" sha1="48150529172ff411e3e1bd38b9a74d8b32e5fa59" serial="A9RE"/>
```

Local ROM recomputation agrees exactly: size 4,194,304; CRC32 `8834af99`; MD5 `0a4da0bbdad29f2faa5584b49b0a4f5d`; SHA1 `48150529172ff411e3e1bd38b9a74d8b32e5fa59`; SHA256 `f0af99188e7ffaf0b0ea95e1503365a7eaf2eac6c9bc01c18c0f5c5ed010d4b6`.

## Notes

- The Europe release is a different dump (serial `A9RP`, SHA1 `414eeff87dbc7196c6a8bce60702dee07dd4b006`, CRC32 `f4693458`). Our baseline remains the USA revision; do not mix the two.
- Header byte 0xBE is `0x00` in this dump. Per GBATEK (verified against the local reference copy `work/recon/gbatek.htm`), the GBA header contains:
  - `0xBD`: Complement check ("header checksum, required!") — verified OK here: stored `0x6A` equals recomputed `0x6A`.
  - `0xBE-0xBF`: Reserved area, "should be zero filled" — `0x00` here is expected, not an anomaly.
- Therefore the earlier "unusual zero header checksum" concern in the plan was a mislabel. Authenticity is established by the full-file hash match above; no re-baseline is needed.

## Reproduction

```powershell
python tools\recon\rom_recon.py "Road Rash - Jailbreak (USA).gba" `
  --out docs\recon\rom_recon_report.md `
  --nointro-dat work\recon\dat\nointro-gba.dat
```
