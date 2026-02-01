from abc import ABC
from email import message
from enum import Enum
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Header

app = FastAPI()

class ListenerManager(ABC):

    def __init__(self):
        self.messages = []

    def evict_message_bundle(self):
        pass

    def add_message(self):
        pass


class TimeListener(ListenerManager):

    def evict_message_bundle(self):
        pass


class SizeListener(ListenerManager):

    def evict_message_bundle(self):
        pass


class HybridListener(ListenerManager):

    def evict_message_bundle(self):
        pass


def do():
    return 'abc'

class ListenerRequest(BaseModel):
    _id: str # UserID + MessageID/InitialMessageTimestamp
    message: str
    total: pydantic.field(gt=0)


class ListenerResponse(BaseModel):
    _id: str
    action: str


app.post("/events")
async def endpoint(reqs: ListenerRequest) -> ListenerResponse:

    action = do()
    return ListenerResponse(_id=reqs._id, action=action)



if __name__ == "__main__":
    pass