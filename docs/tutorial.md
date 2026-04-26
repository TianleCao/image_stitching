# Image Stitching: From Theory to Practice

This guide explains the core concepts behind our image stitching implementation. We focus on the "why" and "how" of registering, warping, and blending images.

## 1. Registering Images

To stitch two images together, we first need to "register" them—that is, figure out how they align. 

![Fig 1: Original Images](../imgs/fig1.jpg)
<br>

1. **Feature Detection**: We use algorithms like SIFT to find distinctive keypoints in both images.
2. **Feature Matching**: We match keypoints across images using their descriptors.
   
```python
# Detect SIFT features
pts1, des1 = detector.detectAndCompute(image1, None)
pts2, des2 = detector.detectAndCompute(image2, None)

# Match using KNN
matches = bf_matcher.knnMatch(des2, des1, k=2)
# Apply Lowe's ratio test
good_matches = [m for m, n in matches if m.distance < n.distance * 0.7]
```

![Fig 2: Feature Matching](../imgs/fig2.jpg)
<br>

3. **Transformation Estimation**: We estimate a **Homography** matrix that maps points from Image 2 to Image 1.

## 2. Why Homography?

Generally, the transformation between two images of a 3D scene is complex. However, in image stitching, we usually assume **pure camera rotation**. Because the camera center doesn't move, the mapping between images is perfectly described by a $3 \times 3$ Homography matrix $\mathbf{H}$, regardless of scene depth.

## 3. Warping the Images

We must warp Image 2 to align with Image 1. To fit both on a single canvas, we shift the coordinates using a translation matrix $\mathbf{H}_{\text{offset}}$ derived from the bounding box of both images.

```python
# Combine homography with canvas offset
H_final = H_offset @ H_2to1
# Warp images onto the shared canvas
warped1 = cv2.warpPerspective(image1, H_offset, (canvas_w, canvas_h))
warped2 = cv2.warpPerspective(image2, H_final, (canvas_w, canvas_h))
```

![Fig 3: Warped Images](../imgs/fig3.jpg)
<br>

## 4. Simple Blending: Defining the Mask

Once warped, we combine them using a **Mask** ($M$). A value of 1 means "Use Image 1", and 0 means "Use Image 2".

```python
# Create a mask to define the seam
final_image = mask * warped1 + (1 - mask) * warped2
```

![Fig 4: Simple Mask and Result](../imgs/fig4.jpg)
<br>

While simple, a binary mask often leaves a visible seam due to color differences. Advanced techniques like Laplacian blending (Appendix B) can hide these.

---

## Appendix A: Proof of Homography for Rotation
Pixels are related by: $\mathbf{H} = \mathbf{K}_2 \mathbf{R} \mathbf{K}_1^{-1}$.

## Appendix B: Advanced Blending (Laplacian Pyramids)

Multi-band blending allows us to transition low frequencies over a wide area and high frequencies over a narrow area.

```python
# Build pyramids
lp1 = build_laplacian_pyramid(image1)
lp2 = build_laplacian_pyramid(image2)
gm = build_gaussian_pyramid(weight_mask)

# Blend scale-by-scale
blended_lp = [m * l1 + (1 - m) * l2 for l1, l2, m in zip(lp1, lp2, gm)]
# Reconstruct
result = reconstruct_from_pyramid(blended_lp)
```

### Visual Comparison
As seen below, Laplacian blending (right) effectively hides the exposure differences and seam artifacts that are visible in simple binary blending (left).

![Fig 5: Simple vs Advanced Blending](../imgs/fig5.jpg)
