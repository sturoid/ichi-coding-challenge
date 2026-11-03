# Plan review: building height and escape windows

**Project:** NEW 3-STORY SINGLE-FAMILY DWELLING WITH ATTACHED ACCESSORY DWELLING UNIT (ADU). SLEEPING ROOMS ON ALL FLOORS  
**Code:** 2018 INTERNATIONAL BUILDING CODE (IBC) AS ADOPTED BY THE CITY OF MERIDIAN FALLS  
**Checks:** building height (IBC 2018 Table 504.3) and emergency escape and rescue openings (EEROs) in sleeping rooms (IBC 2018 Section 1030)  
**Inputs:** `instructions/fixtures/project/code-analysis.html` (sha256 a0dc18fc9c36); `instructions/fixtures/project/window-schedule.html` (sha256 85de501d0b3c); `instructions/fixtures/code/table-504.3.html` (sha256 2c08579613a6)

| | Pass | Fail | Could Not Evaluate | Not Applicable |
|---|---|---|---|---|
| Building | 0 | 1 | 0 | 0 |
| Rooms | 0 | 2 | 5 | 0 |
| Windows | 0 | 3 | 4 | 10 |

### How to read this

- **Fail** means the item fails even under the most favorable reading of the drawings (no frame loss, the most generous head-height datum). **Pass** needs real clear-opening data, so **no window can Pass from this schedule**: it gives nominal unit sizes, not net clear openings.
- **Could Not Evaluate** means the documents don't settle it. Each one says why, by how much, and what would settle it. The 2 rooms whose escape window is exactly at a limit in the best case, so any real frame makes it fail, are listed with the Fails as **likely Fail — confirm**.
- Every finding cites the code section and shows what was read from which cell. Anything the tool corrected (OCR) or couldn't read is under [Needs your eyes](#2-needs-your-eyes).

## 1. Fails and likely Fails

**Before issuing any room comment:** Exception 2 to 1030.1: no EERO is needed if the room has an exit door opening directly to a public way, yard or court. Not visible in these documents; verify on the floor plan before issuing.

| Item | Verdict | Code | Problem | What settles it |
|---|---|---|---|---|
| Building height | **Fail** | IBC 2018 Table 504.3, row 'R' / sub-row S13D / column Type V-B | The building is 41' - 6" (41.5 ft); Table 504.3 allows 40 ft, so it's over by 1'-6" (18 in). | — |
| **ADU BEDROOM 107** (window 7) | **Could Not Evaluate** (likely Fail — confirm) | IBC 1030.1, 1030.2, 1030.2.1, 1030.3 | Window 7: at the limit even with no frame loss (sill: 0 in to spare; area: needs 76% of nominal as net clear) | manufacturer data or a detail for type F: net clear width/height and the sill-to-clear-opening offset |
| **BEDROOM 203** (window 10) | **Fail** | IBC 1030.1, 1030.2, 1030.3 | Window 10: Area 5.00 sf < 5.7 sf even with no frame loss (1030.2); sill 50 in > 44 in max, 6 in over before any frame (1030.3). | — |
| **BEDROOM 205** (windows 12, 13) | **Could Not Evaluate** (likely Fail — confirm) | IBC 1030.1, 1030.2, 1030.2.1, 1030.3 | Window 12: at the limit even with no frame loss (clear height: 0 in to spare; area: needs 95% of nominal as net clear)<br>Window 13: Fixed window: it doesn't open, so it provides no clear opening under normal operation. | manufacturer data or a detail for type J: net clear width/height and the sill-to-clear-opening offset |
| **BEDROOM 301** (window 20) | **Fail** | IBC 1030.1, 1030.3 | Window 20: Sill 60 in > 44 in max, 16 in over before any frame (1030.3). | — |

**Draft comments for the correction letter** (corrections for Fails, information requests for likely Fails; edit before issuing):

