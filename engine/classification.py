__author__ = 'greg'
import clustering
import os
import re
import matplotlib.pyplot as plt
import networkx as nx
import itertools
from copy import deepcopy
import abc
import json
import csv
import math

def findsubsets(S,m):
    return set(itertools.combinations(S, m))

class Classification:
    def __init__(self):
        # ,clustering_alg=None
        # assert isinstance(project,ouroboros_api.OuroborosAPI)

        # if clustering_alg is not None:
        #     assert isinstance(clustering_alg,clustering.Cluster)
        # self.cluster_alg = clustering_alg

        current_directory = os.getcwd()
        slash_indices = [m.start() for m in re.finditer('/', current_directory)]

        self.species = {"lobate":0,"larvaceanhouse":0,"salp":0,"thalasso":0,"doliolidwithouttail":0,"rocketthimble":1,"rockettriangle":1,"siphocorncob":1,"siphotwocups":1,"doliolidwithtail":1,"cydippid":2,"solmaris":2,"medusafourtentacles":2,"medusamorethanfourtentacles":2,"medusagoblet":2,"beroida":3,"cestida":3,"radiolariancolonies":3,"larvacean":3,"arrowworm":3,"shrimp":4,"polychaeteworm":4,"copepod":4}
        self.candidates = self.species.keys()

    @abc.abstractmethod
    def __task_aggregation__(self,classifications,task_id,aggregations):
        return []

    # def __add_new_results__(self,current_aggregations,keyword_list,new_aggregations,maps_to_list=()):
    #     """
    #     start by traversing the current_aggregations as a dictionary until we find where we should insert
    #     the new results - if along the way we find that a keyword isn't in the aggregation dictionary
    #     were we expected it - just add it (mapping to either an empty dictionary or empty list)
    #     since the vast majority of key words will map to dictionaries, seems easiest to just the ones
    #     that don't
    #     """
    #     assert isinstance(current_aggregations,dict)
    #     # think of it a bit like a tree traversal - so we'll call where we currently are
    #     # the current_node
    #     current_node = current_aggregations
    #     for ii,keyword in enumerate(keyword_list):
    #         assert isinstance(current_node,dict)
    #         if keyword not in current_node:
    #             if keyword in maps_to_list:
    #                 current_node[keyword] = []
    #             else:
    #                 current_node[keyword] = {}
    #
    #         # don't go all the way done - makes assignment a lot easier
    #         if ii < (len(keyword_list)-1):
    #             current_node = current_node[keyword]
    #
    #     # we have finally reached where will we actually insert the new results
    #     # if we are at a list, append
    #     if isinstance(current_node[keyword],list):
    #         current_node[keyword].append(new_aggregations)
    #     else:
    #         current_node[keyword] = new_aggregations
    #
    #     return current_aggregations

    def __subtask_classification__(self,task_id,classification_tasks,raw_classifications,clustering_results,aggregations):
        """
        call this when at least one of the tools associated with task_id has a follow up question
        :param task_id:
        :param classification_tasks:
        :param raw_classifications:
        :param clustering_results:
        :param aggregations:
        :return:
        """

        # go through the tools which actually have the followup questions
        for tool in classification_tasks[task_id]:

            # now go through the individual followup questions
            for followup_question_index in classification_tasks[task_id][tool]:
                global_index = str(task_id)+"_" +str(tool)+"_"+str(followup_question_index)

                followup_classification = {}
                shapes_per_cluster = {}

                # go through each cluster and find the corresponding raw classifications
                for subject_id in clustering_results:
                    # print subject_id
                    if subject_id == "param":
                        continue

                    # has anyone done this task for this subject?
                    if task_id in clustering_results[subject_id]:
                        # look at all the shape markings used and see if any correspond to the relevant type
                        # todo - probably a more efficient way to do this
                        # since we only store the shape associated with each cluster
                        for shape_clusters in clustering_results[subject_id][task_id]:
                            shape = shape_clusters.split(" ")[0]
                            if shape == "param":
                                continue

                            # for each cluster, find users who might have a relevant marking - and see if the tool
                            # type matches
                            for cluster_index,cluster in clustering_results[subject_id][task_id][shape + " clusters"].items():
                                if cluster_index in ["param","all_users"]:
                                    continue

                                # polygons and rectangles will pass cluster membership back as indices
                                # ints => we can't case tuples
                                if isinstance(cluster["cluster members"][0],int):
                                    user_identifiers = zip(cluster["cluster members"],cluster["users"])
                                else:
                                    user_identifiers = zip([tuple(x) for x in cluster["cluster members"]],cluster["users"])
                                ballots = []

                                for user_identifiers,tool_used in zip(user_identifiers,cluster["tools"]):
                                    # did the user use the relevant tool - doesn't matter if most people
                                    # used another tool
                                    if tool_used == tool:
                                        # print raw_classifications[global_index].keys()
                                        followup_answer = raw_classifications[global_index][subject_id][user_identifiers]
                                        u = user_identifiers[1]
                                        ballots.append((u,followup_answer))
                                followup_classification[(subject_id,cluster_index)] = deepcopy(ballots)
                                shapes_per_cluster[(subject_id,cluster_index)] = shape

                print "follow up aggregaton"
                followup_results = self.__task_aggregation__(followup_classification,global_index,{})
                assert isinstance(followup_results,dict)

                for subject_id,cluster_index in followup_results:
                    shape =  shapes_per_cluster[(subject_id,cluster_index)]
                    # keyword_list = [subject_id,task_id,shape+ " clusters",cluster_index,"followup_questions"]
                    new_results = followup_results[(subject_id,cluster_index)]
                    new_agg = {subject_id: {task_id: {shape + " clusters": {cluster_index: {"followup_questions": [new_results]}}}}}

                    # merge the new results into the existing one
                    aggregations = self.__merge_results__(aggregations,new_agg)

                    # maps_to_list = ["followup_questions"]
                    #
                    # aggregations = self.__add_new_results__(aggregations,keyword_list,new_results,maps_to_list)

                    # if subject_id not in aggregations:
                    #     aggregations[subject_id] = {"param":"task_id"}
                    # if task_id not in aggregations[subject_id]:
                    #     aggregations[subject_id][task_id] = {"param":"clusters"}
                    # if (shape+ " clusters") not in aggregations[subject_id][task_id]:
                    #     aggregations[subject_id][task_id][shape+ " clusters"] = {}
                    # # this part is probably redundant
                    #
                    # if cluster_index not in aggregations[subject_id][task_id][shape+ " clusters"]:
                    #     aggregations[subject_id][task_id][shape+ " clusters"][cluster_index] = {}
                    #
                    # # todo - not compliant
                    # if "followup_questions" not in aggregations[subject_id][task_id][shape+ " clusters"][cluster_index]:
                    #     aggregations[subject_id][task_id][shape+ " clusters"][cluster_index]["followup_questions"] = []
                    #
                    # aggregations[subject_id][task_id][shape+ " clusters"][cluster_index]["followup_questions"].append(followup_results[(subject_id,cluster_index)])

        return aggregations

    def __existence_classification__(self,task_id,shape,clustering_results,aggregations,gold_standard_clustering=([],[])):
        """
        classify whether clusters are true or false positives
        i.e. whether each cluster corresponds to something which actually exists

        return in json format so we can merge with other results
        :return:
        """


        mapped_gold_standard = {}
        assert isinstance(clustering_results,dict)
        # aggregations = {}

        # raw_classifications and clustering_results have different hierarchy orderings- raw_classifications
        # is better for processing data and clustering_results is better for showing the end result
        # technically we only need to look at the data from clustering_results right now but its
        # hierarchy is really inefficient so use raw_classifications to help

        # each shape is done independently

        # set - so if multiple tools create the same shape - we only do that shape once
        # for shape in set(marking_tasks[task_id]):


        # pretentious name but basically whether each person who has seen a subject thinks it is a true
        # positive or not
        existence_classification = {"param":"subject_id"}

        global_cluster_index = 0
        # clusters_per_subject = []

        # look at the individual points in the cluster
        for subject_id in clustering_results.keys():
            if subject_id == "param":
                continue

            # gold standard pts may not match up perfectly with the given clusters -
            # for example, we could have a gold penguin at 10,10 but the users' cluster
            # is centered at 10.1,9.8 - same penguin though
            # so as we go through the clusters, we need to see which ones match up more closely
            # with the gold standard
            if subject_id in gold_standard_clustering[0]:
                # closest cluster and distance
                gold_to_cluster = {pt:(None,float("inf")) for pt in gold_standard_clustering[0][subject_id]}
            else:
                gold_to_cluster = None


            # clusters_per_subject.append([])

            # # in either case probably an empty image
            # if subject_id not in clustering_results:
            #     continue
            # if task_id not in clustering_results[subject_id]:
            #     continue

            if (shape+ " clusters") not in clustering_results[subject_id][task_id]:
                # if none of the relevant markings were made on this subject, skip it
                continue

            for local_cluster_index in clustering_results[subject_id][task_id][shape+ " clusters"]:
                if (local_cluster_index == "param") or (local_cluster_index == "all_users"):
                    continue

                # extract the users who marked this cluster
                cluster = clustering_results[subject_id][task_id][shape+ " clusters"][local_cluster_index]

                # is this user cluster close to any gold standard pt?
                if subject_id in gold_standard_clustering[0]:
                    x,y = cluster["center"]
                    for (gold_x,gold_y) in gold_to_cluster:
                        dist = math.sqrt((x-gold_x)**2+(y-gold_y)**2)
                        if dist < gold_to_cluster[(gold_x,gold_y)][1]:
                            gold_to_cluster[(gold_x,gold_y)] = local_cluster_index,dist

                # now repeat for negative gold standards
                if subject_id in gold_standard_clustering[1]:
                    x,y = cluster["center"]
                    min_dist = float("inf")
                    closest= None
                    for x2,y2 in gold_standard_clustering[1][subject_id]:
                        dist = math.sqrt((x-x2)**2+(y-y2)**2)
                        if dist < min_dist:
                            min_dist = min(dist,min_dist)
                            closest = (x2,y2)
                    if min_dist == 0.:
                        assert (x,y) == closest
                        mapped_gold_standard[(subject_id,local_cluster_index)] = 0

                users = cluster["users"]

                ballots = []

                # todo - the 15 hard coded value - might want to change that at some point
                for u in clustering_results[subject_id][task_id][shape+ " clusters"]["all_users"]:
                    if u in users:
                        ballots.append((u,1))
                    else:
                        ballots.append((u,0))

                existence_classification[(subject_id,local_cluster_index)] = ballots
                # clusters_per_subject[-1].append(global_cluster_index)
                global_cluster_index += 1

            # note we don't care about why a cluster corresponds to a gold standard pt - that is
            # it could be really close to given gold standards - the point is that it is close
            # to at least one of them
            if gold_to_cluster is not None:
                for (local_cluster_index,dist) in gold_to_cluster.values():
                    # arbitrary threshold but seems reasonable
                    if dist < 1:
                        mapped_gold_standard[(subject_id,local_cluster_index)] = 1

        existence_results = self.__task_aggregation__(existence_classification,task_id,{})#,mapped_gold_standard)
        assert isinstance(existence_results,dict)

        for subject_id,cluster_index in existence_results:
            new_results = existence_results[(subject_id,cluster_index)][task_id]
            new_agg = {subject_id: {task_id: {shape + " clusters": {cluster_index: {"existence": new_results}}}}}
            aggregations = self.__merge_results__(aggregations,new_agg)

            # if subject_id not in aggregations:
            #     aggregations[subject_id] = {}
            # if task_id not in aggregations[subject_id]:
            #     aggregations[subject_id][task_id] = {}
            # if (shape + " clusters") not in aggregations[subject_id][task_id]:
            #     aggregations[subject_id][task_id][shape+ " clusters"] = {}
            # # this part is probably redundant
            # if cluster_index not in aggregations[subject_id][task_id][shape+ " clusters"]:
            #     aggregations[subject_id][task_id][shape+ " clusters"][cluster_index] = {}
            #
            # aggregations[subject_id][task_id][shape+ " clusters"][cluster_index]["existence"] = existence_results[(subject_id,cluster_index)]

        return aggregations

    def __tool_classification__(self,task_id,shape,raw_classifications,clustering_results,aggregations):
        """
        if multiple tools can make the same shape - we need to decide which tool actually corresponds to this cluster
        for example if both the adult penguin and chick penguin make a pt - then for a given point we need to decide
        if it corresponds to an adult or chick
        :param task_id:
        :param classification_tasks:
        :param raw_classifications:
        :param clustering_results:
        :return:
        """

        if clustering_results == {"param":"subject_id"}:
            print "warning - empty classifications"
            return {}

        # aggregations = {}

        # todo - we should skip such cases but they should also be pretty rare - double check
        if task_id not in raw_classifications:
            return {}

        # only go through the "uncertain" shapes
        tool_classifications = {}

        for subject_id in raw_classifications[task_id][shape]:
            # look at the individual points in the cluster

            # this should only happen if there were badly formed markings
            if raw_classifications[task_id][shape][subject_id] == {}:
                continue

            # in either case probably an empty image
            if subject_id not in clustering_results:
                continue
            if task_id not in clustering_results[subject_id]:
                continue

            for cluster_index in clustering_results[subject_id][task_id][shape+ " clusters"]:
                if (cluster_index == "param") or (cluster_index == "all_users"):
                    continue

                cluster = clustering_results[subject_id][task_id][shape+ " clusters"][cluster_index]
                pts = cluster["cluster members"]
                users = cluster["users"]
                # users = clustering_results[subject_id][task_id][shape][subject_id]["users"]

                # in this case, we want to "vote" on the tools
                ballots = []
                for (p,user) in zip(pts,users):
                    try:
                        tool_index = raw_classifications[task_id][shape][subject_id][(tuple(p),user)]
                    except KeyError:
                        print "===----"
                        print cluster
                        print raw_classifications[task_id][shape][subject_id].keys()
                        print (tuple(p),user)
                        raise

                    ballots.append((user,tool_index))

                tool_classifications[(subject_id,cluster_index)] = ballots

        # classify
        print "tool results classification"
        tool_results = self.__task_aggregation__(tool_classifications,task_id,{})
        assert isinstance(tool_results,dict)

        for subject_id,cluster_index in tool_results:
            new_results = tool_results[(subject_id,cluster_index)][task_id]
            new_agg = {subject_id: {task_id: {shape + " clusters": {cluster_index: {"tool_classification": new_results}}}}}
            aggregations = self.__merge_results__(aggregations,new_agg)

            # if subject_id not in aggregations:
            #     aggregations[subject_id] = {"param":"task_id"}
            # if task_id not in aggregations[subject_id]:
            #     aggregations[subject_id][task_id] = {"param":"clusters"}
            # if (shape+ " clusters") not in aggregations[subject_id][task_id]:
            #     aggregations[subject_id][task_id][shape+ " clusters"] = {}
            # # this part is probably redundant
            # if cluster_index not in aggregations[subject_id][task_id][shape+ " clusters"]:
            #     aggregations[subject_id][task_id][shape+ " clusters"][cluster_index] = {}
            #
            # aggregations[subject_id][task_id][shape+ " clusters"][cluster_index]["tool_classification"] = tool_results[(subject_id,cluster_index)]

        return aggregations

    def __aggregate__(self,raw_classifications,workflow,clustering_results=None,gold_standard_clustering=([],[])):
        # use the first subject_id to find out which tasks we are aggregating the classifications for
        aggregations = {}
        classification_tasks,marking_tasks = workflow

        # start by doing existence classifications for markings
        # i.e. determining whether a cluster is a true positive or false positive
        # also do tool type classification for tasks where more than one tool
        # can create the same shape
        # followup questions will be dealt as classification tasks
        # note that polygons and rectangles (since they are basically a type of polygon)
        # handle some of this themselves
        for task_id in marking_tasks:
            for shape in set(marking_tasks[task_id]):
                if shape not in ["polygon","rectangle","text"]:
                    aggregations = self.__existence_classification__(task_id,shape,clustering_results,aggregations,gold_standard_clustering)
                    # aggregations = self.__merge_results__(aggregations,exist_results)

                    # can more than one tool create this shape?
                    if sum([1 for s in marking_tasks[task_id] if s == shape]) > 1:
                        aggregations = self.__tool_classification__(task_id,shape,raw_classifications,clustering_results,aggregations)
                        # merge the tool results into the overall results
                        # aggregations = self.__merge_results__(aggregations,tool_results)

                    # # now merge the results
                    # for subject_id in results:
                    #     if subject_id not in aggregations:
                    #         aggregations[subject_id] = {}
                    #     # we have results from other tasks, so we need to merge in the results
                    #     assert isinstance(results[subject_id],dict)
                    #     aggregations[subject_id] = self.__merge_results__(aggregations[subject_id],results[subject_id])

        # now go through the normal classification aggregation stuff
        # which can include follow up questions
        for task_id in classification_tasks:
            # print task_id
            if task_id == "param":
                continue

            print "classifying task " + str(task_id)

            # task_results = {}
            # just a normal classification question
            if isinstance(classification_tasks[task_id],bool):
                # did anyone actually do this classification?
                if task_id in raw_classifications:
                    print raw_classifications[task_id]
                    aggregations = self.__task_aggregation__(raw_classifications[task_id],task_id,aggregations)

                    # aggregations = self.__merge_results__(aggregations,classification_results)

                # # now merge the results
                #     for subject_id in results:
                #         if subject_id not in aggregations:
                #             aggregations[subject_id] = {}
                #         # we have results from other tasks, so we need to merge in the results
                #         assert isinstance(results[subject_id],dict)
                #         aggregations[subject_id] = self.__merge_results__(aggregations[subject_id],results[subject_id])
            else:
                # we have a follow up classification
                aggregations = self.__subtask_classification__(task_id,classification_tasks,raw_classifications,clustering_results,aggregations)
                # aggregations = self.__merge_results__(aggregations,subtask_results)
                # print subtask_results
                # assert False

            # if isinstance(classification_tasks[task_id],bool):
            #     # we have a basic classification task
            #     # todo - double check if this is right
            #     if task_id in raw_classifications:
            #         temp_results = self.__task_aggregation__(raw_classifications[task_id])
            #         # convert everything into a dict and add the the task id
            #
            #         for subject_id in temp_results:
            #             task_results[subject_id] = {task_id:temp_results[subject_id]}
            # else:
            #     # we have classifications associated with markings
            #     # make sure we have clustering results associated with these classifications
            #     assert clustering_results is not None
            #
            #     # not every marking will need existence or tool classification
            #     # polygons and rectangles can take care of that themselves
            #     # however, they might have follow up questions
            #     print classification_tasks[task_id]
            #
            #
            #     # we have to first decide which cluster is a "true positive" and which is a "false positive"
            #     # so a question of whether or not people marked it - regardless of whether they marked it as the
            #     # correct "type"
            #     existence_results = self.__existence_classification__(task_id,marking_tasks,clustering_results,gold_standard_clustering)
            #
            #
            #     # now decide what type each cluster is
            #     # note that this step does not care whether a cluster is a false positive or not (i.e. the results
            #     # from the previous step are not taken into account)
            #     tool_results = self.__tool_classification__(task_id,classification_tasks,raw_classifications,clustering_results)
            #
            #     task_results = self.__merge_results__(existence_results,tool_results)
            #
            #     # are there any subtasks associated with this task/marking?
            #     if "subtask" in classification_tasks[task_id]:
            #         subtask_results = self.__subtask_classification__(task_id,classification_tasks,raw_classifications,clustering_results)
            #         task_results = self.__merge_results__(task_results,subtask_results)

            #assert isinstance(task_results,dict)

                # aggregations[subject_id][task_id] = task_results[subject_id]



        return aggregations

    def __merge_results__(self,r1,r2):
        """
        if we have json results from two different steps of the aggregation process - merge them
        :param r1:
        :param r2:
        :return:
        """
        assert isinstance(r1,dict)
        assert isinstance(r2,dict)

        for kw in r2:
            try:
                if kw not in r1:
                    r1[kw] = r2[kw]
                elif r1[kw] != r2[kw]:
                    if isinstance(r1[kw],list):
                        assert isinstance(r2[kw],list)
                        r1[kw].extend(r2[kw])
                    else:
                        r1[kw] = self.__merge_results__(r1[kw],r2[kw])
            except TypeError:
                print "==--"
                print r1
                print r2
                print kw
                raise
        return r1


