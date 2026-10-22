# CRA Annex VII — text fixture vs Formex XML

- Text provisions: 13
- XML provisions: 13
- Shared loci: 13
- Exact matches: 6
- Normalization-only matches: 6
- Genuine wording differences: 1
- Exact-text differences (includes wrap-only): 7

## Structural

- Text-only loci: none
- XML-only loci: none
- Shared loci: 1(a), 1(b), 1(c), 1(d), 2(a), 2(b), 2(c), 3, 4, 5, 6, 7, 8

## Classification

Normalized string equality is **not** a claim of semantic equivalence.
The text fixture is unchanged pending independent verification of locus `1(d)`.

- Exact: 3, 4, 5, 6, 7, 8
- Normalization only: 1(a), 1(b), 1(c), 2(a), 2(b), 2(c)
- Genuine wording: 1(d)

## Unresolved parsing questions

- Locus 1(d) differs in wording (fixture 'the information…' vs Formex TXT 'user information…'). The controlled text fixture is left unchanged until independently verified against the official OJ/PDF; Formex is not treated as automatic ground truth.
- Normalized equality is not semantic equivalence.
- Text atomizer wraps at 78 columns; Formex extraction collapses whitespace then rewraps — exact-byte mismatches can be formatting-only.
- EUR-Lex HTML notice retrieval was WAF-blocked; XML identity is CELLAR Formex ZIP checksums in MANIFEST.json.

## Exact-text differences (sample)

### Locus `1(a)`

- normalized_match: True
- text: `a general description of the product with digital elements, including:
(a) its intended purpose;`
- xml: `a general description of the product with digital elements, including: (a) its
intended purpose;`

### Locus `1(b)`

- normalized_match: True
- text: `a general description of the product with digital elements, including:
(b) versions of software affecting compliance with essential cybersecurity
requirements;`
- xml: `a general description of the product with digital elements, including: (b)
versions of software affecting compliance with essential cybersecurity
requirements;`

### Locus `1(c)`

- normalized_match: True
- text: `a general description of the product with digital elements, including:
(c) where the product with digital elements is a hardware product, photographs
or illustrations showing external features, markin`
- xml: `a general description of the product with digital elements, including: (c)
where the product with digital elements is a hardware product, photographs or
illustrations showing external features, markin`

### Locus `1(d)`

- normalized_match: False
- text: `a general description of the product with digital elements, including:
(d) the information and instructions as set out in Annex II;`
- xml: `a general description of the product with digital elements, including: (d)
user information and instructions as set out in Annex II;`

### Locus `2(a)`

- normalized_match: True
- text: `a description of the design, development and production of the product with
digital elements and vulnerability handling processes, including:
(a) necessary information on the design and development of`
- xml: `a description of the design, development and production of the product with
digital elements and vulnerability handling processes, including: (a)
necessary information on the design and development of`
