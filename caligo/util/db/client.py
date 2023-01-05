from contextlib import asynccontextmanager
from typing import (
    Any,
    AsyncGenerator,
    FrozenSet,
    List,
    MutableMapping,
    Optional,
    Set,
    Tuple,
    Union
)

from bson import CodecOptions
from bson.codec_options import DEFAULT_CODEC_OPTIONS
from bson.son import SON
from bson.timestamp import Timestamp
from pymongo import MongoClient
from pymongo.client_session import TransactionOptions
from pymongo.collation import Collation
from pymongo.driver_info import DriverInfo
from pymongo.read_concern import ReadConcern
from pymongo.read_preferences import ReadPreference
from pymongo.topology_description import TopologyDescription
from pymongo.write_concern import DEFAULT_WRITE_CONCERN, WriteConcern

from .base import AsyncBaseProperty
from .change_stream import AsyncChangeStream
from .client_session import AsyncClientSession
from .command_cursor import AsyncCommandCursor, CommandCursor
from .db import AsyncDatabase
from .types import ReadPreferences

from caligo import util


class AsyncClient(AsyncBaseProperty):
    """AsyncIO :obj:`~MongoClient`

       *DEPRECATED* methods are removed in this class.
    """

    dispatch: MongoClient

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["driver"] = DriverInfo(
            name="AsyncIOMongoDB", version="staging", platform="AsyncIO"
        )
        dispatch = MongoClient(*args, **kwargs)

        # Propagate initialization to base
        super().__init__(dispatch)

    def __getitem__(self, name: str) -> AsyncDatabase:
        return AsyncDatabase(self, self.dispatch[name])

    async def close(self) -> None:
        await util.run_sync(self.dispatch.close)

    async def drop_database(
        self,
        name_or_database: Union[str, AsyncDatabase],
        session: Optional[AsyncClientSession] = None
    ) -> None:
        if isinstance(name_or_database, AsyncDatabase):
            name_or_database = name_or_database.name

        return await util.run_sync(
            self.dispatch.drop_database,
            name_or_database,
            session=session.dispatch if session else session
        )

    def get_database(
        self,
        name: Optional[str] = None,
        *,
        codec_options: Optional[CodecOptions] = None,
        read_preference: Optional[ReadPreferences] = None,
        write_concern: Optional[WriteConcern] = None,
        read_concern: Optional[ReadConcern] = None
    ) -> AsyncDatabase:
        return AsyncDatabase(
            self,
            self.dispatch.get_database(
                name,
                codec_options=codec_options,
                read_preference=read_preference,
                write_concern=write_concern,
                read_concern=read_concern
            )
        )

    def get_default_database(
        self,
        default: Optional[str] = None,
        *,
        codec_options: Optional[CodecOptions] = None,
        read_preference: Optional[ReadPreferences] = None,
        write_concern: Optional[WriteConcern] = None,
        read_concern: Optional[ReadConcern] = None
    ) -> AsyncDatabase:
        return AsyncDatabase(
            self,
            self.dispatch.get_default_database(
                default,
                codec_options=codec_options,
                read_preference=read_preference,
                write_concern=write_concern,
                read_concern=read_concern
            )
        )

    async def list_database_names(
        self, session: Optional[AsyncClientSession] = None
    ) -> List[str]:
        return await util.run_sync(
            self.dispatch.list_database_names,
            session=session.dispatch if session else session
        )

    async def list_databases(
        self, session: Optional[AsyncClientSession] = None, **kwargs: Any
    ) -> AsyncCommandCursor:
        cmd = SON([("listDatabases", 1)])
        cmd.update(kwargs)
        database = self.get_database("admin",
                                     codec_options=DEFAULT_CODEC_OPTIONS,
                                     read_preference=ReadPreference.PRIMARY,
                                     write_concern=DEFAULT_WRITE_CONCERN)
        res: MutableMapping[str, Any] = await util.run_sync(
            database.dispatch._retryable_read_command,  # skipcq: PYL-W0212
            cmd,
            session=session.dispatch if session else session
        )
        cursor: MutableMapping[str, Any] = {
            "id": 0,
            "firstBatch": res["databases"],
            "ns": "admin.$cmd",
        }
        return AsyncCommandCursor(CommandCursor(database["$cmd"], cursor, None))

    async def server_info(
        self, session: Optional[AsyncClientSession] = None
    ) -> MutableMapping[str, Any]:
        return await util.run_sync(
            self.dispatch.server_info,
            session=session.dispatch if session else session
        )

    # Don't need await when entering the context manager,
    # because it's slightly different than motor libs.
    @asynccontextmanager
    async def start_session(
        self,
        *,
        causal_consistency: Optional[bool] = None,
        default_transaction_options: Optional[TransactionOptions] = None,
        snapshot: bool = False,
    ) -> AsyncGenerator[AsyncClientSession, None]:
        session = await util.run_sync(
            self.dispatch.start_session,
            causal_consistency=causal_consistency,
            default_transaction_options=default_transaction_options,
            snapshot=snapshot
        )

        async with AsyncClientSession(self, session) as session:
            yield session

    def watch(
        self,
        pipeline: Optional[List[MutableMapping[str, Any]]] = None,
        *,
        full_document: Optional[str] = None,
        resume_after: Optional[Any] = None,
        max_await_time_ms: Optional[int] = None,
        batch_size: Optional[int] = None,
        collation: Optional[Collation] = None,
        start_at_operation_time: Optional[Timestamp] = None,
        session: Optional[AsyncClientSession] = None,
        start_after: Optional[Any] = None
    ) -> AsyncChangeStream:
        return AsyncChangeStream(
            self,
            pipeline,
            full_document,
            resume_after,
            max_await_time_ms,
            batch_size,
            collation,
            start_at_operation_time,
            session,
            start_after
        )

    @property
    def HOST(self) -> str:
        return self.dispatch.HOST

    @property
    def PORT(self) -> int:
        return self.dispatch.PORT

    @property
    def address(self) -> Optional[Tuple[str, int]]:
        return self.dispatch.address

    @property
    def arbiters(self) -> Set[Tuple[str, int]]:
        return self.dispatch.arbiters

    @property
    def event_listeners(self) -> Any:
        return self.dispatch.event_listeners

    @property
    def is_mongos(self) -> bool:
        return self.dispatch.is_mongos

    @property
    def is_primary(self) -> bool:
        return self.dispatch.is_primary

    @property
    def local_threshold_ms(self) -> int:
        return self.dispatch.local_threshold_ms

    @property
    def max_bson_size(self) -> int:
        return self.dispatch.max_bson_size

    @property
    def max_idle_time_ms(self) -> Optional[int]:
        return self.dispatch.max_idle_time_ms

    @property
    def max_message_size(self) -> int:
        return self.dispatch.max_message_size

    @property
    def max_pool_size(self) -> int:
        return self.dispatch.max_pool_size

    @property
    def max_write_batch_size(self) -> int:
        return self.dispatch.max_write_batch_size

    @property
    def min_pool_size(self) -> int:
        return self.dispatch.min_pool_size

    @property
    def nodes(self) -> FrozenSet[Set[Tuple[str, int]]]:
        return self.dispatch.nodes

    @property
    def primary(self) -> Optional[Tuple[str, int]]:
        return self.dispatch.primary

    @property
    def retry_reads(self) -> bool:
        return self.dispatch.retry_reads

    @property
    def retry_writes(self) -> bool:
        return self.dispatch.retry_writes

    @property
    def secondaries(self) -> Set[Tuple[str, int]]:
        return self.dispatch.secondaries

    @property
    def server_selection_timeout(self) -> int:
        return self.dispatch.server_selection_timeout

    @property
    def topology_description(self) -> TopologyDescription:
        return self.dispatch.topology_description
