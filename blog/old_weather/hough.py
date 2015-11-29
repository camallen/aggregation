from skimage.transform import (hough_line, hough_line_peaks,
                               probabilistic_hough_line)
from skimage.feature import canny
from skimage import data
from skimage.data import load
from skimage.color import rgb2gray
import cv2
import numpy as np
import matplotlib.pyplot as plt
from sklearn.neighbors import KDTree
import math

def deter(a,b,c,d):
    return a*d - c*b

def does_intersect(l1,l2):
    (x1,y1),(x2,y2) = l1
    (x3,y3),(x4,y4) = l2

    l1_lower_x = min(x1,x2)
    l1_upper_x = max(x1,x2)
    l2_lower_x = min(x3,x4)
    l2_upper_x = max(x3,x4)

    l1_lower_y = min(y1,y2)
    l1_upper_y = max(y1,y2)
    l2_lower_y = min(y3,y4)
    l2_upper_y = max(y3,y4)

    x_inter,y_inter = intersection(l1,l2)
    valid_x = (l1_lower_x <= x_inter) and (l2_lower_x <= x_inter) and (x_inter <= l1_upper_x) and (x_inter <= l2_upper_x)
    valid_y = (l1_lower_y <= y_inter) and (l2_lower_y <= y_inter) and (y_inter <= l1_upper_y) and (y_inter <= l2_upper_y)

    return valid_x and valid_y

def intersection(h_line,v_line):
    (x1,y1),(x2,y2) = h_line
    (x3,y3),(x4,y4) = v_line

    d1 = deter(x1,y1,x2,y2)
    d2 = deter(x1,1,x2,1)
    d3 = deter(x3,y3,x4,y4)
    d4 = deter(x3,1,x4,1)

    D1 = deter(d1,d2,d3,d4)

    d5 = deter(y1,1,y2,1)
    d6 = deter(y3,1,y4,1)

    D2 = deter(d1,d5,d3,d6)

    d7 = deter(x3,1,x4,1)
    d8 = deter(y3,1,y4,1)

    D3 = deter(d2,d5,d7,d8)

    intersect_x = D1/float(D3)
    intersect_y = D2/float(D3)

    return intersect_x,intersect_y

def multi_intersection(h_line,v_line):
    for h in h_line:
        for v in v_line:
            if does_intersect(h,v):
                x,y = intersection(h,v)
                print h
                print v
                print
                plt.plot(x,y,"o",color ="green")

def hesse_line(line_seg):
    """
    use if we want to cluster based on Hesse normal form - but want to retain the original values
    :param line_segment:
    :return:
    """


    (x1,y1),(x2,y2) = line_seg

    # x2 += random.uniform(-0.0001,0.0001)
    # x1 += random.uniform(-0.0001,0.0001)

    dist = (x2*y1-y2*x1)/math.sqrt((y2-y1)**2+(x2-x1)**2)

    try:
        tan_theta = math.fabs(y1-y2)/math.fabs(x1-x2)
        theta = math.atan(tan_theta)
    except ZeroDivisionError:
        theta = math.pi/2.

    return dist,theta


# image = data.camera()
image = load("/home/ggdhines/Databases/old_weather/test_cases/Bear-AG-29-1939-0191.JPG")
# image = rgb2gray(image)
# aws s3 ls s3://zooniverse-static/old-weather-2015/Distant_Seas/Navy/Bear_AG-29_/Bear-AG-29-1939/
# img = cv2.imread("/home/ggdhines/Databases/old_weather/test_cases/Bear-AG-29-1939-0191.JPG",0)

gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
edges = cv2.Canny(gray,25,150,apertureSize = 3)
# cv2.imwrite('/home/ggdhines/1.jpg',edges)

lines = probabilistic_hough_line(edges, threshold=5, line_length=50,line_gap=0)
fig, ax1 = plt.subplots(1, 1)
fig.set_size_inches(52,78)
# ax1.imshow(image)

horiz_list = []
horiz_intercepts = []

vert_list = []
vert_intercepts = []

big_lower_x = 559
big_upper_x = 3245
big_lower_y = 1292
big_upper_y = 2014

