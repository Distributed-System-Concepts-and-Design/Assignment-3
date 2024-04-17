import grpc
import mapReduce_pb2
import mapReduce_pb2_grpc
from concurrent import futures
from threading import Thread
import random
import queue
import logging
import sys
import os
import json

class VariablesContainer:
    def __init__(self):
        self.data_points = []
        self.cluster_centroids = []
        self.mapper_ports = {i: 50051 + i for i in range(1, 6)}
        self.reducer_ports = {i: 50060 + i for i in range(1, 6)}
        self.num_reducers = None
        self.load_input_data()

    def load_input_data(self):
        with open('Input/points.txt') as f:
            for line in f:
                x, y = line.split(',')
                self.data_points.append((float(x), float(y)))

def initialize_cluster_centroids(data_points, num_centroids, cluster_centroids):
    for i in range(num_centroids):
        cluster_centroids.append([data_points[i][0], data_points[i][1]])

def connect_to_mapper(variables, mapper_id):
    mapper_addr = "localhost:" + str(variables.mapper_ports[mapper_id])
    channel = grpc.insecure_channel(mapper_addr)
    stub = mapReduce_pb2_grpc.MapReduceServiceStub(channel)
    return stub

def run_mapper(variables, start_index, end_index, iteration_num, mapper_id, num_reducers, result_queue):
    print(f"Running Mapper {mapper_id} with start index {start_index} and end index {end_index}.")
    try:
        stub = connect_to_mapper(variables, mapper_id)
        centroid_points_x = [centroid[0] for centroid in variables.cluster_centroids]
        centroid_points_y = [centroid[1] for centroid in variables.cluster_centroids]
        response = stub.ProcessMap(
            mapReduce_pb2.MapRequest(
                startIdx=start_index,
                endIdx=end_index,
                iterNum=iteration_num,
                reducers=num_reducers,
                mapperID=mapper_id,
                centroids_x=centroid_points_x,
                centroids_y=centroid_points_y
            )
        )
        result_queue.put((mapper_id,start_index, end_index, response.status == "Completed"))
        print(f"Mapper {mapper_id} completed.")
    except Exception as e:
        result_queue.put((mapper_id,start_index, end_index, False))

def connect_to_reducer(variables, reducer_id):
    reducer_addr = "localhost:" + str(variables.reducer_ports[reducer_id])
    channel = grpc.insecure_channel(reducer_addr)
    stub = mapReduce_pb2_grpc.MapReduceServiceStub(channel)
    return stub

def process_reduce_response(variables, response, target_reducer_id, reducer_id, result_queue):
    # print("Inside",reducer_id,response.status)
    if response.status == "Reduce Completed":
        centroid_ids = [pair.centroidId for pair in response.pairs]
        new_centroids_x, new_centroids_y = [pair.x for pair in response.pairs], [pair.y for pair in response.pairs]
        if not check_convergence(variables, centroid_ids, new_centroids_x, new_centroids_y):
            for i in range(len(centroid_ids)):
                variables.cluster_centroids[centroid_ids[i]-1][0] = new_centroids_x[i]
                variables.cluster_centroids[centroid_ids[i]-1][1] = new_centroids_y[i]
            # result_queue.put((reducer_id, -1))
        # else:
            # result_queue.put((reducer_id, 1))
    else:
        # print(f"Reducer {reducer_id} failed.")
        result_queue.put((target_reducer_id, reducer_id,  0))

def run_reducer(variables, iteration_num, reducer_id, target_reducer_id, num_mappers, result_queue):
    print(f"Running Reducer {reducer_id} with target reducer {target_reducer_id}.")
    try:
        stub = connect_to_reducer(variables, reducer_id)
        response = stub.ProcessReduce(
            mapReduce_pb2.ReduceRequest(
                iterNum=iteration_num,
                reducerId=reducer_id,
                targetReducerId=target_reducer_id,
                mappers=num_mappers
            )
        )
        process_reduce_response(variables, response, target_reducer_id, reducer_id, result_queue)
        print("Outside",reducer_id,response.status)
    except Exception as e:
        result_queue.put((target_reducer_id, reducer_id,  0))

