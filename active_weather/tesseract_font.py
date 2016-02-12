import cv2
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN

characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890."
characters = [c for c in characters]
print characters

image = cv2.imread("weather.basic.exp0.tif")

gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
_,bw_image = cv2.threshold(gray_image,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)

pixel_points = np.where(bw_image<255)

# plt.plot(pixel_points[1],pixel_points[0],".")
# plt.show()

X = np.asarray(zip(pixel_points[1],pixel_points[0]))

db = DBSCAN(eps=3, min_samples=4).fit(X)
labels = db.labels_

n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)

clusters = []

height_list = []
width_list = []

print n_clusters_
unique_labels = set(labels)
colors = plt.cm.Spectral(np.linspace(0, 1, len(unique_labels)))

# start by just ordering the clusters so we can match them up to their characters
for k, col in zip(unique_labels, colors):

    class_member_mask = (labels == k)
    xy = X[class_member_mask]

    clusters.append(xy)

clusters.sort(key = lambda c:np.mean(c[:,0]))

for cluster_index,xy in enumerate(clusters):
    min_x,min_y = np.min(xy,axis=0)
    max_x,max_y = np.max(xy,axis=0)



    height = max_y-min_y+1
    width = max_x-min_x +1

    print min_x,min_y,height,width

    height_list.append(height)
    width_list.append(width)

    xy[:,0] -= min_x
    xy[:,1] -= min_y

    clusters[cluster_index] = xy

spacing = 35

overall_width = 10*max(width_list) + spacing*11
overall_height = sum(height_list) + spacing*len(characters)

print overall_height,overall_width

template_image = np.zeros((overall_height,overall_width),np.uint8)
template_image.fill(255)

# cv2.imwrite("/home/ggdhines/fonts.jpg",template_image)

print template_image

print template_image.shape
height_offset = 0

with open("/home/ggdhines/active.basic.exp0.box","w") as f:
    for i,c in enumerate(characters):
        # char_mask = np.zeros((height_list[i],width_list[i]),np.uint8)
        char_mask = np.zeros((height_list[i],width_list[i]),np.uint8)
        char_mask.fill(255)

        # todo - do this better
        for x,y in clusters[i]:
            char_mask[y,x] = 0

        height = height_list[i]
        width = width_list[i]

        print char_mask.shape

        width_offset = spacing
        for column in range(10):
            template_image[height_offset:height_offset+height,width_offset:width_offset+width] = char_mask

            f.write(c)
            f.write(" "+str(width_offset)+" "+str(overall_height - height_offset-height))
            f.write(" "+str(width_offset+width)+" "+str(overall_height - height_offset) + " 0\n")

            width_offset += width + spacing

        height_offset += height + spacing


cv2.imwrite("/home/ggdhines/active.basic.exp0.tiff",template_image)