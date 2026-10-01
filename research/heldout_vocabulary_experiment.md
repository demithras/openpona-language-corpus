# Held-out vocabulary reconstruction experiment

**Status: HISTORICAL RESEARCH**

**Evidence status (added 2026-10-01 after independent review):** every strength label in this file describes an internal, unpublished experiment from the 2026-09 research conversations. No data, method, baseline or code for them is in this repository. Read each label as *reported, unpublished*; nothing here is reproducible from the repository alone.

An early test used the reduced OpenPona inventory to reconstruct Toki Pona vocabulary that was not included in the 42-token kernel.

Reported results in the research conversation included:

- roughly **84.6%** functional reconstruction under one classification;
- a later closed-set decoding result of **70/78 (89.7%)**;
- strongest behavior in topology, relation and transformation;
- weaker behavior for scalar magnitude/quantity, sensory polarity and color/coordinate-like distinctions;
- collisions and locally weak reconstructions remained.

The architectural conclusion was **not** "OpenPona replaces Toki Pona". It was narrower:

> a small relational/operational kernel can reconstruct many omitted concepts compositionally, but bounded vocabulary has predictable weak axes.

No token was added merely to improve this benchmark.
