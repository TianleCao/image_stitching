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

Using RANSAC (Random Sample Consensus) along with our matched features, we can robustly estimate this homography matrix $\mathbf{H}_{2 \to 1}$, which maps pixels from Image 2 to Image 1.

## 3. Warping the Images

Once we have $\mathbf{H}_{2 \to 1}$, we must "warp" Image 2 so it aligns with Image 1. However, we can't just apply $\mathbf{H}_{2 \to 1}$ directly and call it a day, because the warped Image 2 might end up with negative coordinates or get clipped outside the standard image boundaries.

### Redefining the Canvas Boundary

To ensure both images fit into a single canvas without cropping:
1. We calculate the coordinates of the four corners of Image 2 after applying the homography $\mathbf{H}_{2 \to 1}$.
2. We find the global minimum and maximum $x$ and $y$ coordinates across the corners of *both* the original Image 1 and the warped Image 2.
3. If the minimum $x$ or $y$ is negative, it means the warped image extends to the top or left of Image 1. We must introduce a **Translation Matrix (Offset)** to shift everything into positive coordinates:

$$
\mathbf{H}_{\text{offset}} = \begin{bmatrix} 1 & 0 & -x_{\min} \\ 0 & 1 & -y_{\min} \\ 0 & 0 & 1 \end{bmatrix}
$$

### Applying the Warps

To warp Image 1 onto the new canvas, we just apply the translation:
$$ \text{Image 1}_{\text{warped}} = \text{warpPerspective}(\text{Image 1}, \mathbf{H}_{\text{offset}}) $$

To warp Image 2, we combine the homography and the translation:
$$ \text{Image 2}_{\text{warped}} = \text{warpPerspective}(\text{Image 2}, \mathbf{H}_{\text{offset}} \mathbf{H}_{2 \to 1}) $$

![Fig 3: Warped Images](../imgs/fig3.jpg)
<br>

*(Under the hood, `warpPerspective` performs **inverse warping**: iterating over the new canvas coordinates, applying the inverse matrix to find the source coordinate, and using bilinear interpolation to sample the color).*

## 4. Blending

Once warped, we have two aligned images on the same canvas. Simply pasting one over the other creates a harsh, visible seam due to exposure differences and lens vignetting.

We solve this using **Laplacian Pyramid Blending**:
1. **Gaussian Pyramids**: We build a Gaussian pyramid for both warped images and a generated binary mask. To avoid artifacts from the sharp image boundaries, we slightly **erode** the mask first. This ensures the transition happens in a region where both images have valid data.
2. **Laplacian Pyramids**: From the Gaussian pyramids, we build Laplacian pyramids, which capture the high-frequency details (edges) at each scale.
3. **Multi-band Blending**: We blend the Laplacian levels of the two images together using the Gaussian pyramid of the mask as the weights.
4. **Reconstruction**: Finally, we collapse the blended Laplacian pyramid back into a single, high-resolution image. 

![Fig 4: Blending Comparison](../imgs/fig4.jpg)
<br>

This technique smoothly transitions low frequencies (like sky colors) over a wide area, while transitioning high frequencies (like sharp edges) over a very narrow area, effectively hiding the seam!

---

## Appendix: Proof that Pure Camera Rotation is a Homography

Let a 3D point be $\mathbf{P} = [X, Y, Z]^T$. 
A camera projects this 3D point onto a 2D pixel coordinate $\mathbf{p} = [x, y, 1]^T$ (in homogeneous coordinates) using the camera intrinsic matrix $\mathbf{K}$ and its rotation $\mathbf{R}$ and translation $\mathbf{t}$.

If the first camera is at the origin with no rotation, its projection equation is:
$$ \lambda_1 \mathbf{p}_1 = \mathbf{K}_1 [\mathbf{I} \mid \mathbf{0}] \begin{bmatrix} \mathbf{P} \\ 1 \end{bmatrix} = \mathbf{K}_1 \mathbf{P} $$
which gives $\mathbf{P} = \lambda_1 \mathbf{K}_1^{-1} \mathbf{p}_1$.

If the second camera shares the exact same center but is rotated by $\mathbf{R}$, its projection is:
$$ \lambda_2 \mathbf{p}_2 = \mathbf{K}_2 [\mathbf{R} \mid \mathbf{0}] \begin{bmatrix} \mathbf{P} \\ 1 \end{bmatrix} = \mathbf{K}_2 \mathbf{R} \mathbf{P} $$

Substituting $\mathbf{P}$ from the first equation into the second:
$$ \lambda_2 \mathbf{p}_2 = \mathbf{K}_2 \mathbf{R} (\lambda_1 \mathbf{K}_1^{-1} \mathbf{p}_1) $$
$$ \frac{\lambda_2}{\lambda_1} \mathbf{p}_2 = (\mathbf{K}_2 \mathbf{R} \mathbf{K}_1^{-1}) \mathbf{p}_1 $$

Since homogeneous coordinates are scale-invariant, the scalar $\frac{\lambda_2}{\lambda_1}$ doesn't change the 2D point. Therefore, the pixels are related by a $3 \times 3$ linear transformation matrix:
$$ \mathbf{H} = \mathbf{K}_2 \mathbf{R} \mathbf{K}_1^{-1} $$

This proves that for pure camera rotation, the mapping between the two images is purely a homography $\mathbf{H}$, entirely independent of the depth $Z$ of the 3D point $\mathbf{P}$!
