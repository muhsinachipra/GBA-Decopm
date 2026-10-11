# ROM Recon Report

- ROM: `Road Rash - Jailbreak (USA).gba`
- Size: 4194304 bytes

## Hashes

| Algorithm | Value |
|---|---|
| crc32 | `8834af99` |
| md5 | `0a4da0bbdad29f2faa5584b49b0a4f5d` |
| sha1 | `48150529172ff411e3e1bd38b9a74d8b32e5fa59` |
| sha256 | `f0af99188e7ffaf0b0ea95e1503365a7eaf2eac6c9bc01c18c0f5c5ed010d4b6` |

## Header

| Field | Value |
|---|---|
| title | `ROADRASHJAIL` |
| game_code | `A9RE` |
| maker_code | `20` |
| version | `0x00` |
| entry_word | `0xEA000030` |
| entry_target | `0x000000C8` |
| fixed_b2 | `0x96` |
| fixed_b2_ok | `0x01` |
| complement_stored | `0x6A` |
| complement_calc | `0x6A` |
| complement_ok | `0x01` |
| reserved_be | `0x0000` |
| logo_sha1 | `17daa0fec02fc33c0f6abb549a8b80b6613b48ee` |

## No-Intro cross-check

MATCH. SHA1 found in provided DAT:

- `<rom name="Road Rash - Jailbreak (USA).gba" size="4194304" crc="8834af99" md5="0a4da0bbdad29f2faa5584b49b0a4f5d" sha1="48150529172ff411e3e1bd38b9a74d8b32e5fa59" serial="A9RE"/>`

## Entropy map (Shannon entropy per block, bits/byte)

| Offset | Entropy |
|---|---|
| 0x000000 | 7.971 ################################ |
| 0x010000 | 7.981 ################################ |
| 0x020000 | 7.955 ################################ |
| 0x030000 | 7.953 ################################ |
| 0x040000 | 7.960 ################################ |
| 0x050000 | 7.818 ############################### |
| 0x060000 | 7.946 ################################ |
| 0x070000 | 7.918 ################################ |
| 0x080000 | 7.915 ################################ |
| 0x090000 | 7.925 ################################ |
| 0x0A0000 | 7.844 ############################### |
| 0x0B0000 | 7.832 ############################### |
| 0x0C0000 | 7.908 ################################ |
| 0x0D0000 | 7.885 ################################ |
| 0x0E0000 | 7.880 ################################ |
| 0x0F0000 | 7.930 ################################ |
| 0x100000 | 6.341 ######################### |
| 0x110000 | 6.000 ######################## |
| 0x120000 | 5.909 ######################## |
| 0x130000 | 5.671 ####################### |
| 0x140000 | 5.895 ######################## |
| 0x150000 | 5.795 ####################### |
| 0x160000 | 5.933 ######################## |
| 0x170000 | 5.515 ###################### |
| 0x180000 | 5.376 ###################### |
| 0x190000 | 5.583 ###################### |
| 0x1A0000 | 5.698 ####################### |
| 0x1B0000 | 5.978 ######################## |
| 0x1C0000 | 5.685 ####################### |
| 0x1D0000 | 5.884 ######################## |
| 0x1E0000 | 6.281 ######################### |
| 0x1F0000 | 6.183 ######################### |
| 0x200000 | 5.815 ####################### |
| 0x210000 | 6.573 ########################## |
| 0x220000 | 6.570 ########################## |
| 0x230000 | 6.756 ########################### |
| 0x240000 | 6.207 ######################### |
| 0x250000 | 6.172 ######################### |
| 0x260000 | 5.970 ######################## |
| 0x270000 | 6.134 ######################### |
| 0x280000 | 5.715 ####################### |
| 0x290000 | 5.799 ####################### |
| 0x2A0000 | 6.078 ######################## |
| 0x2B0000 | 5.842 ####################### |
| 0x2C0000 | 6.218 ######################### |
| 0x2D0000 | 5.512 ###################### |
| 0x2E0000 | 6.538 ########################## |
| 0x2F0000 | 7.974 ################################ |
| 0x300000 | 7.329 ############################# |
| 0x310000 | 6.837 ########################### |
| 0x320000 | 7.134 ############################# |
| 0x330000 | 7.150 ############################# |
| 0x340000 | 7.121 ############################ |
| 0x350000 | 6.906 ############################ |
| 0x360000 | 7.652 ############################### |
| 0x370000 | 7.210 ############################# |
| 0x380000 | 6.857 ########################### |
| 0x390000 | 6.217 ######################### |
| 0x3A0000 | 6.095 ######################## |
| 0x3B0000 | 6.463 ########################## |
| 0x3C0000 | 7.387 ############################## |
| 0x3D0000 | 7.446 ############################## |
| 0x3E0000 | 6.588 ########################## |
| 0x3F0000 | 4.179 ################# |

