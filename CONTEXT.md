# Context

Domain glossary for Jessie. Use these words in code, docs, tests and reviews.

**Source image** — a JPG, JPEG or PNG file a user wants turned into an icon. _Avoid_: input, file (too vague). (`convert_to_ico(input_path, output_path)` keeps its original parameter names so existing keyword callers don't break.)

**Icon** — the `.ico` file Jessie writes for one source image. _Avoid_: output, ico.

**Frame** — one square resolution stored inside an icon (16, 32, …, 256 px). An icon holds several frames. _Avoid_: size (that's the frame's dimension, not the frame).

**Batch** — a set of source images converted in one run, by `convert_many` or the CLI with several sources. Each source image gets one icon and one `ConversionResult`; a failure never stops the batch.

**Clash** — two different source images in a batch whose icons would have the same path (`logo.png` and `logo.jpg` → `logo.ico`), compared case-insensitively. Only source images that exist and have a supported extension can clash. Every icon in a clash is renamed after its full source name (`logo.png.ico`), with a counter (`logo.png-2.ico`) if that still collides. The same source image listed twice is not a clash; it is converted once.