1. Building height of 41' - 6" exceeds the 40 ft maximum in IBC Table 504.3 for Group R-3 (R row), S13D sprinkler sub-row, Type V-B construction. Reduce the building height, or revise the construction type or sprinkler system and update the code analysis. For reference, Table 504.3 allows 60 ft with an NFPA 13 system (IBC 903.3.1.1) or an NFPA 13R system (IBC 903.3.1.2) in this row and column. Correct the allowable height on the code analysis: it states 60' - 0"; Table 504.3 gives 40 ft.
2. Window 7 (ADU BEDROOM 107): provide manufacturer data for window type F showing the net clear opening width and height and the height of the bottom of the clear opening above the finished floor, to verify IBC 1030.2, 1030.2.1 and 1030.3.
3. BEDROOM 203 has no compliant emergency escape and rescue opening: window 10: area 5.00 sf < 5.7 sf even with no frame loss (1030.2); sill 50 in > 44 in max, 6 in over before any frame (1030.3). Provide a compliant opening per IBC 1030.
4. Window 12 (BEDROOM 205): provide manufacturer data for window type J showing the net clear opening width and height and the height of the bottom of the clear opening above the finished floor, to verify IBC 1030.2, 1030.2.1 and 1030.3.
5. Window 13 (BEDROOM 205), the designated emergency escape and rescue opening, does not comply: fixed unit, does not open, so normal operation gives no clear opening (1030.2.1). Provide a compliant opening per IBC 1030.
6. BEDROOM 301 has no compliant emergency escape and rescue opening: window 20: sill 60 in > 44 in max, 16 in over before any frame (1030.3). Provide a compliant opening per IBC 1030.

## 2. Needs your eyes

- Window symbols 9, 15, 16, 17, 18, 19 are missing from the schedule. Rows dropped, or windows deleted? Confirm on the window schedule sheet.

**Text the tool read differently from what's printed** (check these against the drawing):

| Where | Printed | Read as | Why |
|---|---|---|---|
| window schedule, symbol 4, WIDTH | `3' - O"` | `3' - 0"` | letter O in a dimension read as zero |
| window schedule, symbol 12, LOCATION | `BEDRROM 205` | `BEDROOM 205` | 'BEDRROM' read as BEDROOM (one-letter OCR difference) |

## 3. Open questions

Could Not Evaluate items that aren't at a limit. Each needs a fact from the architect or a call from you; the draft information requests below ask the architect for what's missing.

