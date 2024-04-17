from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class MapRequest(_message.Message):
    __slots__ = ("startIdx", "endIdx", "iterNum", "reducers", "mapperID", "centroids_x", "centroids_y")
    STARTIDX_FIELD_NUMBER: _ClassVar[int]
    ENDIDX_FIELD_NUMBER: _ClassVar[int]
    ITERNUM_FIELD_NUMBER: _ClassVar[int]
    REDUCERS_FIELD_NUMBER: _ClassVar[int]
    MAPPERID_FIELD_NUMBER: _ClassVar[int]
    CENTROIDS_X_FIELD_NUMBER: _ClassVar[int]
    CENTROIDS_Y_FIELD_NUMBER: _ClassVar[int]
    startIdx: int
    endIdx: int
    iterNum: int
    reducers: int
    mapperID: int
    centroids_x: _containers.RepeatedScalarFieldContainer[float]
    centroids_y: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, startIdx: _Optional[int] = ..., endIdx: _Optional[int] = ..., iterNum: _Optional[int] = ..., reducers: _Optional[int] = ..., mapperID: _Optional[int] = ..., centroids_x: _Optional[_Iterable[float]] = ..., centroids_y: _Optional[_Iterable[float]] = ...) -> None: ...

class MapResponse(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: str
    def __init__(self, status: _Optional[str] = ...) -> None: ...

class ReduceRequest(_message.Message):
    __slots__ = ("iterNum", "reducerId", "targetReducerId", "mappers")
    ITERNUM_FIELD_NUMBER: _ClassVar[int]
    REDUCERID_FIELD_NUMBER: _ClassVar[int]
    TARGETREDUCERID_FIELD_NUMBER: _ClassVar[int]
    MAPPERS_FIELD_NUMBER: _ClassVar[int]
    iterNum: int
    reducerId: int
    targetReducerId: int
    mappers: int
    def __init__(self, iterNum: _Optional[int] = ..., reducerId: _Optional[int] = ..., targetReducerId: _Optional[int] = ..., mappers: _Optional[int] = ...) -> None: ...

class ReduceResponse(_message.Message):
    __slots__ = ("pairs", "status")
    PAIRS_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    pairs: _containers.RepeatedCompositeFieldContainer[Pair]
    status: str
    def __init__(self, pairs: _Optional[_Iterable[_Union[Pair, _Mapping]]] = ..., status: _Optional[str] = ...) -> None: ...

class MapPairsRequest(_message.Message):
    __slots__ = ("reducerId", "mapperId")
    REDUCERID_FIELD_NUMBER: _ClassVar[int]
    MAPPERID_FIELD_NUMBER: _ClassVar[int]
    reducerId: int
    mapperId: int
    def __init__(self, reducerId: _Optional[int] = ..., mapperId: _Optional[int] = ...) -> None: ...

class MapPairsResponse(_message.Message):
    __slots__ = ("pairs",)
    PAIRS_FIELD_NUMBER: _ClassVar[int]
    pairs: _containers.RepeatedCompositeFieldContainer[Pair]
    def __init__(self, pairs: _Optional[_Iterable[_Union[Pair, _Mapping]]] = ...) -> None: ...

class Pair(_message.Message):
    __slots__ = ("centroidId", "x", "y")
    CENTROIDID_FIELD_NUMBER: _ClassVar[int]
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    centroidId: int
    x: float
    y: float
    def __init__(self, centroidId: _Optional[int] = ..., x: _Optional[float] = ..., y: _Optional[float] = ...) -> None: ...
