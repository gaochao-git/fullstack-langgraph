# Document Preview Implementation Guide

## Overview
This guide documents how to implement document preview functionality in chat messages and historical conversations.

## Current Implementation

### 1. Document Preview in Sent Messages (Completed ✓)

We've implemented the ability to preview documents in actively sent messages:

- **Backend Flow**:
  1. Files are uploaded and get file IDs
  2. File IDs are passed with chat messages via `config.configurable.file_ids`
  3. Backend inserts document content as a system message before user message
  4. System message format: `"请参考以下文档内容回答用户问题：\n\n【文档：filename】\ncontent"`

- **Frontend Implementation**:
  1. Added `parseDocumentReferences()` function to extract document info from system messages
  2. Created `SystemMessage` component to display documents with preview buttons
  3. Integrated with existing `FilePreviewModal` for .txt and .md files
  4. Store current file IDs when submitting messages

### 2. Document Preview in Historical Conversations (To Be Implemented)

To enable preview in historical conversations, follow these steps:

#### Backend Changes

1. **Add method to retrieve thread file associations**:

```python
# In agent_service.py or a new thread_service.py
async def get_thread_file_ids(self, db: AsyncSession, thread_id: str) -> List[str]:
    """Get file IDs associated with a thread"""
    from src.apps.agent.models import AgentDocumentSession
    from sqlalchemy import select
    
    result = await db.execute(
        select(AgentDocumentSession.file_id)
        .where(AgentDocumentSession.thread_id == thread_id)
        .order_by(AgentDocumentSession.create_time)
    )
    
    return [row[0] for row in result.fetchall()]
```

2. **Modify thread loading endpoint to include file metadata**:

```python
# In endpoints.py
@router.get("/v1/agents/threads/{thread_id}/messages")
async def get_thread_messages(
    thread_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    # Get messages
    messages = await agent_service.get_thread_messages(db, thread_id)
    
    # Get associated file IDs
    file_ids = await agent_service.get_thread_file_ids(db, thread_id)
    
    return success_response({
        "messages": messages,
        "file_ids": file_ids,
        "thread_id": thread_id
    })
```

3. **Store file associations when creating threads**:

```python
# When processing a chat with files
async def create_thread_file_associations(
    db: AsyncSession, 
    thread_id: str, 
    file_ids: List[str], 
    agent_id: str,
    user_name: str
):
    """Create associations between thread and files"""
    from src.apps.agent.models import AgentDocumentSession
    
    for file_id in file_ids:
        session = AgentDocumentSession(
            thread_id=thread_id,
            file_id=file_id,
            agent_id=agent_id,
            create_by=user_name
        )
        db.add(session)
    
    await db.flush()
```

#### Frontend Changes

1. **Update ChatMessage component to accept file metadata**:

```tsx
// Add to ChatMessagesProps interface
interface ChatMessagesProps {
  // ... existing props
  threadFileIds?: string[]; // File IDs for the entire thread
  messageFileIds?: Map<string, string[]>; // File IDs per message
}
```

2. **Modify message rendering to use proper file IDs**:

```tsx
// In ChatMessage component
{dialogRounds.map((round, idx) => {
  // Get file IDs for this specific message or use thread-level IDs
  const messageFileIds = messageFileIds?.get(round.user.id) || threadFileIds || [];
  
  // Rest of rendering logic...
})}
```

3. **Update parent component that loads historical conversations**:

```tsx
// When loading a historical thread
const loadHistoricalThread = async (threadId: string) => {
  const response = await agentApi.getThreadMessages(threadId);
  
  setMessages(response.messages);
  setThreadFileIds(response.file_ids); // Store file IDs for preview
};
```

## Key Considerations

1. **File ID Storage**: 
   - For new messages: Store in `AgentDocumentSession` table
   - For historical: Retrieve from database when loading thread

2. **Performance**:
   - Cache file metadata to avoid repeated database queries
   - Consider pagination for threads with many documents

3. **Security**:
   - Verify user has access to both thread and associated files
   - Use existing permission checks in document service

4. **User Experience**:
   - Show loading state while fetching file content
   - Handle cases where files may have been deleted
   - Provide clear error messages

## Testing Checklist

- [ ] Upload multiple documents and send message
- [ ] Verify preview works for .txt and .md files
- [ ] Load historical conversation with documents
- [ ] Verify preview works in historical messages
- [ ] Test with deleted/inaccessible files
- [ ] Test performance with many documents

## Future Enhancements

1. Support more file types for preview (PDF, images)
2. Add document search within conversations
3. Implement document version tracking
4. Add collaborative annotations on documents