def run_parallel_mappers(variables, num_mappers, num_reducers, iteration_num, mapper_index_slice):
    threads = []
    result_queue = queue.Queue()
    for i in range(num_mappers):
        start_idx = i * mapper_index_slice
        end_idx = start_idx + mapper_index_slice - 1 if i != num_mappers - 1 else len(variables.data_points) - 1
        thread = Thread(target=run_mapper, args=(variables, start_idx, end_idx, iteration_num + 1, i+1, num_reducers, result_queue))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()
    while not result_queue.empty():
        mapper_id, start_idx, end_idx, success = result_queue.get()
        if not success:
            # Reassign to a new mapper
            print(f"Mapper {mapper_id} failed. Reassigning to a new mapper.{(mapper_id % num_mappers)+1}")
            run_mapper(variables, start_idx, end_idx, iteration_num + 1, (mapper_id % num_mappers)+1, num_reducers, result_queue)

def run_parallel_reducers(variables, num_reducers, iteration_num, num_mappers):
    threads = []
    result_queue = queue.Queue()
    for i in range(num_reducers):
        thread = Thread(target=run_reducer, args=(variables, iteration_num + 1, i+1, i+1, num_mappers, result_queue))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()
    while not result_queue.empty():
        target_reducer_id, reducer_id, result = result_queue.get()
        if result == 0:
            # Reassign to a new reducer
            # print(f"Reducer {reducer_id} failed. Reassigning to a new reducer.{(reducer_id % num_mappers)+1}")
            run_reducer(variables, iteration_num + 1, (reducer_id % num_mappers) + 1, target_reducer_id, num_mappers, result_queue)

def check_convergence(variables, centroid_ids, new_centroids_x, new_centroids_y):
    converged = True
    for i, cid in enumerate(centroid_ids):
        old_x, old_y = variables.cluster_centroids[cid-1]
        new_x, new_y = new_centroids_x[i], new_centroids_y[i]
        if abs(old_x - new_x) > 0.001 or abs(old_y - new_y) > 0.001:
            converged = False
            variables.cluster_centroids[cid-1][0] = new_x
            variables.cluster_centroids[cid-1][1] = new_y
    return converged

def setup_initial_state(sys_args):
    variables = VariablesContainer()
    num_mappers = int(sys_args[1])
    num_reducers = int(sys_args[2])
    num_iterations = int(sys_args[3])
    num_centroids = int(sys_args[4])
    initialize_cluster_centroids(variables.data_points, num_centroids, variables.cluster_centroids)
    variables.num_reducers = num_reducers
    return variables, num_mappers, num_reducers, num_iterations, num_centroids

def run_map_reduce_iterations(variables, num_mappers, num_reducers, num_iterations):
    mapper_index_slice = len(variables.data_points) // num_mappers
    for iteration_num in range(num_iterations):
        print("Iteration number:", iteration_num + 1)
        run_parallel_mappers(variables, num_mappers, num_reducers, iteration_num, mapper_index_slice)
        run_parallel_reducers(variables, num_reducers, iteration_num, num_mappers)
        if iteration_num > 0 and check_convergence_and_update(variables, num_reducers):
            print(f"Convergence reached after {iteration_num} iterations.")
            break
        print(f"Centroids after iteration {iteration_num + 1}: {variables.cluster_centroids}")
    print("Final Centroids:", variables.cluster_centroids)
    with open('centroids.txt', 'w') as f:
        for centroid in variables.cluster_centroids:
            f.write(f"{centroid[0]},{centroid[1]}\n")

def check_convergence_and_update(variables, num_reducers):
    all_converged = True
    for i in range(len(variables.cluster_centroids)):
        if not check_convergence(variables, [i+1], [variables.cluster_centroids[i][0]], [variables.cluster_centroids[i][1]]):
            all_converged = False
            break
    return all_converged

def main():
    variables, num_mappers, num_reducers, num_iterations, num_centroids = setup_initial_state(sys.argv)
    dump_file_name = 'dumpMaster.txt'
    data = {
        "numMappers": num_mappers,
        "numReducers": num_reducers,
        "numIterations": num_iterations,
        "numCentroids": num_centroids
    }
    dump_data_to_file(data, dump_file_name)
    run_map_reduce_iterations(variables, num_mappers, num_reducers, num_iterations)

def dump_data_to_file(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

if __name__ == '__main__':
    main()