## Byte census

- 0x00: 412235 (9.8%)
- 0xFF: 68086 (1.6%)

## Instruction-pattern census (heuristic)

| Pattern | Count |
|---|---|
| thumb_push_lr | 4478 |
| thumb_sub_sp | 2939 |
| arm_stmfd_sp_lr | 13 |
| arm_b_bl_words | 28912 |

## String harvest

- ASCII strings (min 4 chars): 70288
- Strong-keyword hits: 21
- Content-keyword hits: 5

### Strong keyword hits

- 0x0000A0 [roadrash] `ROADRASHJAILA9RE20`
- 0x019B48 [gax] `rogaxgxh`
- 0x31E2F4 [road rash] `Road Rash`
- 0x31E352 [magicpockets] `<C> WWW;MAGICPOCKETS;COM`
- 0x3AA51A [gax] `zmc`wzvimxyncZRdbb^_ghhaWFS\[WKV^b\TFJWXUGNX__UICU[\MHP[^URIV]ZUKU\aYUKP^^`SW\a_^`PV]glXZclkcVMfimc\nqpee^ZbbnegnonhfX[bhiZdjqoe\K]cg]Ufikf^UOZ\`XZcfe`bRMU\j[X_`
- 0x3ED134 [gax] `GAX Sound Engine 3.03A (Mar  5 2003) `
- 0x3ED280 [gax] `GAX2_INIT`
- 0x3ED29C [gax] `GAX2_NEW`
- 0x3ED2BC [gax] `GAX2_NEW_FX`
- 0x3ED2E0 [gax] `WHEN USING DIFFERENT FX_MIXING_RATE, FLAG GAX_FX_REVERB AND GAX_HALFRATE_FX ARE NOT ALLOWED.`
- 0x3ED340 [gax] `GAX2_JINGLE`
- 0x3ED34C [gax] `GAX_NO_JINGLE FLAG IS SET`
- 0x3ED368 [gax] `GAX_IRQ`
- 0x3ED370 [gax] `GAX_PLAY HAS NOT FINISHED BEFORE GAX_IRQ. USE LOWER MIXING RATE OR LESS FX CHANNELS OR PUT GAX_PLAY IN VBLANK IRQ.`
- 0x3ED3E4 [gax] `GAX_FX`
- 0x3ED3EC [gax] `YOU TRIED TO PLAY A SPEECH FX BUT HAVE NOT USED THE GAX_SPEECH FLAG WITH GAX2_INIT.`
- 0x3ED440 [gax] `GAX2_FX`
- 0x3ED448 [gax] `FXPARAMS->FXID IS GAX_DEFAULT`
- 0x3ED468 [gax] `GAX_RESTORE_FX`
- 0x3ED5A4 [gax] `GAX ENGINE V3.03A Mar  5 2003`
- 0x3EE0B8 [magicpockets] `* Engine by www.MagicPockets.com* Engine by www.MagicPockets.com* Engine by www.MagicPockets.com* Engine by www.MagicPockets.com* Engine by www.MagicPockets.com`

### Content keyword hits

- 0x01F7D0 [pacific highway] `WILDCOP PATRTIME TKSURVIVAMUL-PLAYERPPacific Highwayuburban DumpRaiForestIcellshCitBikers'RideradisBehFlood Tckne VaeEDASSWORNew ct ar!EY  HAExntsrviv mUnPlatin`
- 0x024D75 [surviv] `WILDES BULLSTIFEZTATCKSURVIVALMTIPLAYERPSPazifik-HighwayVort-M`
- 0x024DC6 [cop] `lDie CitBer-FreahradsstnHoceckT rednsGPRTKWONeuFur!.ICHTSWErwtn vntSvivodusAllfscPlatin-KnwtdnnLelpcopWazimmpl12BeAuw`
- 0x025B15 [pacific highway] ` OCORITRUCCHPacific HighwayobboriFesta tropaleoMeolGi berSagg dsognPc latVeei RedneckBLSSWDilotivo!. FACIDIFC.Tsmit e`
- 0x35A76F [cop] `nTCOPQ@37Lp`