| Item | Why it's open | What settles it |
|---|---|---|
| **BEDROOM 101** | No designated window is shown to comply: window 1 needs net clear data; window 3 needs net clear data. | manufacturer net clear opening (width, height) for window type A, or a net-clear column on the schedule |
| **GUEST BED 303** | Sleeping room with no window marked EGRESS. Possible: window 21 (L.H. CASM'T) could comply in the best case. The code analysis says EEROs are 'PROVIDED AT ALL SLEEPING ROOMS PER IBC 1030. SEE WINDOW SCHEDULE, SHEET A6.1'. | the architect designating an escape window (and its net clear data)<br>Ask the architect to designate an escape window (window 21 is a candidate) and give its net clear opening. If none is designated, the room doesn't meet 1030.1. |
| **OFFICE 102** | 'OFFICE' isn't named as a bedroom, but 'OFFICE' rooms are sometimes slept in. If it's a sleeping room it needs an EERO; designated: none; possible: window 4 (L.H. CASM'T) could comply in the best case. | the floor plan / the architect's intended use of the room<br>Decide whether OFFICE 102 is a sleeping room. |

**Draft information requests:**

1. Windows 1 and 3 (BEDROOM 101): provide manufacturer data for window type A showing the net clear opening width and height and the height of the bottom of the clear opening above the finished floor, to verify IBC 1030.2, 1030.2.1 and 1030.3.
2. GUEST BED 303: no emergency escape and rescue opening is designated on the window schedule. Designate a compliant opening per IBC 1030 and provide its net clear dimensions.
3. Clarify the use of OFFICE 102. If it is a sleeping room, designate a compliant emergency escape and rescue opening per IBC 1030.
4. The window schedule skips symbols 9, 15–19. Provide the complete schedule, or confirm these windows were deleted, and identify any that serve a sleeping room.

## 4. Check 1: building height

- **Verdict:** **Fail**
- **Code:** IBC 2018 Table 504.3, row 'R' / sub-row S13D / column Type V-B
- **Why:** The building is 41' - 6" (41.5 ft); Table 504.3 allows 40 ft, so it's over by 1'-6" (18 in).
- **Margin:** 1'-6" (18 in) over
- **Note:** The code analysis says the allowable height is 60' - 0" per Table 504.3, but the table gives 40 ft for this building (row 'R' / sub-row S13D / column Type V-B). 60 ft is the S and S13R value in the same column, not S13D.
- **Read from the documents:**
  - Occupancy: `R-3` → row 'R' *(code analysis, 'OCCUPANCY GROUP')*
  - Construction type: `V-B` → Type V-B *(code analysis, 'CONSTRUCTION TYPE')*
  - Sprinklers: `YES - AUTOMATIC SPRINKLER SYSTEM THROUGHOUT PER NFPA 13D (IBC 903.3.1.3)` → sub-row S13D *(code analysis, 'FIRE SPRINKLE RS')*
  - Building height: `41' - 6" (TO AVG. HT. OF HIGHEST ROOF SURFACE)` → 41.5 ft *(code analysis, 'BUILDING HEIGHT ABOVE GRADE PLAN E')*
  - Table 504.3 cell: `40` → 40 ft *(table-504.3.html, row 'R' / sub-row S13D / column Type V-B)*
  - Architect's stated allowable: `60' - 0" PER TABLE 504.3` → 60 ft *(code analysis, 'ALLOWABLE HEIGHT')*
- **Worked out:**
  - Occupancy R-3 -> 'R-3' falls under row 'R'.
  - Construction V-B -> column TYPE V / B.
  - Sprinklers: NFPA 13D and Section 903.3.1.3 -> S13D per the Table 504.3 legend.
  - Lookup R > S13D > Type V-B = 40.
  - 41.5 ft > 40 ft.
- **Assumptions:**
  - The building height is the architect's stated value; the grade-plane calculation it depends on (civil sheet) wasn't provided.

Table 504.3, row `R` as parsed (the cell used is in bold):

| Sub-row | I-A | I-B | II-A | II-B | III-A | III-B | IV-HT | V-A | V-B |
|---|---|---|---|---|---|---|---|---|---|
| NS | UL | 160 | 65 | 55 | 65 | 55 | 65 | 50 | 40 |
| S | UL | 180 | 85 | 75 | 85 | 75 | 85 | 70 | 60 |
| S13R | 60 | 60 | 60 | 60 | 60 | 60 | 60 | 60 | 60 |
| **S13D** | 60 | 60 | 60 | 60 | 60 | 60 | 60 | 50 | **40** |

## 5. Check 2: escape windows, by room

How every window below was worked out:

- Sill height is head height minus nominal height (the schedule has no sill column).
- Clear openings are upper bounds: nominal size times the share of the unit that opens (casement and awning 1, hung ½ height, slider ½ width, fixed 0).
- Best case: no frame or sash loss, so the real clear opening is smaller than this.
- Head height is taken as the top of the unit, the usual schedule convention. If it's measured to the clear opening instead, the real sill is higher; any Pass here relies on this convention.
- First floor: may be a grade-floor opening (5.0 sf). Finished grade at each window isn't given, so Pass needs 5.7 sf; a Fail on area is only called below 5.0 sf.

### ADU BEDROOM 107: **Could Not Evaluate** (likely Fail — confirm)

No designated window is shown to comply: window 7 is at the limit. Settled by: manufacturer data or a detail for type F: net clear width/height and the sill-to-clear-opening offset. *(IBC 1030.1, 1030.2, 1030.2.1, 1030.3)*

#### Window 7: **Could Not Evaluate** (likely Fail — confirm)

- **Verdict:** **Could Not Evaluate** (likely Fail — confirm)
- **Code:** IBC 1030.2, IBC 1030.2.1, IBC 1030.3
- **Why:** At the limit even in the best case: sill: best case exactly 44 in, so any frame loss puts the opening above 44 in (1030.3). Also open: area: best case 7.50 sf vs 5.7 sf required, so net clear must be at least 76% of it; clear height: best case 36 in vs 24 in minimum (12 in to spare before frame loss); clear width: best case 30 in vs 20 in minimum (10 in to spare before frame loss).
- **Margin:** sill: 0 in to spare; area: needs 76% of nominal as net clear
- *Reason code: `SILL_AT_LIMIT`*
- **Settled by:** manufacturer data or a detail for type F: net clear width/height and the sill-to-clear-opening offset
- **Read from the documents:**
  - Location: `ADU BEDROOM 107` → ADU BEDROOM (room 107, floor 1): sleeping, name contains 'BEDROOM' *(window schedule, symbol 7, LOCATION)*
  - Nominal size: `2'-6" x 3' - 0"` → 2'-6" x 3'-0" = 7.5 sf *(window schedule, symbol 7, NOMINAL SIZE)*
  - Operation: `L.H. CASM'T` → casement *(window schedule, symbol 7, TYPE (operation))*
  - Type mark: `F` → F *(window schedule, symbol 7, TYPE (mark))*
  - Head height: `6' - 8"` → 6'-8" *(window schedule, symbol 7, HEAD HEIGHT)*
  - Egress: `Y` → designated EERO *(window schedule, symbol 7, EGRESS)*
- **Worked out:**
  - Best-case clear opening = nominal x operation factor (casement: width x1, height x1) = 30 x 36 in.
  - Area = 30 x 36 / 144 = 7.50 sf.
  - Sill = head height 6'-8" - nominal height 3'-0" = 44 in above the floor.
  - Sill about 56 in above the grade plane (sill 44 in + first floor 12 in above grade plane): more than 44 in, so probably not a grade-floor opening; 5.7 sf applies unless grade at this wall is higher.
  - At the limit: sill: best case exactly 44 in, so any frame loss puts the opening above 44 in (1030.3)
  - Open: area: best case 7.50 sf vs 5.7 sf required, so net clear must be at least 76% of it
  - Open: clear height: best case 36 in vs 24 in minimum (12 in to spare before frame loss)
  - Open: clear width: best case 30 in vs 20 in minimum (10 in to spare before frame loss)

### BEDROOM 101: Could Not Evaluate

No designated window is shown to comply: window 1 needs net clear data; window 3 needs net clear data. Settled by: manufacturer net clear opening (width, height) for window type A, or a net-clear column on the schedule. *(IBC 1030.1, 1030.2, 1030.2.1, 1030.3)*

#### Window 1: Could Not Evaluate

- **Verdict:** Could Not Evaluate
- **Code:** IBC 1030.2, IBC 1030.2.1, IBC 1030.3
- **Why:** Nominal size would comply, but the schedule doesn't give the net clear opening. Area: best case 10.00 sf vs 5.7 sf required, so net clear must be at least 57% of it (50% if it's a grade-floor opening); clear height: best case 48 in vs 24 in minimum (24 in to spare before frame loss); clear width: best case 30 in vs 20 in minimum (10 in to spare before frame loss); sill: 32 in, 12 in under the max before the sill frame is added.
- **Margin:** area: needs 57% of nominal as net clear
- *Reason code: `NET_CLEAR_UNKNOWN`*
- **Settled by:** manufacturer net clear opening (width, height) for window type A, or a net-clear column on the schedule
- **Read from the documents:**
  - Location: `BEDROOM 101` → BEDROOM (room 101, floor 1): sleeping, name contains 'BEDROOM' *(window schedule, symbol 1, LOCATION)*
  - Nominal size: `2' - 6" x 4' - 0"` → 2'-6" x 4'-0" = 10 sf *(window schedule, symbol 1, NOMINAL SIZE)*
  - Operation: `L.H. CASM'T` → casement *(window schedule, symbol 1, TYPE (operation))*
  - Type mark: `A` → A *(window schedule, symbol 1, TYPE (mark))*
  - Head height: `6' - 8"` → 6'-8" *(window schedule, symbol 1, HEAD HEIGHT)*
  - Egress: `Y` → designated EERO *(window schedule, symbol 1, EGRESS)*
- **Worked out:**
  - Best-case clear opening = nominal x operation factor (casement: width x1, height x1) = 30 x 48 in.
  - Area = 30 x 48 / 144 = 10.00 sf.
  - Sill = head height 6'-8" - nominal height 4'-0" = 32 in above the floor.
  - Sill about 44 in above the grade plane (sill 32 in + first floor 12 in above grade plane): within 44 in, so possibly a grade-floor opening (5.0 sf).
  - Open: area: best case 10.00 sf vs 5.7 sf required, so net clear must be at least 57% of it (50% if it's a grade-floor opening)
  - Open: clear height: best case 48 in vs 24 in minimum (24 in to spare before frame loss)
  - Open: clear width: best case 30 in vs 20 in minimum (10 in to spare before frame loss)
  - Open: sill: 32 in, 12 in under the max before the sill frame is added

#### Window 3: Could Not Evaluate

- **Verdict:** Could Not Evaluate
- **Code:** IBC 1030.2, IBC 1030.2.1, IBC 1030.3
- **Why:** Nominal size would comply, but the schedule doesn't give the net clear opening. Area: best case 10.00 sf vs 5.7 sf required, so net clear must be at least 57% of it (50% if it's a grade-floor opening); clear height: best case 48 in vs 24 in minimum (24 in to spare before frame loss); clear width: best case 30 in vs 20 in minimum (10 in to spare before frame loss); sill: 32 in, 12 in under the max before the sill frame is added.
- **Margin:** area: needs 57% of nominal as net clear
- *Reason code: `NET_CLEAR_UNKNOWN`*
- **Settled by:** manufacturer net clear opening (width, height) for window type A, or a net-clear column on the schedule
- **Read from the documents:**
  - Location: `BEDROOM 101` → BEDROOM (room 101, floor 1): sleeping, name contains 'BEDROOM' *(window schedule, symbol 3, LOCATION)*
  - Nominal size: `2' - 6" x 4' - 0"` → 2'-6" x 4'-0" = 10 sf *(window schedule, symbol 3, NOMINAL SIZE)*
  - Operation: `R.H. CASM'T` → casement *(window schedule, symbol 3, TYPE (operation))*
  - Type mark: `A` → A *(window schedule, symbol 3, TYPE (mark))*
  - Head height: `6' - 8"` → 6'-8" *(window schedule, symbol 3, HEAD HEIGHT)*
  - Egress: `Y` → designated EERO *(window schedule, symbol 3, EGRESS)*
- **Worked out:**
  - Best-case clear opening = nominal x operation factor (casement: width x1, height x1) = 30 x 48 in.
  - Area = 30 x 48 / 144 = 10.00 sf.
  - Sill = head height 6'-8" - nominal height 4'-0" = 32 in above the floor.
  - Sill about 44 in above the grade plane (sill 32 in + first floor 12 in above grade plane): within 44 in, so possibly a grade-floor opening (5.0 sf).
  - Open: area: best case 10.00 sf vs 5.7 sf required, so net clear must be at least 57% of it (50% if it's a grade-floor opening)
  - Open: clear height: best case 48 in vs 24 in minimum (24 in to spare before frame loss)
  - Open: clear width: best case 30 in vs 20 in minimum (10 in to spare before frame loss)
  - Open: sill: 32 in, 12 in under the max before the sill frame is added

| Other window | Verdict | Why |
|---|---|---|
| 2 | Not Applicable | Not marked EGRESS, so it isn't the room's escape opening. As an alternative it couldn't serve: fixed unit, does not open, so normal operation gives no clear opening (see the BEDROOM 101 finding). |

### BEDROOM 203: **Fail**

Every designated escape window fails (10), so the room has no compliant EERO. *(IBC 1030.1, 1030.2, 1030.3)*

#### Window 10: **Fail**

- **Verdict:** **Fail**
- **Code:** IBC 1030.2, 1030.3
- **Why:** Area 5.00 sf < 5.7 sf even with no frame loss (1030.2); sill 50 in > 44 in max, 6 in over before any frame (1030.3).
- **Margin:** sill 6 in too high; area 0.70 sf short
- **Read from the documents:**
  - Location: `BEDROOM 203` → BEDROOM (room 203, floor 2): sleeping, name contains 'BEDROOM' *(window schedule, symbol 10, LOCATION)*
  - Nominal size: `2' - 0" x 2' - 6"` → 2'-0" x 2'-6" = 5 sf *(window schedule, symbol 10, NOMINAL SIZE)*
  - Operation: `L.H. CASM'T` → casement *(window schedule, symbol 10, TYPE (operation))*
  - Type mark: `H` → H *(window schedule, symbol 10, TYPE (mark))*
  - Head height: `6' - 8"` → 6'-8" *(window schedule, symbol 10, HEAD HEIGHT)*
  - Egress: `Y` → designated EERO *(window schedule, symbol 10, EGRESS)*
- **Worked out:**
  - Best-case clear opening = nominal x operation factor (casement: width x1, height x1) = 24 x 30 in.
  - Area = 24 x 30 / 144 = 5.00 sf.
  - Sill = head height 6'-8" - nominal height 2'-6" = 50 in above the floor.
  - Fails: area 5.00 sf < 5.7 sf even with no frame loss (1030.2)
  - Fails: sill 50 in > 44 in max, 6 in over before any frame (1030.3)
  - Open: clear height: best case 30 in vs 24 in minimum (6 in to spare before frame loss)
  - Open: clear width: best case 24 in vs 20 in minimum (4 in to spare before frame loss)

| Other window | Verdict | Why |
|---|---|---|
| 11 | Not Applicable | Not marked EGRESS, so it isn't the room's escape opening. As an alternative it couldn't serve: fixed unit, does not open, so normal operation gives no clear opening (see the BEDROOM 203 finding). |

### BEDROOM 205: **Could Not Evaluate** (likely Fail — confirm)

No designated window is shown to comply: window 12 is at the limit; window 13 fails. Settled by: manufacturer data or a detail for type J: net clear width/height and the sill-to-clear-opening offset. *(IBC 1030.1, 1030.2, 1030.2.1, 1030.3)*

#### Window 12: **Could Not Evaluate** (likely Fail — confirm)

- **Verdict:** **Could Not Evaluate** (likely Fail — confirm)
- **Code:** IBC 1030.2, IBC 1030.2.1, IBC 1030.3
- **Why:** At the limit even in the best case: clear height: best case exactly 24 in, so any frame or rail loss fails it (1030.2.1). Also open: area: best case 6.00 sf vs 5.7 sf required, so net clear must be at least 95% of it; clear width: best case 36 in vs 20 in minimum (16 in to spare before frame loss); sill: 32 in, 12 in under the max before the sill frame is added.
- **Margin:** clear height: 0 in to spare; area: needs 95% of nominal as net clear
- *Reason code: `HUNG_HEIGHT_AT_LIMIT`*
- **Settled by:** manufacturer data or a detail for type J: net clear width/height and the sill-to-clear-opening offset
- **Read from the documents:**
  - Location: `BEDRROM 205` → BEDROOM (room 205, floor 2): sleeping, 'BEDRROM' is BEDROOM with an OCR error *(window schedule, symbol 12, LOCATION)*
  - Nominal size: `3' - 0" x 4' - 0"` → 3'-0" x 4'-0" = 12 sf *(window schedule, symbol 12, NOMINAL SIZE)*
  - Operation: `S.H.` → single hung *(window schedule, symbol 12, TYPE (operation))*
  - Type mark: `J` → J *(window schedule, symbol 12, TYPE (mark))*
  - Head height: `6' - 8"` → 6'-8" *(window schedule, symbol 12, HEAD HEIGHT)*
  - Egress: `Y` → designated EERO *(window schedule, symbol 12, EGRESS)*
- **Worked out:**
  - Best-case clear opening = nominal x operation factor (single hung: width x1, height x0.5) = 36 x 24 in.
  - Area = 36 x 24 / 144 = 6.00 sf.
  - Sill = head height 6'-8" - nominal height 4'-0" = 32 in above the floor.
  - At the limit: clear height: best case exactly 24 in, so any frame or rail loss fails it (1030.2.1)
  - Open: area: best case 6.00 sf vs 5.7 sf required, so net clear must be at least 95% of it
  - Open: clear width: best case 36 in vs 20 in minimum (16 in to spare before frame loss)
  - Open: sill: 32 in, 12 in under the max before the sill frame is added
- **Assumptions:**
  - Hung window: only one sash opens; assumed to be half the unit height (equal sashes). A cottage-style unit with a taller bottom sash would open more.

#### Window 13: **Fail**

- **Verdict:** **Fail**
- **Code:** IBC 1030.2.1
- **Why:** Fixed window: it doesn't open, so it provides no clear opening under normal operation.
- **Margin:** no operable opening
- **Read from the documents:**
  - Location: `BEDROOM 205` → BEDROOM (room 205, floor 2): sleeping, name contains 'BEDROOM' *(window schedule, symbol 13, LOCATION)*
  - Nominal size: `4' - 0" x 4' - 0"` → 4'-0" x 4'-0" = 16 sf *(window schedule, symbol 13, NOMINAL SIZE)*
  - Operation: `FIXED` → fixed *(window schedule, symbol 13, TYPE (operation))*
  - Type mark: `K` → K *(window schedule, symbol 13, TYPE (mark))*
  - Head height: `6' - 8"` → 6'-8" *(window schedule, symbol 13, HEAD HEIGHT)*
  - Egress: `Y` → designated EERO *(window schedule, symbol 13, EGRESS)*

### BEDROOM 301: **Fail**

Every designated escape window fails (20), so the room has no compliant EERO. *(IBC 1030.1, 1030.3)*

#### Window 20: **Fail**

- **Verdict:** **Fail**
- **Code:** IBC 1030.3
- **Why:** Sill 60 in > 44 in max, 16 in over before any frame (1030.3).
- **Margin:** sill 16 in too high
- **Read from the documents:**
  - Location: `BEDROOM 301` → BEDROOM (room 301, floor 3): sleeping, name contains 'BEDROOM' *(window schedule, symbol 20, LOCATION)*
  - Nominal size: `2' - 6" x 3' - 0"` → 2'-6" x 3'-0" = 7.5 sf *(window schedule, symbol 20, NOMINAL SIZE)*
  - Operation: `L.H. CASM'T` → casement *(window schedule, symbol 20, TYPE (operation))*
  - Type mark: `F` → F *(window schedule, symbol 20, TYPE (mark))*
  - Head height: `8' - 0"` → 8'-0" *(window schedule, symbol 20, HEAD HEIGHT)*
  - Egress: `Y` → designated EERO *(window schedule, symbol 20, EGRESS)*
- **Worked out:**
  - Best-case clear opening = nominal x operation factor (casement: width x1, height x1) = 30 x 36 in.
  - Area = 30 x 36 / 144 = 7.50 sf.
  - Sill = head height 8'-0" - nominal height 3'-0" = 60 in above the floor.
  - Fails: sill 60 in > 44 in max, 16 in over before any frame (1030.3)
  - Open: area: best case 7.50 sf vs 5.7 sf required, so net clear must be at least 76% of it
  - Open: clear height: best case 36 in vs 24 in minimum (12 in to spare before frame loss)
  - Open: clear width: best case 30 in vs 20 in minimum (10 in to spare before frame loss)

### GUEST BED 303: Could Not Evaluate

Sleeping room with no window marked EGRESS. Possible: window 21 (L.H. CASM'T) could comply in the best case. The code analysis says EEROs are 'PROVIDED AT ALL SLEEPING ROOMS PER IBC 1030. SEE WINDOW SCHEDULE, SHEET A6.1'. Settled by: the architect designating an escape window (and its net clear data). *(IBC 1030.1)*

| Other window | Verdict | Why |
|---|---|---|
| 21 | Not Applicable | Not marked EGRESS, so it isn't the room's escape opening. As an alternative it could comply in the best case (see the GUEST BED 303 finding). |

### OFFICE 102: Could Not Evaluate

'OFFICE' isn't named as a bedroom, but 'OFFICE' rooms are sometimes slept in. If it's a sleeping room it needs an EERO; designated: none; possible: window 4 (L.H. CASM'T) could comply in the best case. Settled by: the floor plan / the architect's intended use of the room. *(IBC 1030.1)*

| Other window | Verdict | Why |
|---|---|---|
| 4 | Not Applicable | Not marked EGRESS, so it isn't the room's escape opening. As an alternative it could comply in the best case (see the OFFICE 102 finding). |

### Windows in rooms that aren't sleeping rooms

| Window | Room | Verdict | Why |
|---|---|---|---|
| 14 | BATH 206 | Not Applicable | BATH isn't a sleeping room (not a sleeping-room name), so 1030 doesn't require an EERO here. |
| 22 | HALL 302 | Not Applicable | HALL isn't a sleeping room (not a sleeping-room name), so 1030 doesn't require an EERO here. |
| 6 | KITCHEN 104 | Not Applicable | KITCHEN isn't a sleeping room (not a sleeping-room name), so 1030 doesn't require an EERO here. |
| 8 | LAUNDRY 108 | Not Applicable | LAUNDRY isn't a sleeping room (not a sleeping-room name), so 1030 doesn't require an EERO here. |
| 5 | LIVING 103 | Not Applicable | LIVING isn't a sleeping room (not a sleeping-room name), so 1030 doesn't require an EERO here. |
| 23 | STAIR S1 | Not Applicable | STAIR S1 isn't a sleeping room (not a sleeping-room name), so 1030 doesn't require an EERO here. |

## 6. Not checked

These need documents the tool wasn't given. They're not verdicts.

- **1030.1 Exception 2** (a bedroom exit door directly to the outside): needs the floor plans. Applies to every room Fail above.
- **1030.1 opens to a public way, yard or court:** needs the site plan.
- **1030.5 screens and bars releasable from inside:** the schedule marks screens but not their hardware; needs window details.
- **1030.2 grade-floor openings (5.0 sf):** needs finished grade at each window. The grade plane and first-floor elevations give an estimate (shown per window); first-floor windows are still treated as possibly grade-floor when calling a Fail.
- **Building height measurement:** the 504.3 check uses the architect's stated height; the grade-plane calculation (civil sheet) wasn't provided.
- **Table 504.4 (stories):** out of scope.

## Appendix A: how the schedule columns were read

| Header (as printed) | Read as | How |
|---|---|---|
| `SYMBOL` | symbol | header, contents agree (id) |
| `LOCATION` | location | header, contents agree (room) |
| `NOMINAL SIZE / WIDTH` | width | header, contents agree (length) |
| `NOMINAL SIZE / HEIGHT` | height | header, contents agree (length) |
| `TYPE` | operation | header, contents agree (operation) |
| `TYPE` | type_mark | header, contents agree (mark) |
| `HEAD HEIGHT` | head_height | header, contents agree (length) |
| `GLAZING / GLASS TYPE` | glass_type | header, contents agree (text) |
| `GLAZING / SAFETY` | safety | header, contents agree (mark) |
| `SCREE N` | screen | header, contents agree (flag) |
| `HARDWARE` | hardware | header (column empty) |
| `EGRESS` | egress | header, contents agree (flag) |
| `MANUFACTURE` | manufacturer | header (column empty) |
| `NOTES` | notes | header, contents agree (text) |

## Appendix B: code analysis as read

| Field | Label (as printed) | Value |
|---|---|---|
| project | `PROJECT` | NEW 3-STORY SINGLE-FAMILY DWELLING WITH ATTACHED ACCESSORY DWELLING UNIT (ADU). SLEEPING ROOMS ON ALL FLOORS |
| code | `APPLICABLE CODE` | 2018 INTERNATIONAL BUILDING CODE (IBC) AS ADOPTED BY THE CITY OF MERIDIAN FALLS |
| occupancy | `OCCUPANCY GROUP` | R-3 |
| construction | `CONSTRUCTION TYPE` | V-B |
| sprinklers | `FIRE SPRINKLE RS` | YES - AUTOMATIC SPRINKLER SYSTEM THROUGHOUT PER NFPA 13D (IBC 903.3.1.3) |
| stories | `NUMBER OF STORIES` | 3 |
| height | `BUILDING HEIGHT ABOVE GRADE PLAN E` | 41' - 6" (TO AVG. HT. OF HIGHEST ROOF SURFACE) |
| allowable_height | `ALLOWABLE HEIGHT` | 60' - 0" PER TABLE 504.3 |
| grade_plane | `GRADE PLANE` | EL. 100.0' (SEE CIVIL C1.0). FIRST FLOOR F.F. EL. 101.0' |
| room_numbering | `ROOM NUMBERING` | 1XX = FIRST FLOOR, 2XX = SECOND FLOOR, 3XX = THIRD FLOOR |
| egress_note | `EMERGENCY ESCAPE & RESCUE` | PROVIDED AT ALL SLEEPING ROOMS PER IBC 1030. SEE WINDOW SCHEDULE, SHEET A6.1 |