for line in lines:
    p0, p1 = line
    X = p0[0],p1[0]
    Y = p0[1],p1[1]

    if (min(X) >= 559) and (max(X) <= 3245) and (min(Y) >= 1292) and (max(Y) <= 2014):
        d,t = hesse_line(line)
        if math.fabs(t) <= 0.1:
            horiz_list.append(line)
            # hesse_list.append(hesse_line(line))

            m = (Y[0]-Y[1])/float(X[0]-X[1])
            b = Y[0]-m*X[0]
            horiz_intercepts.append(b)
        else:
            vert_list.append(line)
            m = (X[0]-X[1])/float(Y[0]-Y[1])
            b = X[0]-m*Y[0]
            vert_intercepts.append(b)


        # ax1.plot(X, Y,color="red")
    # else:
    #     print min(X)
    # print hesse_line(line)

from sklearn.cluster import DBSCAN

def fil_gaps(line_segments,horiz=True):
    first_pt = line_segments[0][0]
    last_pt = line_segments[-1][1]

    for l_index in range(len(line_segments)-1):
        l1 = line_segments[l_index]
        l2 = line_segments[l_index+1]

        line_segments.append((l1[1],l2[0]))

    return line_segments


def analysis(lines,intercepts,horiz=True):
    retval = []
    # d_list,t_list = zip(*hesse_list)
    min_dist = min(intercepts)
    max_dist = max(intercepts)
    # min_theta = min(t_list)
    # max_theta = max(t_list)

    normalized_d = [[(d-min_dist)/float(max_dist-min_dist),] for d in intercepts]
    # normalized_t = [(t-min_theta)/float(max_theta-min_theta) for t in t_list]
    # print normalized_d
    # print normalized_t

    X = np.asarray([[i,] for i in intercepts])
    # print X
    db = DBSCAN(eps=15, min_samples=2).fit(X)
    core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
    core_samples_mask[db.core_sample_indices_] = True
    labels = db.labels_

    unique_labels = set(labels)
    colors = plt.cm.Spectral(np.linspace(0, 1, len(unique_labels)))

    for k, col in zip(unique_labels, colors):
        if k == -1:
            # Black used for noise.
            col = 'k'
            continue

        class_indices = [i for (i,l) in enumerate(labels) if l == k]
        # print class_indices
        print len(class_indices)

        multiline = []

        for i in class_indices:
            line = lines[i]
            p0, p1 = line
            X = p0[0],p1[0]
            Y = p0[1],p1[1]
            # ax1.plot(X, Y,color=col)

            # if horiz, sort by increasing X values
            if horiz:
                if p0[0] < p1[0]:
                    multiline.append([list(p0),list(p1)])
                else:

                    multiline.append([list(p1),list(p0)])
            else:
                # sort y increasing Y values
                if p0[1] < p1[1]:
                    multiline.append([list(p0),list(p1)])
                else:
                    multiline.append([list(p1),list(p0)])
        # print multiline
        # multiline.sort(key = lambda x:x[0][0])

        lb = [[-float("inf"),float("inf")],[float("inf"),float("inf")]]
        # lb.extend(multiline[0])
        # lb.sort(key = lambda x:x[0])
        ub = [[-float("inf"),-float("inf")],[float("inf"),-float("inf")]]
        # ub.extend(multiline[0])
        # ub.sort(key = lambda x:x[0])

        print "^^^^"
        if horiz:
            for ii,(starting_pt,ending_pt) in enumerate(multiline):
                print starting_pt,ending_pt
                if ii == 4:
                    break
                m = (ending_pt[1]-starting_pt[1])/float(ending_pt[0]-starting_pt[0])
                b = starting_pt[1]-m*starting_pt[0]

                inserted_end_point = False
                # start at the end point so we can insert element without messing order
                for pt_index in range(len(lb)-1,-1,-1):
                    # haven't gone far enough - keep searching
                    if lb[pt_index][0] > ending_pt[0]:
                        continue
                    # gone just far enough -
                    elif lb[pt_index][0] == ending_pt[0]:
                        lb[pt_index][1] = min(ending_pt[1],lb[pt_index][1])
                        inserted_end_point = True
                    # have we gone too far?
                    elif lb[pt_index][0] < starting_pt[0]:
                        lb.insert(pt_index+1,starting_pt)
                        break
                    elif lb[pt_index][0] == starting_pt[0]:
                        lb[pt_index][1] = min(starting_pt[1],lb[pt_index][1])
                        break
                    else:
                        assert starting_pt[0] < lb[pt_index][0]
                        assert lb[pt_index][0] < ending_pt[0]

                        # if we hadn't already inserted the end point
                        if not inserted_end_point:
                            lb.insert(pt_index+1,ending_pt)
                            inserted_end_point = True

                        # according to our line, what should y(x) be for lb[pt_index][0]
                        y = m*lb[pt_index][0]+b
                        lb[pt_index][1] = min(y,lb[pt_index][1])
                print lb
                # repeat for upper bound
                inserted_end_point = False
                # start at the end point so we can insert element without messing order
                for pt_index in range(len(ub)-1,-1,-1):
                    # haven't gone far enough - keep searching
                    if ub[pt_index][0] > ending_pt[0]:
                        continue
                    # gone just far enough -
                    elif ub[pt_index][0] == ending_pt[0]:
                        ub[pt_index][1] = max(ending_pt[1],ub[pt_index][1])
                        inserted_end_point = True
                    # have we gone too far?
                    elif ub[pt_index][0] < starting_pt[0]:
                        ub.insert(pt_index+1,starting_pt)
                        break
                    elif ub[pt_index][0] == starting_pt[0]:
                        ub[pt_index][1] = max(starting_pt[1],ub[pt_index][1])
                        break
                    else:
                        assert starting_pt[0] < ub[pt_index][0]
                        assert ub[pt_index][0] < ending_pt[0]

                        # if we hadn't already inserted the end point
                        if not inserted_end_point:
                            ub.insert(pt_index+1,ending_pt)
                            inserted_end_point = True

                        # according to our line, what should y(x) be for lb[pt_index][0]
                        y = m*ub[pt_index][0]+b
                        ub[pt_index][1] = max(y,ub[pt_index][1])
                print ub

        X,Y = zip(*lb)
        plt.plot(X[1:-1],Y[1:-1],"-",color="red")
        X,Y = zip(*ub)
        plt.plot(X[1:-1],Y[1:-1],"-",color="blue")


        # for l_index,line in enumerate(multiline):
        #     for l2_index,line_2 in list(enumerate(multiline)):
        #         if l_index == l2_index:
        #             continue
        #         # if the starting point of the next line segment is after the ending point of the current line segment
        #         # stop
        #         if horiz:
        #             try:
        #                 if does_intersect(line,line_2):
        #                     print "ii"
        #                     continue
        #             except ZeroDivisionError:
        #                 continue
        #             # check the case where line 2 is first - so line 1 must start before line 2 ends
        #             opt1 = (line_2[0][0] < line[0][0]) and (line[1][0] > line_2[0][0])
        #             # or line
        #             opt2 = (line_2[0][0] < line[0][0]) and (line[0][0] < line_2[1][0])
        #
        #
        #             print "^^"
        #             print line
        #             print line_2
        #             print opt1,opt2
        #             if not(opt1 or opt2):
        #                 continue
        #             # print "^^"
        #
        #
        #             # if line_2[0][0] > line[1][0]:
        #             #     break
        #             # print (line_2[0][1] , line[0][1]) , (line_2[1][1] , line[1][1])
        #
        #             if (line_2[0][1] > line[0][1]) and (line_2[1][1] > line[1][1]):
        #                 ub.add(l2_index)
        #                 lb.add(l_index)
        #                 print "a"
        #             elif (line_2[0][1] < line[0][1]) and (line_2[1][1] < line[1][1]):
        #                 lb.add(l2_index)
        #                 ub.add(l_index)
        #                 # print "b"
        #         else:
        #             try:
        #                 if does_intersect(line,line_2):
        #                     continue
        #             except ZeroDivisionError:
        #                 continue
        #             # if line_2[0][1] > line[1][1]:
        #             #     break
        #
        #             opt1 = (line_2[0][1] < line[0][1]) and (line[1][1] > line_2[0][1])
        #             # or line
        #             opt2 = (line_2[0][1] < line[0][1]) and (line[0][1] < line_2[1][1])
        #
        #             if not(opt1 or opt2):
        #                 continue
        #
        #             if line_2[0][0] > line[0][0]:
        #                 assert line_2[-1][0] > line[-1][0]
        #                 ub.add(l2_index)
        #                 lb.add(l_index)
        #             elif line_2[0][0] < line[0][0]:
        #                 assert line_2[-1][0] <line[-1][0]
        #                 lb.add(l2_index)
        #                 ub.add(l_index)
        # print [i for i in range(len(multiline)) if (i not in lb) and (i not in ub)]
        # lb = sorted(list(lb))
        # ub = sorted(list(ub))
        #
        # for i in range(len(multiline)):
        #     if (i not in lb) and (i not in ub):
        #         for ii in range(len(ub)-1):
        #             l_index = ub[ii]
        #             l2_index = ub[ii+1]
        #             p1 = multiline[l_index][1]
        #             p2 = multiline[l2_index][0]
        #             try:
        #                 if does_intersect(multiline[i],(p1,p2)):
        #                     ub.append(i)
        #             except ZeroDivisionError:
        #                 pass
        #         for ii in range(len(lb)-1):
        #             l_index = lb[ii]
        #             l2_index = lb[ii+1]
        #             p1 = multiline[l_index][1]
        #             p2 = multiline[l2_index][0]
        #             try:
        #                 if does_intersect(multiline[i],(p1,p2)):
        #                     lb.append(i)
        #             except ZeroDivisionError:
        #                 pass
        #
        # lb = sorted(list(set(lb)))
        # ub = sorted(list(set(ub)))
        # lower_lines = []
        # for ii in range(len(lb)):
        #     l_index = lb[ii]
        #     # l2_index = lb[ii+1]
        #     # X = multiline[l_index][1][0],multiline[l2_index][0][0]
        #     # Y = multiline[l_index][1][1],multiline[l2_index][0][1]
        #     # ax1.plot(X, Y,color=col)
        #     # lower_lines.append(((X[0],Y[0]),(X[1],Y[1])))
        #     lower_lines.append(multiline[l_index])
        #
        # # if lower_lines != []:
        # #     lower_lines = fil_gaps(lower_lines)
        # for (x1,y1),(x2,y2) in lower_lines:
        #     ax1.plot((x1,x2),(y1,y2),color="red")
        #     pass
        #
        # upper_lines = []
        #
        # for ii in range(len(ub)-1):
        #     l_index = ub[ii]
        #     # l2_index = ub[ii+1]
        #     # X = multiline[l_index][1][0],multiline[l2_index][0][0]
        #     # Y = multiline[l_index][1][1],multiline[l2_index][0][1]
        #     # ax1.plot(X, Y,color=col)
        #     # upper_lines.append(((X[0],Y[0]),(X[1],Y[1])))
        #     upper_lines.append(multiline[l_index])
        #
        # # if upper_lines != []:
        # #     upper_lines = fil_gaps(upper_lines)
        #
        # for (x1,y1),(x2,y2) in upper_lines:
        #     ax1.plot((x1,x2),(y1,y2),color="green")
        #     pass
        #
        # if lower_lines == [] and upper_lines == []:
        #     for ii in range(len(multiline)-1):
        #         X = multiline[ii][1][0],multiline[ii+1][0][0]
        #         Y = multiline[ii][1][1],multiline[ii+1][0][1]
        #         ax1.plot(X,Y,color="blue")
        #     retval.append((multiline,multiline))
        # else:
        #     # assert lower_lines != []
        #     # assert upper_lines != []
        #     retval.append((lower_lines,upper_lines))

    # if horiz:
    #     retval.sort(key = lambda x:x[0][0][0])
    # else:
    #     retval.sort(key = lambda x:x[1][0][1])
    return retval


h_lines = analysis(horiz_list,horiz_intercepts,horiz=True)
# assert False
# v_lines = analysis(vert_list,vert_intercepts,horiz=False)



# ax1.set_title('Probabilistic Hough')
ax1.set_axis_off()
ax1.set_adjustable('box-forced')


# for row_index in range(len(h_lines)-1):
#     for column_index in range(len(v_lines)-1):
#         # start with the top left
#         lower_horiz = h_lines[row_index][1]
#         lower_vert = v_lines[column_index][1]
#         # print lower_horiz
#         # print lower_vert
#         multi_intersection(lower_horiz,lower_vert)
#         break
#     break
plt.savefig("/home/ggdhines/Databases/example.jpg",bbox_inches='tight', pad_inches=0,dpi=72)
plt.close()