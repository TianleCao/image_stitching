import numpy as np
import cv2
from typing import List
    
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


class Stitcher:
    def __init__(self):
        self.detector = cv2.SIFT_create()
    def _read(self,imagePath1, imagePath2):
        self.image1, self.image2 = cv2.imread(imagePath1), cv2.imread(imagePath2)
        self.image1Gray, self.image2Gray = cv2.cvtColor(self.image1, cv2.COLOR_BGR2GRAY), cv2.cvtColor(self.image2, cv2.COLOR_BGR2GRAY)
    def _computeDescription(self, image1, image2):
        pts1, des1 = self.detector.detectAndCompute(image1, None)
        pts2, des2 = self.detector.detectAndCompute(image2, None)
        return pts1, des1, pts2, des2
    def _matchDescription(self, pts1, des1, pts2, des2):
        knnmatcher = cv2.BFMatcher(cv2.NORM_L2)
        matches = knnmatcher.knnMatch(des2,des1,2)
        # ratio check
        good_matches = []
        matchedPts1, matchedPts2 = [], []
        for m in matches:
            if m[0].distance < m[1].distance*0.7:
                good_matches.append(m[0])
                matchedPts1.append(pts1[m[0].trainIdx].pt)
                matchedPts2.append(pts2[m[0].queryIdx].pt)
        return np.array(matchedPts1), np.array(matchedPts2)
    
    def _computeHomography(self, pts1, pts2):
        H,_ = cv2.findHomography(pts2,pts1, cv2.RANSAC) # 2->1
        return H
    
    def _transform(self,pt,H):
        # pt: [2,]
        pt = H @ np.array((pt[0],pt[1],1.0))
        pt = pt[:2]/pt[-1]
        return pt.astype(int)
    
    def _warp(self, image1, image2, H):
        h1, w1 = image1.shape[:2]
        h2, w2 = image2.shape[:2]
        x1, y1  = self._transform((0,0),H)
        x2, y2 = self._transform((w2,0),H)
        x3, y3 = self._transform((0,h2),H)
        x4, y4 = self._transform((w2,h2),H)
        newXMin, newXMax = min([x1,x2,x3,x4,0,w1]), max([x1,x2,x3,x4,0,w1])
        newYMin, newYMax = min([y1,y2,y3,y4,0,h1]), max([y1,y2,y3,y4,0,h1])
        HOffset = np.array([[1.0,0,-newXMin],[0,1.0,-newYMin],[0,0,1.0]])

        image2Warped = cv2.warpPerspective(image2,HOffset@H,(newXMax-newXMin,newYMax-newYMin))
        image1Warped = cv2.warpPerspective(image1,HOffset,(newXMax-newXMin,newYMax-newYMin))
        mask1 = np.ones_like(image1)
        mask1Warped = cv2.warpPerspective(mask1,HOffset,(newXMax-newXMin,newYMax-newYMin))
        return image1Warped, image2Warped, mask1Warped
    
    def blend(self, image1, image2, mask):
        return mask * image1 + (1-mask)*image2
    
    def softBlend(self, image1, image2, mask):
        imagePyramid = ImagePyramid(5)
        gp1 = imagePyramid.buildGaussianPyramid(image1)
        gp2 = imagePyramid.buildGaussianPyramid(image2)
        gpmask = imagePyramid.buildGaussianPyramid(mask)

        lp1 = imagePyramid.buildLaplacianPyramid(gp1)
        lp2 = imagePyramid.buildLaplacianPyramid(gp2)

        blended_lp = []
        for l1, l2, m in zip(lp1, lp2, gpmask):
            blended_lp.append(m*l1+(1-m)*l2)
        return imagePyramid.reconstructFromLaplacianPyramid(blended_lp)
        
    def stitchImage(self, imagePath1, imagePath2):
        self._read(imagePath1, imagePath2)
        descriptions = self._computeDescription(self.image1Gray,self.image2Gray)
        matchedPts1, matchedPts2 = self._matchDescription(*descriptions)
        H = self._computeHomography(matchedPts1,matchedPts2)
        warpedImage1, warpedImage2, mask1 = self._warp(self.image1,self.image2,H)
        stitchedImage = self.softBlend(warpedImage1, warpedImage2, mask1)
        return stitchedImage

if __name__ == '__main__':
    stitcher = Stitcher()
    stitcher.stitchImage('imgs/1.jpg','imgs/2.jpg')