class VoteCount(Classification):
    def __init__(self,param_dict):
        Classification.__init__(self)

    def __task_aggregation__(self,raw_classifications,task_id,aggregations):
        """
        question_id is not None if and only if the classification relates to a marking
        :param subject_ids:
        :param task_id:
        :param question_id:
        :param gold_standard:
        :return:
        """
        # results = {}

        for subject_id in raw_classifications:
            vote_counts = {}
            if subject_id == "param":
                continue
            # print raw_classifications[subject_id]
            for user,ballot in raw_classifications[subject_id]:
                if ballot is None:
                    continue
                # in which case only one vote is allowed
                if isinstance(ballot,int):
                    if ballot in vote_counts:
                        vote_counts[ballot] += 1
                    else:
                        vote_counts[ballot] = 1
                # in which case multiple votes are allowed
                else:
                    for vote in ballot:
                        if vote in vote_counts:
                            vote_counts[vote] += 1
                        else:
                            vote_counts[vote] = 1
            # convert to percentages
            percentages = {}
            for vote in vote_counts:
                percentages[vote] = vote_counts[vote]/float(sum(vote_counts.values()))

            results = percentages,len(raw_classifications[subject_id])

            new_agg = {subject_id: {task_id: results}}

            # merge the new results into the existing one
            aggregations = self.__merge_results__(aggregations,new_agg)

        return aggregations


