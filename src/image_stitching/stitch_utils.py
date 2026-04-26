import numpy as np
import cv2
from image_stitching.pyramid import ImagePyramid

def readImages(image_paths):
    """ Read images from the specified paths.
    args:
        image_paths (list): A list of paths to images to read.
    returns:
        A list of images read from the specified paths.
    """
    images, imagesGray = [], []
    for path in image_paths:
        image = cv2.imread(path)
        images.append(image)
        imagesGray.append(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY))
    return images, imagesGray

def computeDescription(images, detector):
    """ Compute SIFT keypoints and descriptors for a list of images.
    args:
        images (list): A list of images to compute keypoints and descriptors for.
        detector: The SIFT detector to use.
    returns:
        A list of tuples containing keypoints and descriptors for each image.
    """
    descriptions = []
    for image in images:
        pts, des = detector.detectAndCompute(image, None)
        descriptions.append((pts, des))
    return descriptions

def matchDescription(descriptions, reference_index):
    """ MATCH SIFT descriptors within a list of images, using image at reference_index as the reference.
    args:
        descriptions (list): A list of tuples containing keypoints and descriptors for each image.
        reference_index (int): The index of the reference image in the descriptions list.
    returns:
        A list of matched keypoints for each image (keypoints in reference image, keypoints in moving image).
    """
    knnmatcher = cv2.BFMatcher(cv2.NORM_L2)
    ptsRef, descRef = descriptions[reference_index]
    matchedPtsList = []
    for i, (pts, des) in enumerate(descriptions):
        if i == reference_index:
            matchedPtsList.append((ptsRef, ptsRef)) # dummy match for reference image
            continue
        
        matches = knnmatcher.knnMatch(des, descRef, 2)
        # ratio check
        good_matches = []
        matchedPtsRef, matchedPtsMoving = [], []
        for m in matches:
            if m[0].distance < m[1].distance*0.7:
                good_matches.append(m[0])
                matchedPtsRef.append(ptsRef[m[0].trainIdx].pt)
                matchedPtsMoving.append(pts[m[0].queryIdx].pt)
        matchedPtsList.append((np.array(matchedPtsRef), np.array(matchedPtsMoving)))
    return matchedPtsList

def warp(images, homography):
    """ Warp images to the reference image using the computed homography matrices.
    args:
        images (list): A list of images to warp.
        homography (list): A list of homography matrices for each image to the reference image.
    returns:
        A list of warped images and corresponding masks indicating valid pixels.
    """
    warped_images, masks = [], []
    newXMin, newXMax, newYMin, newYMax = float('inf'),  -float('inf'), float('inf'), -float('inf')
    for image, H in zip(images, homography):
        h, w = image.shape[:2]
        x1, y1  = transform((0,0),H)
        x2, y2 = transform((w,0),H)
        x3, y3 = transform((0,h),H)
        x4, y4 = transform((w,h),H)
        newXMin, newXMax = min([x1,x2,x3,x4,newXMin]), max([x1,x2,x3,x4,newXMax])
        newYMin, newYMax = min([y1,y2,y3,y4,newYMin]), max([y1,y2,y3,y4,newYMax])
    HOffset = np.array([[1.0,0,-newXMin],[0,1.0,-newYMin],[0,0,1.0]])

    for image, H in zip(images, homography):
        warped = cv2.warpPerspective(image,HOffset@H,(newXMax-newXMin,newYMax-newYMin))
        warped_images.append(warped)
        m = np.ones(image.shape[:2], dtype=np.uint8)
        mask = cv2.warpPerspective(m, HOffset@H, (newXMax-newXMin, newYMax-newYMin))
        masks.append(mask)
    return warped_images, masks
    
def softBlend(images, masks):
    """
    Blend a list of images together using multi-band blending with distance transform-based seam finding.
    args:
        images (list): A list of images to blend.
        masks (list): A list of binary masks indicating valid pixels for each image.
    returns:
        The blended panorama image.
    """
    dists = np.stack([cv2.distanceTransform(mask, cv2.DIST_L2, 3) for mask in masks], axis=-1) 
    weight_mask = np.argmax(dists, axis=-1) # 0 where image1 is closer, 1 where image2 is closer, so on and so forth

    # Use 6 levels for smoother transition if the image size allows
    levels = 6
    imagePyramid = ImagePyramid(levels)
    gps = [imagePyramid.buildGaussianPyramid(image) for image in images]
    gpmasks = [imagePyramid.buildGaussianPyramid((weight_mask == i).astype(np.float32)) for i in range(len(images))]
    lps = [imagePyramid.buildLaplacianPyramid(gp) for gp in gps]

    blendedLaplacianPyramid = []
    for i in range(levels+1):
        lp_levels = [lp[i] for lp in lps]
        gpmask_levels = [gpmask[i] for gpmask in gpmasks]
        image = 0
        for lp, gpmask in zip(lp_levels, gpmask_levels):
            if len(lp.shape) == 3 and len(gpmask.shape) == 2:
                gpmask = np.expand_dims(gpmask, axis=-1)
            image += gpmask * lp
        blendedLaplacianPyramid.append(image)
        
    return imagePyramid.reconstructFromLaplacianPyramid(blendedLaplacianPyramid)
    
def transform(pt,H):
    """ Apply homography transformation to a point.
    args:
        pt (tuple): A tuple representing the (x, y) coordinates of the point to transform.
        H (numpy.ndarray): A 3x3 homography matrix to apply to the point.
    returns:
        A tuple representing the (x, y) coordinates of the transformed point.
    """
    pt = H @ np.array((pt[0],pt[1],1.0))
    pt = pt[:2]/pt[-1]
    return pt.astype(int)

def transformCylindricalToPlanar(coords, focal_length, img_width, img_height):
    """
    Transform cylindrical coordinates to planar coordinates using the cylindrical warping formula.
    args:
        coords  (Nx2 array): An array of (x, y) coordinates in the cylindrical image (not centered).
        focal_length (float): The focal length of the camera.
        img_width (int): The width of the image.
        img_height (int): The height of the image.
    returns:
        The transformed coordinates in the planar space.
    """
    x_i, y_i = coords[:,0], coords[:,1]
    x_c = x_i - img_width / 2.0
    y_c = y_i - img_height / 2.0
    theta = x_c / focal_length
    # Apply the Inverse Cylindrical Formula
    # x_src = f * tan(theta)
    # y_src = h_cyl * (f / Z) -> y_src = y_c / cos(theta)
    x_src = focal_length * np.tan(theta) + img_width / 2.0
    y_src = y_c / np.cos(theta) + img_height / 2.0
    return np.stack([x_src, y_src], axis=-1)

def transformPlanarToCylindrical(coords, focal_length, img_width, img_height):
    """
    Transform planar coordinates to cylindrical coordinates using the cylindrical warping formula.
    args:
        coords  (Nx2 array): An array of (x, y) coordinates in the planar image (not centered).
        focal_length (float): The focal length of the camera.
        img_width (int): The width of the image.
        img_height (int): The height of the image.
    returns:
        The transformed coordinates in the cylindrical space.
    """
    x_i, y_i = coords[:,0], coords[:,1]
    x_c = x_i - img_width / 2.0
    y_c = y_i - img_height / 2.0
    theta = np.arctan2(x_c, focal_length)
    # Apply the forward Cylindrical Formula
    x_cyl = focal_length * theta + img_width / 2.0
    y_cyl = y_c * np.cos(theta) + img_height / 2.0
    return np.stack([x_cyl, y_cyl], axis=-1)