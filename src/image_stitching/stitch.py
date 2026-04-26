import numpy as np
import cv2
from image_stitching.stitch_utils import readImages, computeDescription, matchDescription, softBlend, transform, transformPlanarToCylindrical, transformCylindricalToPlanar, warp

class StitcherFactory:
    def createStitcher(self, method):
        """ Factory method to create stitcher
        args:
            method (str): The stitching method to use. Options are 'planar' and 'cylindrical'.
        """
        if method == 'planar':
            return PlanarStitcher()
        elif method == 'cylindrical':
            return CylindricalStitcher()
        else:
            raise ValueError(f"Unknown stitching method: {method}")
    
class Stitcher:
    def __init__(self):
        self.detector = cv2.SIFT_create()

class CylindricalStitcher(Stitcher):
    def stitch(self, image_paths, focal_length=None):
        """ Stitch a list of images together using cylindrical warping.
        args:
            image_paths (list): A list of paths to images to stitch.
            focal_length (float): The focal length of the camera. If None, it will be computed based on the image width and a 60-degree horizontal field of view.
        returns:
            The stitched panorama image.
        """
        images, imagesGray = readImages(image_paths)
        if focal_length is None:
            focal_length = images[0].shape[1]/(2*np.tan(np.pi/6))
        descriptions = computeDescription(imagesGray, self.detector)
        ref_index = len(images)//2
        matchedPtsList = matchDescription(descriptions, ref_index)
        homography = self._computeHomography(matchedPtsList, images, focal_length, ref_index)
        images = [self._warp_cylindrical(img, focal_length) for img in images]
        warped_images, masks = warp(images, homography)
        stitchedImage = softBlend(warped_images, masks)
        return stitchedImage

    def _computeHomography(self, matchedPtsList, images, focal_length, reference_index):
        """ Compute homography matrices (translation only in cylindrical space) for each image to the reference image.
        args:
            matchedPtsList (list): A list of matched keypoints for each image (keypoints in reference image, keypoints in moving image).
            images (list): A list of images.
            focal_length (float): The focal length of the camera.
            reference_index (int): The index of the reference image in the matchedPtsList.
        returns:
            A list of homography matrices for each image to the reference image.
        """
        homography = []
        for i, (ptsRef, ptsMoving) in enumerate(matchedPtsList):
            if i == reference_index:
                homography.append(np.eye(3))
                continue
            ptsRef = transformPlanarToCylindrical(ptsRef, focal_length, images[reference_index].shape[1], images[reference_index].shape[0])
            ptsMoving = transformPlanarToCylindrical(ptsMoving, focal_length, images[i].shape[1], images[i].shape[0])
            # Compute the average horizontal shift in cylindrical coordinates
            shift = np.median(ptsRef - ptsMoving, axis=0)
            H = np.array([[1, 0, shift[0]], [0, 1, shift[1]], [0, 0, 1]]) # translation only in cylindrical space
            homography.append(H)
        return homography
    
    def _warp_cylindrical(self, img, focal_length):
        """
        Warps a planar image onto a cylinder surface
        """
        h, w = img.shape[:2]
        
        x_i, y_i = np.meshgrid(np.arange(w),np.arange(h), indexing='xy')

        coords_planar = transformCylindricalToPlanar(np.stack((x_i.flatten(), y_i.flatten()), axis=-1), focal_length, w, h)
        x_src, y_src = coords_planar[:,0].reshape(h,w), coords_planar[:,1].reshape(h,w)
        warped_img = cv2.remap(img, 
                            x_src.astype(np.float32), 
                            y_src.astype(np.float32), 
                            cv2.INTER_LINEAR)
        return warped_img

class PlanarStitcher(Stitcher):
    def _computeHomography(self, matchedPtsList, reference_index):
        """ Compute homography matrices for each image to the reference image.
        args:
            matchedPtsList (list): A list of matched keypoints for each image (keypoints in reference image, keypoints in moving image).
            reference_index (int): The index of the reference image in the matchedPtsList.
        returns:
            A list of homography matrices for each image to the reference image.
        """
        homography = []
        for i, (ptsRef, ptsMoving) in enumerate(matchedPtsList):
            if i == reference_index:
                homography.append(np.eye(3))
                continue
            H,_ = cv2.findHomography(ptsMoving, ptsRef, cv2.RANSAC) # moving -> reference
            homography.append(H)
        return homography
    
    def stitch(self, image_paths):
        """ Stitch a list of images together using planar homography.
        args:
            image_paths (list): A list of paths to images to stitch.
        returns:
            The stitched panorama image.
        """
        images, imagesGray = readImages(image_paths)
        descriptions = computeDescription(imagesGray, self.detector)
        ref_index = len(images)//2
        matchedPtsList = matchDescription(descriptions, ref_index)
        homography = self._computeHomography(matchedPtsList, ref_index)
        warped_images, masks = warp(images, homography)
        stitchedImage = softBlend(warped_images, masks)
        return stitchedImage

if __name__ == '__main__':
    # Demonstration CLI
    import os
    
    # Calculate paths relative to this script's location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(os.path.dirname(script_dir))
    img_dir = os.path.join(root_dir, 'imgs')
    
    factory = StitcherFactory()
    image_paths = [os.path.join(img_dir, f'{i}.jpg') for i in [1, 2, 3]]
    
    print("Executing Multi-Image Planar Stitching...")
    planar_stitcher = factory.createStitcher('planar')
    planar_result = planar_stitcher.stitch(image_paths)
    planar_out = os.path.join(img_dir, 'planar_panorama_result.jpg')
    cv2.imwrite(planar_out, np.clip(planar_result, 0, 255).astype(np.uint8))
    print(f"Planar result saved to: {planar_out}")
    
    print("\nExecuting Multi-Image Cylindrical Stitching...")
    cyl_stitcher = factory.createStitcher('cylindrical')
    cyl_result = cyl_stitcher.stitch(image_paths)
    cyl_out = os.path.join(img_dir, 'cylindrical_panorama_result.jpg')
    cv2.imwrite(cyl_out, np.clip(cyl_result, 0, 255).astype(np.uint8))
    print(f"Cylindrical result saved to: {cyl_out}")
    
    print("\nProcessing complete.")

