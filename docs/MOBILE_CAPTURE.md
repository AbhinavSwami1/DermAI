# DermAI - Mobile Photo Capture

The analysis screen has two buttons next to each other: **Choose image** (file or gallery) and **Take photo**.

- Take photo uses a file input with `capture="environment"` and `accept="image/jpeg,image/png"`. On a phone it opens the rear camera; the captured photo then goes through the same preview, upload, validation, quality check and analysis steps as any other image.
- On a desktop browser the attribute is ignored and a file dialog opens.
- It works in a normal browser page; no native app or camera permission code is needed beyond the browser prompt. Browsers require HTTPS (or localhost) for camera access on some devices, so test on a phone over HTTPS or a local network address that the browser treats as secure.

## Limitations
- Phone photos are large (several megapixels). The upload limit is 10 MB; very high-resolution photos may exceed it.
- The blur threshold was validated on 224 x 224 images from PAD-UFES-20, not on full-resolution phone photos, so blur warnings on large photos need to be checked with real captures.
- Live in-page camera preview, on-device cropping and rotation are not implemented.
