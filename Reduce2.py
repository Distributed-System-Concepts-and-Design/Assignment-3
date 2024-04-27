import os
import grpc
import mapReduce_pb2
import mapReduce_pb2_grpc
from concurrent import futures

mapper_ports = {i: 50051 + i for i in range(1, 6)}

class Reducer(mapReduce_pb2_grpc.MapReduceServiceServicer):

    def shuffle_and_sort(self, pairs):
        assignments = []
        for centroid_id in pairs.keys():
            for point in pairs[centroid_id]:
                assignments.append((centroid_id, point))

        centroid_sums = {}
        count = {}
        for tup in assignments:
            centroid_idx, point = tup[0], tup[1]
            if centroid_idx not in centroid_sums:
                centroid_sums[centroid_idx] = [0, 0]
                count[centroid_idx] = 0
            centroid_sums[centroid_idx][0] += point[0]
            centroid_sums[centroid_idx][1] += point[1]
            count[centroid_idx] += 1

        ret_centroids = []
        for centroid_id in centroid_sums.keys():
            ret_centroids.append((int(centroid_id), (centroid_sums[centroid_id][0] / count[centroid_id], centroid_sums[centroid_id][1] / count[centroid_id])))
        return ret_centroids

    def ProcessReduce(self, request, context):
        iteration_num = request.iterNum
        reducer_id = request.reducerId
        target_reducer_id = request.targetReducerId
        num_mappers = request.mappers

        print("Reducer ID {} is shuffling and sorting for reducer {}".format(reducer_id, target_reducer_id))
        pairs = {}
        try:
            for mapper in range(1, num_mappers+1):
                try:
                    mapper_addr = "localhost:" + str(mapper_ports[mapper])
                    with grpc.insecure_channel(mapper_addr) as channel:
                        stub = mapReduce_pb2_grpc.MapReduceServiceStub(channel)
                        response = stub.RetrieveMapPairs(
                            mapReduce_pb2.MapPairsRequest(
                                reducerId=target_reducer_id,
                                mapperId=mapper
                            )
                        )
                    for pair in response.pairs:
                        if pair.centroidId not in pairs:
                            pairs[pair.centroidId] = []
                        pairs[pair.centroidId].append((pair.x, pair.y))
                except Exception as e:
                        continue

            ret_centroids = self.shuffle_and_sort(pairs)
            ret_pairs = [mapReduce_pb2.Pair(centroidId=int(point[0]), x=point[1][0], y=point[1][1]) for point in ret_centroids]
            dump_1 = "Reducer ID {} completed shuffle and sort for reducer {}".format(reducer_id, target_reducer_id)
            dump_2 = "Centriods Returned "+str(ret_pairs)
            print("Reducer ID {} completed shuffle and sort for reducer {}".format(reducer_id, target_reducer_id))
            print("Centriods Returned",ret_pairs)
            file_name="Reducers/R"+str(reducer_id)+"/reduces.txt"
            if not os.path.exists(file_name):
                # create directory
                os.makedirs(os.path.dirname(file_name), exist_ok=True)
            temp_file = open(file_name, "a")
            temp_file.write(dump_1)
            temp_file.write("\n")
            temp_file.write(dump_2)
            temp_file.write("\n")
            return mapReduce_pb2.ReduceResponse(pairs=ret_pairs, status="Reduce Completed")
        except Exception as e:
            return mapReduce_pb2.ReduceResponse(pairs=[], status="Reduce Failed")
        

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    mapReduce_pb2_grpc.add_MapReduceServiceServicer_to_server(Reducer(), server)
    server.add_insecure_port('[::]:50062')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()