# Recorded software evidence

This snapshot records the candidate iCEstick software experiment on 1 November 2026. Physical deployment is incomplete: no board or programmer was available and no hardware was programmed or observed.

`board.json` holds the reviewed candidate target facts and primary-source locators; it is copied to local reports by the identity stage and does not probe hardware. `models.json` identifies the unchanged official iCE40 cell library. `summary.json` records bounded results, stage input hashes, bitstream identity and remaining requirements. `documents.sha256.json` binds the exact reviewed PDF/PPTX copies in docs/.

Run every README software stage to regenerate local evidence. Raw logs, route/configuration/bitstream products and managed tool payloads are excluded from Git. Same-machine reproduction from the staged source package is checked separately; clean-machine and hardware reproduction are not claimed.
