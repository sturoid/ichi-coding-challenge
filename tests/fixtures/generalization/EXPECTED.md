# Expected verdicts: generalization fixture (hand-derived, independent of the tool)

Building: R-3, Type V-A, NFPA 13R, 3 stories (rooms 1XX/2XX/3XX), 55'-0" tall.
Rules: PLAN section 2. Best case = nominal is clear; hung = half height; slider = half width; fixed = no opening. Pass only on real net-clear data (5.7 sf, 24" h, 20" w, sill <= 44"). Sill = HD HT - NOM. H (no sill column). Grade-floor 5.0 sf is not assumed for Pass; level 1 only. IBC 1030.1 item 2 covers R-3 below the 4th story, so all rooms apply.

## Header mapping notes
- Schedule columns: MK=symbol, OPER.=operation type, ROOM, NOM. SIZE (NOM. W, NOM. H), HD HT.=head height, NET CLR OPNG (IN.) with its own sub-headers W and H (inches, decimal), a header-less column holding screen "Y" (must NOT be read as egress), EERO=egress, GLZG, REMARKS.
- The sub-headers "W" and "H" under NET CLR OPNG are not the nominal size; "NOM. W/NOM. H" are. If the tool cannot tell the two size pairs apart, or cannot map EERO / OPER. / MK, expect dependent findings to become CNE (Pass and Fail items below would then be CNE; the N/A items stay N/A only if EERO and room names are mapped).
- Operation vocabulary: SLDR=slider, D.H.=double hung (hung rule), CSMT=casement, AWN.=awning, FIXED. If D.H. is unmapped, D1 and J1 would become CNE.

## H1 Building height
- H1: Pass. R-3 -> row R; NFPA 13R -> sub-row S13R; V-A column = 60 ft. Height 55'-0" = 55 ft <= 60 ft. Margin 5 ft. (Neighbours: S13D V-A = 50 and NS V-A = 50 would wrongly Fail; S V-A = 70 would match the architect's stated 70'. The architect's 70' allowable is wrong vs the table's 60; flag as a discrepancy, verdict unchanged.)

## Windows
- WA1: Could Not Evaluate (boundary). BR 2 104 is a bedroom, EERO=Y, slider. Sill = 6'-8" - 3'-0" = 80 - 36 = 44.0" exactly at the limit, so any frame loss fails it. Best-case clear: width 60/2 = 30" (>=20), height 36" (>=24), area 30 x 36 = 1080 sq in = 7.5 sf (>=5.7). No net clear data.
- WA2: Not Applicable. Fixed, EERO blank, in a sleeping room (undesignated).
- WB1: Could Not Evaluate. DEN lO2 (OCR for DEN 102) is an ambiguous room; EERO blank. Case 3'-0" x 4'-0", sill 84 - 48 = 36". Reason: possible sleeping room.
- WC1: Not Applicable. KITCHEN 103 is not a sleeping room (EERO=Y there is irrelevant).
- WC2: Not Applicable. LIVING 105.
- WD1: Pass. MSTR BRDM 201 (misspelled master bedroom) EERO=Y, D.H. Net clear W 33.0 x H 28.0 = 924 sq in = 6.42 sf >= 5.7; H 28 >= 24; W 33 >= 20. Sill = 7'-0" - 5'-0" = 84 - 60 = 24" <= 44. Level 2, so 5.7 applies.
- WD2: Could Not Evaluate (open). Same room, EERO=Y, slider 6'-0" x 4'-0". Best case clear 36 x 48 = 1728 sq in = 12 sf; sill 84 - 48 = 36" <= 44. Does not fail, but no net clear data, so cannot Pass.
- WE1: Could Not Evaluate. "NURS ERY 202" (OCR split) is ambiguous (nursery may be a sleeping room); EERO blank. Casement 2'-6" x 3'-0".
- WF1: Fail. BR 3 203, EERO=Y, casement 2'-O" (read 2'-0") x 2'-6": best case 24 x 30 = 720 sq in = 5.0 sf < 5.7 (level 2, so the 5.0 grade-floor allowance does not apply). Sill = 80 - 30 = 50" > 44 also fails.
- WG1: Not Applicable. BATH 204.
- WM1: Fail. BR 4 205, EERO=Y, casement 2'-6" x 3'-6" nominal 30 x 42 = 8.75 sf passes, sill 84 - 42 = 42" OK, but real net clear 24.0 x 31.5 = 756 sq in = 5.25 sf < 5.7 (level 2). Nominal passing does not matter once net clear data exists.
- WM2: Fail. Same room, FIXED with EERO=Y: does not open, no net clear opening (1030.1.1/1030.2.1).
- WJ1: Could Not Evaluate (boundary). LOFT 301 (ambiguous room) EERO=Y, D.H. 3'-0" x 4'-0". Best-case clear height = 48/2 = 24.0" exactly at the 24" minimum; area 36 x 24 = 864 sq in = 6.0 sf; sill 80 - 48 = 32". Boundary and ambiguous room, so CNE either way.
- WK1: Pass. BR 5 302, EERO=Y, casement. Net clear 28.0 x 41.0 = 1148 sq in = 7.97 sf >= 5.7; H 41 >= 24; W 28 >= 20; sill = 80 - 48 = 32" <= 44. Level 3.
- WL1: Not Applicable. BATH 303.
- WN1: Not Applicable. BR 6 304 is a bedroom but this window is not designated (EERO blank; the header-less screen column holds Y and must be ignored).

## Rooms (sleeping or possibly sleeping)
- R104 (BR 2): Could Not Evaluate. Only designated window WA1 is CNE (boundary). Room number is 104; the "2" is part of "BR 2".
- R102 (DEN, "lO2"): Could Not Evaluate. Ambiguous room name; no designated window.
- R201 (MSTR BRDM): Pass. WD1 passes (any designated window passing suffices); WD2 CNE does not change it.
- R202 (NURSERY): Could Not Evaluate. Ambiguous name; no designated window.
- R203 (BR 3): Fail. Only designated window WF1 Fails.
- R205 (BR 4): Fail. Both designated windows fail: WM1 (5.25 sf) and WM2 (fixed).
- R301 (LOFT): Could Not Evaluate. Ambiguous name; WJ1 is boundary CNE.
- R302 (BR 5): Pass. WK1 passes.
- R304 (BR 6): Could Not Evaluate. Bedroom with no designated window (only WN1, undesignated), also contradicts "EERO provided at all sleeping rooms".

## Debatable
- NURSERY (R202/WE1) treated as ambiguous, not as a bedroom. An undesignated window in an ambiguous room is CNE (as the original Office 102), not N/A.
- WJ1: designated window in an ambiguous room; expected CNE because of the boundary regardless.
- R104/R102 depend on correctly parsing "BR 2 104" and "DEN lO2" (OCR l/O) to numbers 104 and 102.
- Header-less screen column must not become the egress column.

## Review changes (after the first run)
- **WB1, WE1: Could Not Evaluate -> Not Applicable.** Opus's call, against Sonnet's original expectation above. An undesignated window isn't checked as an escape opening; whether DEN 102 / NURSERY 202 is a sleeping room is a question about the room, so it's raised once, on R102 / R202 (both Could Not Evaluate). Same rule as window 4 / Office 102 in the README fixtures. In PLAN Rev 7 window 4 was listed as CNE; that was changed during the build for the same reason.
- **NURSERY:** the tool treats it as a sleeping room (a nursery is a room someone sleeps in), not as an ambiguous name. R202 is Could Not Evaluate either way (no window designated), with reason `NO_EERO_DESIGNATED` rather than `AMBIGUOUS_SLEEPING_ROOM`.
