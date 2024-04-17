MapReduce System README
Overview
This MapReduce system is designed to process large datasets using distributed computing techniques. The system leverages a custom implementation of the MapReduce programming model, allowing for scalable and efficient data processing across multiple nodes using gRPC for inter-node communication.

Files
M1.py: Implements the Mapper functionality of the MapReduce framework. It processes chunks of data and sends the results to the Reducers.
R1.py: Implements the Reducer functionality. It receives outputs from Mappers and aggregates them into a final result.
master.py: Coordinates the MapReduce operations, including initiating the Mappers and Reducers and handling data distribution.
mapReduce.proto: Defines the gRPC service protocols used for Mapper and Reducer communications.
Prerequisites
Python 3.6 or later.
gRPC Python package:
bash
Copy code
pip install grpcio
gRPC tools for Python, used to compile .proto files:
bash
Copy code
pip install grpcio-tools
Setup Instructions
Compiling Proto Files
To generate the necessary gRPC code from your .proto definitions, navigate to the directory containing mapReduce.proto and run:

bash
Copy code
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. mapReduce.proto
This command generates Python files for gRPC server and client interfaces.

Configuration
Adjust the mapper_ports and reducer_ports in M1.py and R1.py to match your network configuration and ensure that all components can communicate correctly.

Running the System
Start the Reducers
Open a terminal for each Reducer instance you plan to run. Execute the following command in each terminal:

bash
Copy code
python R1.py
Start the Mappers
After starting all Reducers, open a terminal for each Mapper instance. Run the following command in each terminal:

bash
Copy code
python M1.py
Execute the Master Script
To start the whole process, run the master script in another terminal:

bash
Copy code
python master.py
System Features
Fault Tolerance: The system includes mechanisms to handle failures in Mappers and Reducers, retrying tasks as necessary.
Parallel Processing: Mappers and Reducers can operate concurrently, maximizing resource utilization and reducing overall processing time.