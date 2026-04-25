# Image Stitching

This repository documents my learning journey on how to perform image stitching. It includes a complete, runnable implementation along with the underlying mathematical concepts.

## Project Structure

- `src/image_stitching/`: Contains the core implementation.
  - `stitch.py`: The image stitching logic (SIFT features, matching, warping, blending).
- `docs/`: Mathematical background and explanations.
  - `math.md`: Explanation of homography and the math behind image stitching.
- `notebooks/`: Jupyter notebooks for visualizing the results.
- `imgs/`: Sample images for testing the algorithms.

## Quick Start

This project uses `uv` for fast dependency management.

### Installation

1. Install `uv` if you haven't already. While `pip install uv` works, the official standalone installer is recommended:
   - **macOS/Linux:** `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - **Windows:** `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`

2. Set up the virtual environment and install all dependencies:
   ```bash
   uv sync --all-extras
   ```
   *This single command automatically creates a `.venv` directory, installs the core requirements, installs the optional `dev` dependencies (like Jupyter), and installs this repository (`image-stitching`) in editable mode.*

### Running the Code

You can test the main stitching script directly using `uv run`:

```bash
uv run python src/image_stitching/stitch.py
```

Or start the Jupyter notebook in the `notebooks` directory to visualize the process:

```bash
uv run jupyter notebook notebooks/demo.ipynb
```

**Using VS Code:**
If you open this repository in VS Code, the Python extension will automatically detect the `.venv` folder created by `uv sync`. When you open `notebooks/demo.ipynb`, simply click the "Select Kernel" button in the top right and choose the Python environment from `.venv`. This allows you to run the notebook natively without launching the Jupyter server manually!
