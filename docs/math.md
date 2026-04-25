# The Math Behind Image Stitching

Image stitching involves combining multiple images with overlapping fields of view to produce a single panoramic or high-resolution image. The core mathematical concept that enables this is the **Homography**.

## 1. Homogeneous Coordinates
Before discussing homography, we must understand homogeneous coordinates. In standard 2D Euclidean space, a point is represented as $(x, y)$. In homogeneous coordinates, we add a third dimension, making it $(x, y, 1)$. 

Any scalar multiple $w(x, y, 1) = (wx, wy, w)$ represents the same 2D point. To convert back to Euclidean coordinates, we divide by the third coordinate:
$$(x', y', w) \Rightarrow \left(\frac{x'}{w}, \frac{y'}{w}\right)$$

## 2. What is a Homography?
A homography is an isomorphism of projective spaces, which mathematically means it's an invertible transformation from one projective plane to another. In the context of computer vision, a planar homography is a $3 \times 3$ matrix $\mathbf{H}$ that maps points from one image plane to another, assuming the scene is roughly planar or the images were taken from the exact same camera center (just rotated/zoomed).

$$
\begin{bmatrix} x' \\ y' \\ w' \end{bmatrix} = \mathbf{H} \begin{bmatrix} x \\ y \\ 1 \end{bmatrix} = \begin{bmatrix} h_{11} & h_{12} & h_{13} \\ h_{21} & h_{22} & h_{23} \\ h_{31} & h_{32} & h_{33} \end{bmatrix} \begin{bmatrix} x \\ y \\ 1 \end{bmatrix}
$$

Because homography is defined up to a scale factor (since homogeneous coordinates are scale-invariant), $\mathbf{H}$ has 8 degrees of freedom. We typically set $h_{33} = 1$ to normalize it.

## 3. Estimating the Homography (Direct Linear Transform)
To estimate the homography matrix $\mathbf{H}$, we need pairs of corresponding points from the two images. Since each point pair gives us 2 equations (for $x$ and $y$), we need at least 4 point pairs to solve for the 8 unknowns.

From the matrix multiplication above, we have:
$$x' = \frac{h_{11}x + h_{12}y + h_{13}}{h_{31}x + h_{32}y + h_{33}}$$
$$y' = \frac{h_{21}x + h_{22}y + h_{23}}{h_{31}x + h_{32}y + h_{33}}$$

Multiplying out the denominators, we get:
$$x'(h_{31}x + h_{32}y + h_{33}) = h_{11}x + h_{12}y + h_{13}$$
$$y'(h_{31}x + h_{32}y + h_{33}) = h_{21}x + h_{22}y + h_{23}$$

Rearranging these into a system of equations $\mathbf{A}\mathbf{h} = 0$, where $\mathbf{h}$ is the flattened vector of $\mathbf{H}$:

$$
\begin{bmatrix}
-x & -y & -1 & 0 & 0 & 0 & x'x & x'y & x' \\
0 & 0 & 0 & -x & -y & -1 & y'x & y'y & y'
\end{bmatrix}
\begin{bmatrix} h_{11} \\ h_{12} \\ h_{13} \\ h_{21} \\ h_{22} \\ h_{23} \\ h_{31} \\ h_{32} \\ h_{33} \end{bmatrix} = \mathbf{0}
$$

With $N \geq 4$ point pairs, $\mathbf{A}$ becomes a $2N \times 9$ matrix. We can solve $\mathbf{A}\mathbf{h} = 0$ subject to $||\mathbf{h}|| = 1$ using **Singular Value Decomposition (SVD)**. The solution $\mathbf{h}$ is the right singular vector corresponding to the smallest singular value of $\mathbf{A}$ (the last row of $V^T$ in $A = U\Sigma V^T$).

## 4. Feature Matching
How do we find these point pairs?
1. **Detect Keypoints**: Algorithms like SIFT, SURF, or ORB detect distinct points (corners, blobs) in both images.
2. **Compute Descriptors**: A local patch around each keypoint is converted into a vector (descriptor).
3. **Match Features**: We find pairs by measuring the distance between descriptors (e.g., L2 norm). We often use Lowe's ratio test to reject ambiguous matches.

## 5. RANSAC (Random Sample Consensus)
Since feature matching is never perfect, we use RANSAC to robustly estimate $\mathbf{H}$:
1. Randomly select 4 pairs of points.
2. Compute $\mathbf{H}$ using DLT.
3. Apply $\mathbf{H}$ to all points in Image 1 and calculate the distance to their matches in Image 2.
4. Count the "inliers" (points where the distance is below a threshold).
5. Repeat for $k$ iterations and keep the $\mathbf{H}$ that produces the most inliers. Finally, recompute $\mathbf{H}$ using all inliers.

## 6. Warping and Blending
Once $\mathbf{H}$ is known, we can warp Image 2 into the coordinate space of Image 1. 

**Inverse Warping:**
Instead of mapping source pixels to destination (which leaves holes), we iterate over the destination grid. For each pixel in the output, we map it *backwards* using $\mathbf{H}^{-1}$ to find its location in the source image, and use bilinear interpolation to sample the color.

**Blending:**
A simple method is taking the average or overlaying one on top. A better approach (like the one implemented here) uses **Laplacian Pyramid Blending**, which seamlessly blends low frequencies over a wide area and high frequencies over a narrow area to prevent ghosting and visible seams.
