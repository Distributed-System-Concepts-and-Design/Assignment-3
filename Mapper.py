import sys
import grpc
import mapReduce_pb2
import mapReduce_pb2_grpc
import os
import math as Math
from concurrent import futures

class MasterMapper(mapReduce_pb2_grpc.MapReduceServiceServicer):

    def RetrieveMapPairs(self, request, context):   
        reducer_id = request.reducerId
        mapper_id = request.mapperId
        print("mapper id is", mapper_id)
        print("reducer id is", reducer_id)
        temp_file_path = "Mappers/" + "M" + str(mapper_id) + "/R" + str(reducer_id)+".txt"
        if not os.path.exists(temp_file_path):
            return mapReduce_pb2.MapPairsResponse(pairs=[])
        else:
            temp_file = open(temp_file_path, "r")
            assignments = []
            flag = False
            for newline in temp_file:
                if flag:
                    centroid_id, x, y = newline.split(",")
                    assignments.append(mapReduce_pb2.Pair(centroidId=int(centroid_id), x=float(x), y=float(y)))
                else:
                    flag = True
            temp_file.close()
            return mapReduce_pb2.MapPairsResponse(pairs=assignments)

    def ProcessMap(self, request, context):
        start_idx = request.startIdx
        end_idx = request.endIdx
        iter_num = request.iterNum
        num_reducers = request.reducers
        mapper_id = request.mapperID
        centroids_x = request.centroids_x
        centroids_y = request.centroids_y

        points = self.read_points_from_file('Input/points.txt')
        try:
            assignments = {}

            for i in range(start_idx, end_idx+1):
                min_dist = float('inf')
                closest_centroid = None
                for idx in range(len(centroids_x)):
                    dist = Math.sqrt((points[i][0] - centroids_x[idx]) ** 2 + (points[i][1] - centroids_y[idx]) ** 2)
                    if dist < min_dist:
                        min_dist = dist
                        closest_centroid = idx+1
                if closest_centroid not in assignments:
                    assignments[int(closest_centroid)] = []
                tmp_tuple = (points[i][0], points[i][1])
                assignments[int(closest_centroid)].append(tmp_tuple)

            self.parter(assignments, num_reducers, mapper_id, iter_num)
            print("Sending Completed status back.")
            return mapReduce_pb2.MapResponse(status="Completed")
        except Exception as e:
            print(e)
            return mapReduce_pb2.MapResponse(status="Failed")

    def parter(self, assignments, num_reducers, mapper_id, iter_num):
        print("Inside parter")
        for i in range(num_reducers):
            file_path = "Mappers/" + "M" + str(mapper_id) + "/partition_" + str(i+1)+".txt"
            if not os.path.exists(file_path):
                # if directory does noot exist create it
                if not os.path.exists(file_path):                    
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                temp_file = open(file_path, "w")
                temp_file.write(str(iter_num) + "\n")
                temp_file.close()
            else:
                temp_file = open(file_path, "r")
                temp_file_readline = temp_file.readline()
                if temp_file_readline == str(iter_num) + "\n":
                    temp_file.close()
                else:
                    temp_file.close()
                    temp_file = open(file_path, "w")
                    temp_file.write(str(iter_num) + "\n")
                    temp_file.close()
        for centroid_id in assignments.keys():
            temp_file_id = (centroid_id-1) % num_reducers
            file_path = "Mappers/" + "M" + str(mapper_id) + "/partition_" + str(temp_file_id+1)+".txt"
            temp_file = open(file_path, "a")
            for assignment in assignments[centroid_id]:
                temp_file.write("%d, %.4f, %.4f\n" % (centroid_id, assignment[0], assignment[1]))
            temp_file.close()
    

    def dump_points_to_file(self, points, filename):
        with open(filename, 'a') as file:
            for point in points:
                file.write(f"{point[0]}, {point[1]}\n")

    def read_points_from_file(self, filename):
        points = []
        with open(filename, 'r') as file:
            for line in file:
                x, y = line.strip().split(',')
                points.append((float(x), float(y)))
        return points

def serve():
    try:
        Reducer_IDs = {}
        Mapper_IDs = {}
        self_id = sys.argv[1]
        
        with open("Config.conf", "r") as file:
            for line in file:
                id, _, port = line.strip().split()
                if 'R' in id:
                    Reducer_IDs[id] = port
                else:
                    Mapper_IDs[id] = port
        
        # get self port
        port = Mapper_IDs[self_id]

    except Exception as e:
        print("Invalid ID read from Config.conf!")
        return
    
    try:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        mapReduce_pb2_grpc.add_MapReduceServiceServicer_to_server(MasterMapper(), server)
        server.add_insecure_port('[::]:'+port)
        server.start()
        server.wait_for_termination()
    except KeyboardInterrupt:
        print(f"Mapper {id} Stopped!")


if __name__ == '__main__':
    serve()