# app/schema.py
import datetime
import strawberry
from typing import Any, List, Union, Optional
from .models import User, Message, Conversation, Element
from .database import async_session
import datetime 
from dateutil import parser
from sqlalchemy.future import select
from typing import TypeVar, Generic, List, Optional
from sqlalchemy import update, delete
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import selectinload
from .utilities import parse_created_at, format_datetime, export_datetime
from .utilities import log_function_call
from graphql.language import ast

import uuid
import time
from enum import Enum
import json

@strawberry.scalar(
    description="The `JSON` scalar type represents JSON values as specified by ECMA-404"
)
class Json:
    @staticmethod
    def serialize(value) -> str:
        return json.dumps(value)

    @staticmethod
    def parse_value(value) -> dict:
        return json.loads(value)

    @staticmethod
    def parse_literal(ast_node) -> dict:
        if isinstance(ast_node, ast.StringValue):
            return json.loads(ast_node.value)


@strawberry.scalar(description="StringOrFloat Custom Scalar Type")
def StringOrFloat(value: Union[str, float]) -> Union[str, float]:
    return value


@strawberry.enum
class Role(Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    OWNER = "OWNER"
    ANONYMOUS = "ANONYMOUS"

@strawberry.type
class UserType:
    id: strawberry.ID
    username: str
    createdAt: float 
    role: Role
    image: Optional[str]
    provider: Optional[str]
    tags: Optional[List[str]] = None  

@strawberry.type
class ElementType:
    id: strawberry.ID
    conversationId: int
    type: str
    name: str
    mime: Optional[str]
    url: Optional[str]
    display: Optional[str]
    language: Optional[str]
    size: Optional[str]
    forIds: List[str]
    objectKey: Optional[str]  # New field for object key

@strawberry.type
class PageInfo:
    endCursor: Optional[str]
    hasNextPage: bool

T = TypeVar("T")

@strawberry.type
class PaginatedResponse(Generic[T]):
    pageInfo: PageInfo
    edges: List[T]


@strawberry.type
class MessageType:
    id: strawberry.ID
    isError: bool
    parentId: Optional[strawberry.ID]
    indent: int
    author: Optional[str]
    content: str
    waitForAnswer: bool
    humanFeedback: Optional[int] 
    humanFeedbackComment: Optional[str]  
    disableHumanFeedback: bool
    language: Optional[str]
    prompt: Optional[Json]  
    authorIsUser: bool
    createdAt: str 

@strawberry.input
class UserInput:
    username: str
    role: Optional[Role] = Role.USER
    image: Optional[str]
    provider: Optional[str]

@strawberry.input
class MessageInput:
    content: str
    user_id: strawberry.ID
    isError: Optional[bool] = False
@strawberry.type
class ConversationMessageType:
    id: strawberry.ID
    content: str
    createdAt: str
    isError: bool
@strawberry.type
class ConversationType:
    id: strawberry.ID
    createdAt: float 
    appUser: UserType
    tags: List[str]
    metadata: Optional[Json]  
    messages: List[MessageType]
    elements: Optional[List[ElementType]]  


@strawberry.type
class SimpleMessageResponse:
    id: strawberry.ID

@strawberry.type
class HumanFeedbackResponse:
    id: strawberry.ID
    humanFeedback: Optional[int]
    humanFeedbackComment: Optional[str]

@strawberry.type
class DeleteConversationResponse:
    id: strawberry.ID

@strawberry.type
class Edge(Generic[T]):
    node: T
    cursor: str
@strawberry.input
class ConversationInput:
    appUserId: str 
    tags: Optional[List[str]] = None
@strawberry.input
class UpdateConversationInput:
    id: strawberry.ID
    tags: Optional[List[str]] = None


@strawberry.type
class Query:
    @strawberry.field
    async def get_app_user(self, username: str) -> Optional[UserType]:
        async with async_session() as session:
            result = await session.execute(select(User).where(User.username == username))
            user = result.scalars().first()
            new_createdAt = format_datetime(user.createdAt)
            print("type(new_createdAt)", type(new_createdAt), "new_createdAt", new_createdAt)
            if user:
                return UserType(
                    id=str(user.id),
                    username=user.username,
                    createdAt=new_createdAt,
                    role=user.role,
                    image=user.image,
                    provider=user.provider,
                    tags = user.tags
                )
            return None

    @strawberry.field
    async def conversations(
        self,
        first: Optional[int] = None,
        cursor: Optional[str] = None,
        withFeedback: Optional[int] = None,
        username: Optional[str] = None,
        search: Optional[str] = None
    ) -> PaginatedResponse[Edge[ConversationType]]:
        async with async_session() as session:
            query = select(Conversation).options(
                selectinload(Conversation.appUser),
                selectinload(Conversation.messages),
                selectinload(Conversation.elements)  # Load elements as well
            ).order_by(Conversation.createdAt.desc())
            if username:
                query = query.join(User).where(User.username == username)
            try:
                result = await session.execute(query)
                conversations = result.scalars().all()
            except Exception as e:
                print("Error executing query:", e)
                return PaginatedResponse(pageInfo=PageInfo(endCursor=None, hasNextPage=False), edges=[])

            if not conversations:
                return PaginatedResponse(pageInfo=PageInfo(endCursor=None, hasNextPage=False), edges=[])
            edges = [
                Edge(
                    node=ConversationType(
                        id=str(conversation.id),
                        createdAt=format_datetime(conversation.createdAt),
                        appUser=UserType(
                            id=str(conversation.appUser.id),
                            username=conversation.appUser.username,
                            createdAt=format_datetime(conversation.appUser.createdAt),
                            role=Role(conversation.appUser.role),
                            image=conversation.appUser.image,
                            provider=conversation.appUser.provider,
                            tags=conversation.appUser.tags
                        ),
                        tags=conversation.tags,
                        messages=[
                            MessageType(
                                id=str(message.id),
                                isError=message.isError,
                                parentId=str(message.parentId) if message.parentId else None,
                                indent=message.indent,
                                author=message.author,
                                content=message.content,
                                waitForAnswer=message.waitForAnswer,
                                humanFeedback=message.humanFeedback,  # Correctly handle this field
                                humanFeedbackComment=message.humanFeedbackComment,  # Correctly handle this field
                                disableHumanFeedback=message.disableHumanFeedback,
                                language=message.language,
                                prompt=message.prompt if message.prompt else None,
                                authorIsUser=message.authorIsUser,
                                createdAt=export_datetime(message.createdAt)
                            ) for message in conversation.messages
                        ],
                        elements = [
                            ElementType(
                                id=element.id,
                                conversationId=element.conversation_id,
                                type=element.type,
                                name=element.name,
                                mime=element.mime,
                                url=element.url,
                                display=element.display,
                                language=element.language,
                                size=element.size,
                                forIds=element.for_ids,
                                objectKey=element.object_key
                            ) for element in conversation.elements
                        ],
                        metadata={}

                    ),
                    cursor=str(conversation.id)
                ) for conversation in conversations
            ]
            page_info = PageInfo(
                endCursor=str(conversations[-1].id) if conversations else None, 
                hasNextPage=False
            )
            return PaginatedResponse(pageInfo=page_info, edges=edges)

    @strawberry.field
    async def conversation(self, id: strawberry.ID) -> Optional[ConversationType]:
        async with async_session() as session:
            result = await session.execute(
                select(Conversation)
                .options(selectinload(Conversation.appUser))
                .where(Conversation.id == int(id))
            )
            conversation = result.scalars().first()
            if not conversation:
                return None
            messages_result = await session.execute(
                select(Message)
                .where(Message.conversation_id == conversation.id)
                .order_by(Message.createdAt.asc())
            )
            messages = messages_result.scalars().all()
            messages = [
                MessageType(
                    id=str(message.id),
                    isError=message.isError,
                    parentId=str(message.parentId) if message.parentId else None,
                    indent=message.indent,
                    author=message.author,
                    content=message.content,
                    waitForAnswer=message.waitForAnswer,
                    humanFeedback=message.humanFeedback,
                    humanFeedbackComment=message.humanFeedbackComment,
                    disableHumanFeedback=message.disableHumanFeedback,
                    language=message.language,
                    prompt=message.prompt if message.prompt else None,
                    authorIsUser=message.authorIsUser,
                    createdAt=export_datetime(message.createdAt)
                ) for message in messages 
            ]
            elements_result = await session.execute(
                select(Element)
                .where(Element.conversation_id == conversation.id)
            )
            elements = elements_result.scalars().all()

            # Convert elements to ElementType
            element_type = [
                ElementType(
                    id=element.id,
                    conversationId=element.conversation_id,
                    type=element.type,
                    name=element.name,
                    mime=element.mime,
                    objectKey=element.object_key,
                    url=element.url,
                    display=element.display,
                    language=element.language,
                    size=element.size,
                    forIds=element.for_ids
                ) for element in elements
            ]

            return ConversationType(
                id=str(conversation.id),
                #use the format_datetime function to parse the createdAt
                createdAt=format_datetime(conversation.createdAt),
                appUser=UserType(
                    id=str(conversation.appUser.id),
                    username=conversation.appUser.username,
                    createdAt=format_datetime(conversation.createdAt),
                    role=Role(conversation.appUser.role),
                    image=conversation.appUser.image,
                    provider=conversation.appUser.provider,
                    tags=conversation.appUser.tags
                ),
                tags=conversation.tags,
                messages=messages,
                elements=element_type,  
                metadata={}  

            )


@strawberry.type
class Mutation:

    @strawberry.mutation
    async def update_conversation(self, conversation_data: UpdateConversationInput) -> Optional[ConversationType]:
        async with async_session() as session:
            stmt = update(Conversation).where(Conversation.id == int(conversation_data.id))
            if conversation_data.tags is not None:
                stmt = stmt.values(tags=conversation_data.tags)
            result = await session.execute(stmt)
            await session.commit()
            updated_conversation = result.fetchone()
            if updated_conversation:
                return ConversationType(
                    id=str(updated_conversation.id),
                    createdAt=updated_conversation.createdAt,
                    appUser=UserType(
                        id=str(updated_conversation.appUser.id),
                        username=updated_conversation.appUser.username,
                        createdAt=updated_conversation.appUser.createdAt,
                        role=Role(updated_conversation.appUser.role),
                        image=updated_conversation.appUser.image,
                        provider=updated_conversation.appUser.provider,
                        tags=updated_conversation.appUser.tags
                    ),
                    tags=updated_conversation.tags
                )
            return None
    @strawberry.mutation
    async def create_app_user(self, username: str, role: Role, provider: Optional[str], image: Optional[str], tags: Optional[List[str]] = None) -> UserType:
        async with async_session() as session:
            existing_user = await session.execute(select(User).where(User.username == username))
            if existing_user.scalars().first():
                raise Exception(f"Username '{username}' is already taken.")
            new_user = User(
                username=username,
                role=role.value,
                tags=tags if tags is not None else [],
                provider=provider,
                image=image
            )
            session.add(new_user)
            await session.commit()
            return UserType(
                id=str(new_user.id),
                username=new_user.username,
                createdAt=new_user.createdAt,
                role=Role(new_user.role),
                tags=new_user.tags,
                provider=new_user.provider,
                image=new_user.image
            )

    @strawberry.mutation
    async def update_user(self, id: strawberry.ID, user_data: UserInput) -> Optional[UserType]:
        async with async_session() as session:
            stmt = update(User).where(User.id == int(id)).values(username=user_data.username, role=user_data.role, image=user_data.image, provider=user_data.provider).returning(User)
            result = await session.execute(stmt)
            await session.commit()
            updated_user = result.fetchone()
            if updated_user:
                return UserType(id=str(updated_user.id), username=updated_user.username, createdAt=str(updated_user.createdAt), role=updated_user.role, image=updated_user.image, provider=updated_user.provider)
            return None

    @strawberry.mutation
    async def delete_user(self, id: strawberry.ID) -> bool:
        async with async_session() as session:
            stmt = delete(User).where(User.id == int(id))
            await session.execute(stmt)
            await session.commit()
            return True
    
    @strawberry.mutation
    async def set_human_feedback(
        self, 
        message_id: strawberry.ID, 
        human_feedback: int, 
        human_feedback_comment: Optional[str] = None
    ) -> HumanFeedbackResponse:
        async with async_session() as session:
            uuid_message_id = uuid.UUID(str(message_id))
            stmt = (
                update(Message)
                .where(Message.id == uuid_message_id)
                .values(humanFeedback=human_feedback)
            )
            if human_feedback_comment is not None:
                stmt = stmt.values(humanFeedbackComment=human_feedback_comment)
            await session.execute(stmt)
            await session.commit()
            result = await session.execute(select(Message).where(Message.id == uuid_message_id))
            updated_message = result.scalar_one()
            return HumanFeedbackResponse(
                id=str(updated_message.id),
                humanFeedback=updated_message.humanFeedback,
                humanFeedbackComment=updated_message.humanFeedbackComment
            )

    @strawberry.mutation
    async def create_message(
        self,
        id: strawberry.ID,  # Convert the string to a UUID
        author: str,
        content: str,
        conversationId: strawberry.ID,  # Assuming this is a UUID
        createdAt: Optional[StringOrFloat] = None,
        language: Optional[str] = None,
        prompt: Optional[Json] = None,
        isError: Optional[bool] = False,
        parentId: Optional[str] = None,
        indent: Optional[int] = 0,
        authorIsUser: Optional[bool] = False,
        disableHumanFeedback: Optional[bool] = False,
        waitForAnswer: Optional[bool] = False,
    ) -> SimpleMessageResponse:
        uuid_id = uuid.UUID(id)
        conversation_id_int = int(conversationId)
        created_at_datetime = parse_created_at(createdAt)
        async with async_session() as session:
            new_message = Message(
                id = uuid_id, 
                content=content,
                createdAt=created_at_datetime,
                isError=isError,
                conversation_id=conversation_id_int,  
                author=author,
                language=language,
                prompt=prompt,
                parentId=parentId,
                indent=indent,
                authorIsUser=authorIsUser,
                disableHumanFeedback=disableHumanFeedback,
                waitForAnswer=waitForAnswer
            )
            session.add(new_message)
            await session.commit()
            return SimpleMessageResponse(id=str(new_message.id))  # Only return the ID of the new message

    @strawberry.mutation
    async def update_message(
        messageId: strawberry.ID,
        author: str,
        content: str,
        parentId: Optional[str] = None,
        language: Optional[str] = None,
        prompt: Optional[Json] = None,
        disableHumanFeedback: Optional[bool] = None
    ) -> SimpleMessageResponse:
        async with async_session() as session:
            uuid_message_id = uuid.UUID(str(messageId))
            uuid_parent_id = uuid.UUID(str(parentId)) if parentId else None
            stmt = update(Message).where(Message.id == uuid_message_id).values(
                author=author,
                content=content,
                parentId=uuid_parent_id,
                language=language,
                prompt=prompt,
                disableHumanFeedback=disableHumanFeedback
            )

            result = await session.execute(stmt)
            await session.commit()
            if result.rowcount > 0:
                return SimpleMessageResponse(id=str(uuid_message_id))
            else:
                return None

    @strawberry.mutation
    async def delete_message(self, id: strawberry.ID) -> bool:
        async with async_session() as session:
            stmt = delete(Message).where(Message.id == int(id))
            await session.execute(stmt)
            await session.commit()
            return True
    
    @strawberry.mutation
    async def create_element(
        self, 
        conversationId: strawberry.ID,
        type: str,
        name: str,
        display: str,
        forIds: List[str],
        url: Optional[str] = None,
        objectKey: Optional[str] = None,
        size: Optional[str] = None,
        language: Optional[str] = None,
        mime: Optional[str] = None
    ) -> Optional[ElementType]:
        async with async_session() as session:
            # Convert the size from string to integer if necessary

            new_element = Element(
                conversation_id=int(conversationId),  # Assuming conversationId is a string of integer
                type=type,
                name=name,
                display=display,
                url=url,
                object_key=objectKey,
                size=size,
                language=language,
                mime=mime,
                for_ids=forIds  # Assuming this is a JSON serializable list
            )
            session.add(new_element)
            await session.commit()

            return ElementType(
                id=new_element.id,
                conversationId=new_element.conversation_id,
                type=new_element.type,
                name=new_element.name,
                mime=new_element.mime,
                url=new_element.url,
                objectKey=new_element.object_key,
                display=new_element.display,
                language=new_element.language,
                size=new_element.size,
                forIds=new_element.for_ids
            )
    @strawberry.mutation
    async def create_conversation(self, appUserId: Optional[str] = None, tags: Optional[List[str]] = None) -> Optional[ConversationType]:
        if not appUserId:
            raise ValueError("appUserId must be provided")

        app_user_id_int = int(appUserId)

        async with async_session() as session:
            result = await session.execute(select(User).where(User.id == app_user_id_int))
            user = result.scalars().first()

            if not user:
                raise ValueError("Invalid appUserId")
            new_conversation = Conversation(
                appUserId=app_user_id_int,
                tags=tags if tags is not None else []
            )
            session.add(new_conversation)
            await session.commit()

            return ConversationType(
                id=str(new_conversation.id),
                createdAt=new_conversation.createdAt,
                appUser=UserType(
                    id=str(user.id),
                    username=user.username,
                    createdAt=user.createdAt,
                    role=Role(user.role),
                    image=user.image,
                    provider=user.provider,
                    tags=user.tags
                ),
                tags=new_conversation.tags,
                messages=[],  
                elements=[],  
                metadata={}  
            )

    @strawberry.mutation
    async def delete_conversation(self, id: strawberry.ID) -> Optional[DeleteConversationResponse]:
        async with async_session() as session:
            await session.execute(delete(Message).where(Message.conversation_id == int(id)))
            stmt = delete(Conversation).where(Conversation.id == int(id))
            await session.execute(stmt)
            await session.commit()
            return DeleteConversationResponse(id=id)


schema = strawberry.Schema(query=Query, mutation=Mutation)
