# Image Stitching: Theory and Implementation

This repository documents a comprehensive learning journey into the world of image stitching. It provides a complete, modular, and runnable implementation of both planar and cylindrical image stitching, accompanied by a detailed mathematical tutorial.

## Project Structure

- `src/image_stitching/`: Core Python implementation.
  - `stitch_toy.py`: A simple, beginner-friendly implementation for stitching two images.
  - `stitch.py`: A modular, factory-based stitcher supporting multiple images (Planar & Cylindrical).
  - `stitch_utils.py`: Geometric transformations (Homography, Cylindrical projection) and warping logic.
  - `pyramid.py`: Laplacian and Gaussian pyramid implementation for professional-grade blending.
- `docs/`: In-depth educational material.
  - `tutorial.md`: A fully illustrated guide covering registration, homography vs. epipolar geometry, warping boundaries, and multi-band blending.
- `notebooks/`: Interactive visualizations.
  - `two_image_stitch_demo.ipynb`: Step-by-step breakdown of the 2-image stitching process.
  - `multiple_image_stitch.ipynb`: Demonstration of the multi-image pipeline using both Planar and Cylindrical modes.
- `imgs/`: Sample datasets and figures used in the tutorial.

## Quick Start

This project uses `uv` for modern, fast dependency management.

### Installation

1. **Install `uv`** (Official standalone installer recommended):
   - **macOS/Linux:** `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - **Windows:** `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`

2. **Sync the Environment**:
   ```bash
   uv sync --all-extras
   ```
   *This command creates a `.venv`, installs all core and dev dependencies, and sets up the project in editable mode.*

### Running the Code

Test the multi-image stitcher directly using `uv run`:

```bash
uv run python src/image_stitching/stitch.py
```

Or explore the interactive tutorials:

```bash
# Basic 2-image demo
uv run jupyter notebook notebooks/two_image_stitch_demo.ipynb

# Multi-image panorama demo
uv run jupyter notebook notebooks/multiple_image_stitch.ipynb
```

**Using VS Code:**
The Python extension will automatically detect the `.venv` directory. Open any notebook and select the `.venv` kernel to run cells natively within the editor.

## Key Features & Learning Outcomes

- **Geometric Alignment:** Understand the difference between Homography (planar) and 2D Translation (cylindrical) models.
- **Robust Registration:** Implementation of SIFT feature matching with RANSAC-based estimation.
- **Professional Blending:** Multi-band blending using Laplacian pyramids to eliminate seams and exposure differences.
- **Seam Finding:** Advanced seam optimization using Distance Transforms.
