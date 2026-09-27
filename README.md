# Jessie

[Image to Favicon Converter]()

Convert **JPG, JPEG and PNG** images into multi-resolution Windows **.ico** files, powered by [Pillow](https://python-pillow.org/) and managed with [uv](https://docs.astral.sh/uv/).

## Quick start

```bash
uv sync                          # create .venv and install everything
uv run jessie logo.png           # -> logo.ico (16–256 px)
```

## Usage

```bash
uv run jessie photo.jpg -o app.ico            # explicit output
uv run jessie a.png b.jpeg -d icons/          # batch into a folder
uv run jessie logo.png -s 16,32,48 --force    # custom sizes, overwrite
uv run jessie wide.png --no-pad               # keep aspect ratio instead of transparent padding
python -m jessie logo.png                     # module form
```

As a library:

```python
from jessie import convert_many, convert_to_ico

convert_to_ico("logo.png", "build/app.ico", sizes=[16, 32, 256], overwrite=True)

# Batch: one result per source; clashing names (logo.png + logo.jpg) are renamed, never overwritten
for result in convert_many(["logo.png", "logo.jpg"], "build/icons"):
    print(result.icon if result.ok else result.error)
```

## Architecture

Modules in `src/jessie` and what each imports. Arrows point from importer to imported.

```mermaid
%%{init: {'theme':'base','themeVariables':{'background':'#0d1117','primaryColor':'#161b22','primaryTextColor':'#e6edf3','primaryBorderColor':'#58a6ff','lineColor':'#8b949e','secondaryColor':'#1f2937','tertiaryColor':'#0d1117','clusterBkg':'#0d1117','clusterBorder':'#30363d','fontFamily':'Inter, Segoe UI, sans-serif','fontSize':'14px'}}}%%
flowchart TB
    subgraph entry["Entry points"]
        direction LR
        SCRIPT(["jessie command<br/>pyproject: jessie.cli:main"])
        MAIN(["python -m jessie<br/>__main__.py"])
        LIB(["Library caller<br/>from jessie import …"])
    end

    subgraph pkg["src/jessie"]
        CLI["cli.py<br/>argparse · logging · exit codes"]
        INIT["__init__.py<br/>public API · __version__"]
        subgraph conv["converter.py · the conversion module"]
            direction LR
            PUB["<b>public</b><br/>convert_many<br/>convert_to_ico<br/>ConversionResult"]
            PRIV["<b>private</b><br/>_plan_icons · _clash_key<br/>_validate_source · _validate_sizes<br/>_prepare_image"]
            PUB --> PRIV
        end
        EXC["exceptions.py<br/>JessieError<br/>SourceNotFound · UnsupportedFormat · InvalidSize<br/>OutputExists · IconWrite · EmptyBatch"]
    end

    subgraph ext["External"]
        direction LR
        PIL[(Pillow)]
        FS[(File system<br/>source images · icons)]
    end

    SCRIPT --> CLI
    MAIN --> CLI
    LIB --> INIT
    CLI --> INIT
    CLI --> PUB
    CLI --> EXC
    INIT --> PUB
    INIT --> EXC
    conv --> EXC
    conv --> PIL
    conv --> FS
    PIL --> FS

    classDef accent fill:#1f6feb,stroke:#58a6ff,color:#ffffff;
    classDef private fill:#161b22,stroke:#58a6ff,stroke-dasharray:4 4,color:#8b949e;
    classDef ext fill:#238636,stroke:#3fb950,color:#ffffff;
    class PUB accent;
    class PRIV private;
    class PIL,FS ext;
```

- `converter.py` never imports `cli.py`: it doesn't print or exit, and every failure it raises is a `JessieError`.
- The helpers prefixed `_` are private. Tests go through `convert_to_ico`, `convert_many` and `cli.main`.
- Pillow is the only runtime dependency.

## How a conversion flows

```mermaid
%%{init: {'theme':'base','themeVariables':{'background':'#0d1117','primaryColor':'#161b22','primaryTextColor':'#e6edf3','primaryBorderColor':'#58a6ff','lineColor':'#8b949e','secondaryColor':'#1f2937','tertiaryColor':'#0d1117','fontFamily':'Inter, Segoe UI, sans-serif','fontSize':'14px','noteBkgColor':'#1f2937','noteTextColor':'#e6edf3','actorBkg':'#161b22','actorBorder':'#58a6ff','actorTextColor':'#e6edf3','signalColor':'#8b949e','signalTextColor':'#e6edf3'}}}%%
flowchart LR
    U([User]) -->|"jessie SOURCE… -o/-d -s"| CLI["cli.py<br/>argparse · logging · report"]
    L([Library caller]) -->|"from jessie import …"| CONV
    subgraph CONV["converter.py"]
        direction TB
        MANY["convert_many<br/>drop repeats · validate sources<br/>plan icons, rename clashes"]
        ONE["convert_to_ico<br/>validate · prepare · save"]
        MANY -->|each valid source| ONE
        ONE -. "JessieError → result.error" .-> MANY
    end
    CLI -->|"-d or no -o"| MANY
    CLI -->|"-o"| ONE
    MANY -. "list of ConversionResult" .-> CLI
    ONE -. "JessieError, -o only" .-> CLI
    ONE -->|"Image.open / save ICO"| PIL[(Pillow)]
    PIL --> OUT[/"one icon per source image<br/>one frame per size"/]
    CLI -->|"prints icons · logs errors"| X(["exit 0 ok · 1 any failed · 2 bad usage"])
    classDef accent fill:#1f6feb,stroke:#58a6ff,color:#ffffff;
    class MANY,ONE accent;
```

## Development

| Task | Command |
|---|---|
| Install | `make install` / `uv sync` |
| Format | `make format` |
| Lint | `make lint` |
| Type-check | `make typecheck` |
| Test + coverage | `make test` |
| Everything CI runs | `make check` |

See [`docs/`](docs/index.md) for architecture, usage, development, testing and contribution guides.
