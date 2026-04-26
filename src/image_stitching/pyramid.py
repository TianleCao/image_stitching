import cv2
import numpy as np

class ImagePyramid:
    def __init__(self,levels=5):
        self.levels = levels
    def buildGaussianPyramid(self, image):
        # hi -> lo resolution
        res = [image.astype(np.float32).copy()]
        for _ in range(self.levels):
            im = cv2.pyrDown(res[-1],None)
            res.append(im)
        return res
    def buildLaplacianPyramid(self,gaussianPyramid):
        # hi -> lo resolution
        gaussianPyramid = gaussianPyramid
        res = [gaussianPyramid[-1].copy()]
        n = len(gaussianPyramid)
        for i in range(n-2,-1,-1):
            im = cv2.pyrUp(gaussianPyramid[i+1])
            if im.shape != gaussianPyramid[i].shape:
                h, w = gaussianPyramid[i].shape[:2]
                im = cv2.resize(im,(w,h))
            res.append(gaussianPyramid[i]-im)
        return res[::-1]
    def reconstructFromLaplacianPyramid(self, laplacianPyramid):
        laplacianPyramid = laplacianPyramid[::-1] # lo -> hi resolution
        n = len(laplacianPyramid)
        im = laplacianPyramid[0]
        for i in range(n-1):
            im = cv2.pyrUp(im)
            if im.shape != laplacianPyramid[i+1].shape:
                h, w = laplacianPyramid[i+1].shape[:2]
                im = cv2.resize(im,(w,h))  
            im = im + laplacianPyramid[i+1]
        return im            