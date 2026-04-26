# Image Stitching: From Theory to Practice

This guide explains the core concepts behind our image stitching implementation. We focus on the "why" and "how" of registering, warping, and blending images.

## 1. Registering Images

To stitch two images together, we first need to "register" them—that is, figure out how they align. 

![Fig 1: Original Images](../imgs/fig1.jpg)
<br>

1. **Feature Detection**: We use algorithms like SIFT (Scale-Invariant Feature Transform) to find distinctive keypoints (like corners or high-contrast spots) in both images.
2. **Feature Matching**: Each keypoint comes with a "descriptor" (a vector describing its local neighborhood). We match keypoints across images by finding descriptors with the smallest distance (e.g., using K-Nearest Neighbors and Lowe's ratio test).
   
![Fig 2: Feature Matching](../imgs/fig2.jpg)
<br>

3. **Transformation Estimation**: Given these matching point pairs, we estimate a transformation matrix that maps points from Image 2's coordinate space to Image 1's coordinate space. 

## 2. Why Homography?

Generally, the transformation between two images of a 3D scene taken from different viewpoints is complex and depends heavily on the distance to the objects (depth) in the scene. This relationship is typically described using Epipolar Geometry (e.g., via the Fundamental Matrix). 

However, there are two specific cases where the transformation between pixel coordinates in two images can be perfectly described by a much simpler $3 \times 3$ matrix called a **Homography**:
1. **Planar Scene:** The cameras are viewing a completely flat, 2D plane (e.g., taking a picture of a painting, a document, or a completely flat wall).
2. **Pure Camera Rotation:** The cameras are located at the exact same point in 3D space, but are rotated and/or zoomed. There is no translation (movement) of the camera's optical center.

In image stitching, we are in the case of **pure camera rotation** because usually, multiple images taken for a panorama can be approximated as rotating the camera around its optical center without translation (like a photographer standing still and turning, or using a tripod). 

Because there is no translation, the 3D depth of the scene doesn't matter, and the mapping between the two images is a pure homography. *(See the Appendix for the mathematical proof).*

## 3. Warping the Images

Once we have our homography $\mathbf{H}_{2 \to 1}$, we must "warp" Image 2 so it aligns with Image 1. 

### Redefining the Canvas Boundary

To ensure both images fit into a single canvas without cropping:
1. We calculate the new coordinates of Image 2's corners using $\mathbf{H}_{2 \to 1}$.
2. We find the global minimum and maximum coordinates ($x_{\min}, y_{\min}$, etc.) across both images.
3. We shift the entire coordinate system by $-x_{\min}$ and $-y_{\min}$ using a **Translation Matrix ($\mathbf{H}_{\text{offset}}$)** to ensure all pixels have positive coordinates.

### Applying the Warps

To warp Image 1 onto the new canvas, we just apply the translation:
$$ \text{Image 1}_{\text{warped}} = \text{warpPerspective}(\text{Image 1}, \mathbf{H}_{\text{offset}}) $$

To warp Image 2, we combine the homography and the translation:
$$ \text{Image 2}_{\text{warped}} = \text{warpPerspective}(\text{Image 2}, \mathbf{H}_{\text{offset}} \mathbf{H}_{2 \to 1}) $$

![Fig 3: Warped Images](../imgs/fig3.jpg)
<br>

## 4. Simple Blending: Defining the Mask

Once warped, we have two aligned images. To combine them, we need to decide which image to use for each pixel on the canvas. We do this using a **Mask** ($M$).

### What is a Mask?
A mask is a grayscale image of the same size as our canvas where:
- A value of **1 (White)** means "Use Image 1".
- A value of **0 (Black)** means "Use Image 2".

The final image $I$ is calculated as:
$$ I = M \cdot I_1 + (1 - M) \cdot I_2 $$

### Defining the Seam
For a beginner, the simplest mask is a **Binary Mask** that splits the overlap right down the middle. If Image 1 is on the left and Image 2 is on the right, we find the horizontal center of the overlapping region and create a mask that is 1 to the left of that line and 0 to the right.

![Fig 4: Simple Mask and Result](../imgs/fig4.jpg)
<br>

While simple, this often leaves a visible "seam" because the two images might have slightly different brightness or colors. To solve this, we can use more advanced techniques like Laplacian Pyramids (see Appendix B).

---

## Appendix A: Proof that Pure Camera Rotation is a Homography

Let a 3D point be $\mathbf{P} = [X, Y, Z]^T$. 
A camera projects this 3D point onto a 2D pixel coordinate $\mathbf{p} = [x, y, 1]^T$ using its intrinsic matrix $\mathbf{K}$ and rotation $\mathbf{R}$.

If the first camera is at the origin: $\lambda_1 \mathbf{p}_1 = \mathbf{K}_1 \mathbf{P}$.
If the second camera is rotated by $\mathbf{R}$: $\lambda_2 \mathbf{p}_2 = \mathbf{K}_2 \mathbf{R} \mathbf{P}$.

Substituting $\mathbf{P}$:
$$ \frac{\lambda_2}{\lambda_1} \mathbf{p}_2 = (\mathbf{K}_2 \mathbf{R} \mathbf{K}_1^{-1}) \mathbf{p}_1 \Rightarrow \mathbf{H} = \mathbf{K}_2 \mathbf{R} \mathbf{K}_1^{-1} $$

## Appendix B: Advanced Blending (Laplacian Pyramids)

To eliminate visible seams, we use **Multi-band Blending**:
1. **Seam Finding**: Use a **Distance Transform** to find the center-line of the overlap. This creates a more robust "weight mask" where each pixel is assigned to the image it is "deepest" inside of.
2. **Pyramid Decomposition**: We break both images and the mask into **Gaussian and Laplacian Pyramids**. 
3. **Multi-scale Blending**: We blend the images level-by-level. This allows us to blend low-frequency color changes over a wide area while keeping high-frequency details sharp.
4. **Reconstruction**: Collapsing the blended levels creates a seamless, professional result.

*(See our `softBlend` implementation in `stitch_toy.py` for the full code).*
