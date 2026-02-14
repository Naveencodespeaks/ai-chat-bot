# AI RAG Sentiment Bot - API Documentation

## Overview

The AI RAG Sentiment Bot API is a comprehensive REST API for managing conversations, documents, user accounts, and support tickets with advanced AI capabilities including sentiment analysis, retrieval-augmented generation (RAG), and intelligent escalation.

**Base URL:**  `http://localhost:8000/api`

**API Version:** 1.0.0

**Documentation:** `http://localhost:8000/api/docs` (Swagger UI)

---

## Table of Contents

1. [Authentication](#authentication)
2. [API Endpoints](#api-endpoints)
   - [Health](#health)
   - [Authentication](#authentication-endpoints)
   - [Chat](#chat-endpoints)
   - [Documents](#documents-endpoints)
   - [Sentiment](#sentiment-endpoints)
   - [Users](#users-endpoints)
   - [Tickets](#tickets-endpoints)
3. [Error Handling](#error-handling)
4. [Common Patterns](#common-patterns)

---

## Authentication

All endpoints except `/api/auth/register` and `/api/auth/login` require Bearer token authentication.

### How to Authenticate

1. **Register** a new user or **Login** to get an access token
2. **Include** the token in the `Authorization` header for all subsequent requests

```bash
Authorization: Bearer {access_token}
```

### Token Expiry

- Access tokens expire after **24 hours**
- Users must login again to get a new token

---

## API Endpoints

### Health

#### Get API Health Status
- **Endpoint:** `GET /health`
- **Description:** Check if the API is running
- **Authentication:** Not required
- **Response:**
  ```json
  {
    "status": "healthy",
    "version": "1.0.0",
    "database": "connected",
    "vector_db": "connected"
  }
  ```

---

### Authentication Endpoints

#### Register New User
- **Endpoint:** `POST /auth/register`
- **Description:** Create a new user account
- **Authentication:** Not required
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "securepassword123",
    "full_name": "John Doe"
  }
  ```
- **Response:** 201 Created
  ```json
  {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z"
  }
  ```

#### Login User
- **Endpoint:** `POST /auth/login`
- **Description:** Authenticate user and get access token
- **Authentication:** Not required
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "securepassword123"
  }
  ```
- **Response:** 200 OK
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "email": "user@example.com",
      "full_name": "John Doe",
      "is_active": true
    }
  }
  ```

#### Get Current User
- **Endpoint:** `GET /auth/me`
- **Description:** Retrieve authenticated user's profile
- **Authentication:** Required (Bearer token)
- **Response:** 200 OK
  ```json
  {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_active": true
  }
  ```

#### Update User Profile
- **Endpoint:** `PUT /auth/me`
- **Description:** Update current user's information
- **Authentication:** Required (Bearer token)
- **Request Body:**
  ```json
  {
    "full_name": "Jane Doe",
    "email": "jane@example.com"
  }
  ```
- **Response:** 200 OK

#### Change Password
- **Endpoint:** `POST /auth/change-password`
- **Description:** Change password for current user
- **Authentication:** Required (Bearer token)
- **Request Body:**
  ```json
  {
    "old_password": "oldpassword123",
    "new_password": "newpassword123"
  }
  ```
- **Response:** 200 OK

---

### Chat Endpoints

#### Create Conversation
- **Endpoint:** `POST /chat/conversations`
- **Description:** Start a new chat conversation
- **Authentication:** Required
- **Request Body:**
  ```json
  {
    "title": "Support Request"
  }
  ```
- **Response:** 201 Created
  ```json
  {
    "id": 1,
    "user_id": 1,
    "status": "OPEN",
    "created_at": "2024-01-15T10:30:00Z"
  }
  ```

#### List Conversations
- **Endpoint:** `GET /chat/conversations?skip=0&limit=50`
- **Description:** Get all conversations for current user
- **Authentication:** Required
- **Query Parameters:**
  - `skip`: Number of records to skip (default: 0)
  - `limit`: Maximum records to return (default: 50)
- **Response:** 200 OK (List of conversations)

#### Get Conversation Details
- **Endpoint:** `GET /chat/conversations/{conversation_id}`
- **Description:** Retrieve a specific conversation with all messages
- **Authentication:** Required
- **Response:** 200 OK
  ```json
  {
    "id": 1,
    "user_id": 1,
    "status": "OPEN",
    "created_at": "2024-01-15T10:30:00Z",
    "messages": []
  }
  ```

#### Delete Conversation
- **Endpoint:** `DELETE /chat/conversations/{conversation_id}`
- **Description:** Delete a conversation and all its messages
- **Authentication:** Required
- **Response:** 204 No Content

#### Send Message
- **Endpoint:** `POST /chat/conversations/{conversation_id}/messages`
- **Description:** Send message in conversation (gets AI response)
- **Authentication:** Required
- **Request Body:**
  ```json
  {
    "content": "Hello, I need help with..."
  }
  ```
- **Response:** 201 Created
  ```json
  {
    "user_message": {
      "id": 1,
      "content": "Hello, I need help with...",
      "sender_type": "USER",
      "created_at": "2024-01-15T10:30:00Z"
    },
    "bot_response": {
      "id": 2,
      "content": "I understand your issue...",
      "sender_type": "BOT",
      "created_at": "2024-01-15T10:30:05Z"
    },
    "sentiment_score": 0.65,
    "requires_escalation": false
  }
  ```

#### Get Conversation Messages
- **Endpoint:** `GET /chat/conversations/{conversation_id}/messages?skip=0&limit=100`
- **Description:** Retrieve all messages in a conversation
- **Authentication:** Required
- **Response:** 200 OK (List of messages)

#### Delete Message
- **Endpoint:** `DELETE /chat/conversations/{conversation_id}/messages/{message_id}`
- **Description:** Delete a specific message
- **Authentication:** Required
- **Response:** 204 No Content

---

### Documents Endpoints

#### Upload Document
- **Endpoint:** `POST /documents/upload`
- **Description:** Upload a document for RAG ingestion
- **Authentication:** Required
- **Content-Type:** `multipart/form-data`
- **Parameters:**
  - `file`: Document file (PDF, TXT, MD, DOCX)
  - `metadata`: Optional JSON metadata
- **Response:** 201 Created
  ```json
  {
    "id": 1,
    "name": "document.pdf",
    "file_size": 102400,
    "uploaded_by_id": 1,
    "created_at": "2024-01-15T10:30:00Z"
  }
  ```

#### Create Document from Content
- **Endpoint:** `POST /documents`
- **Description:** Create a document from raw content
- **Authentication:** Required
- **Request Body:**
  ```json
  {
    "title": "API Documentation",
    "content": "This is the content...",
    "source_url": "https://example.com/docs",
    "metadata": {"category": "technical"}
  }
  ```
- **Response:** 201 Created

#### List Documents
- **Endpoint:** `GET /documents?skip=0&limit=50`
- **Description:** Retrieve all ingested documents
- **Authentication:** Required
- **Response:** 200 OK (List of documents)

#### Get Document Details
- **Endpoint:** `GET /documents/{document_id}`
- **Description:** Retrieve specific document information
- **Authentication:** Required
- **Response:** 200 OK

#### Delete Document
- **Endpoint:** `DELETE /documents/{document_id}`
- **Description:** Delete a document and its embeddings
- **Authentication:** Required
- **Response:** 204 No Content

#### Get Document Chunks
- **Endpoint:** `GET /documents/{document_id}/chunks?skip=0&limit=20`
- **Description:** Retrieve vector store chunks for a document
- **Authentication:** Required
- **Response:** 200 OK (List of chunks)

---

### Sentiment Endpoints

#### Analyze Text Sentiment
- **Endpoint:** `POST /sentiment/analyze`
- **Description:** Analyze sentiment of provided text
- **Authentication:** Required
- **Request Body:**
  ```json
  {
    "text": "This product is amazing!",
    "context": "product_review"
  }
  ```
- **Response:** 200 OK
  ```json
  {
    "score": 0.92,
    "label": "positive",
    "confidence": 0.95,
    "analysis_id": 1
  }
  ```

#### Get Conversation Sentiment
- **Endpoint:** `GET /sentiment/conversation/{conversation_id}`
- **Description:** Get sentiment analysis for entire conversation
- **Authentication:** Required
- **Response:** 200 OK
  ```json
  {
    "conversation_id": 1,
    "total_messages": 5,
    "messages_analyzed": 5,
    "average_sentiment": 0.68,
    "min_sentiment": 0.45,
    "max_sentiment": 0.92,
    "trend": "improving"
  }
  ```

#### Get User Sentiment Logs
- **Endpoint:** `GET /sentiment/user/logs?skip=0&limit=50`
- **Description:** Retrieve all sentiment analyses for current user
- **Authentication:** Required
- **Response:** 200 OK (List of sentiment logs)

#### Get Sentiment Summary
- **Endpoint:** `GET /sentiment/user/summary`
- **Description:** Get sentiment statistics for current user
- **Authentication:** Required
- **Response:** 200 OK
  ```json
  {
    "user_id": 1,
    "total_analyses": 42,
    "average_sentiment": 0.72,
    "positive_count": 28,
    "negative_count": 8,
    "neutral_count": 6,
    "positive_percentage": 66.7,
    "negative_percentage": 19.0,
    "neutral_percentage": 14.3
  }
  ```

---

### Users Endpoints

#### List All Users
- **Endpoint:** `GET /users?skip=0&limit=50`
- **Description:** Retrieve all users (admin only)
- **Authentication:** Required (admin role)
- **Response:** 200 OK (List of users)

#### Search Users
- **Endpoint:** `GET /users/search?query=john`
- **Description:** Search for users by email or name
- **Authentication:** Required
- **Response:** 200 OK (List of matching users)

#### Get User Details
- **Endpoint:** `GET /users/{user_id}`
- **Description:** Retrieve specific user information
- **Authentication:** Required
- **Response:** 200 OK

#### Update User
- **Endpoint:** `PUT /users/{user_id}`
- **Description:** Update user information (admin only)
- **Authentication:** Required
- **Request Body:**
  ```json
  {
    "full_name": "Updated Name",
    "email": "new@example.com",
    "is_active": true
  }
  ```
- **Response:** 200 OK

#### Delete User
- **Endpoint:** `DELETE /users/{user_id}`
- **Description:** Delete a user account (admin only)
- **Authentication:** Required (admin role)
- **Response:** 204 No Content

#### Assign Role
- **Endpoint:** `POST /users/{user_id}/roles/{role_id}`
- **Description:** Assign a role to a user (admin only)
- **Authentication:** Required (admin role)
- **Response:** 201 Created

#### Remove Role
- **Endpoint:** `DELETE /users/{user_id}/roles/{role_id}`
- **Description:** Remove a role from a user (admin only)
- **Authentication:** Required (admin role)
- **Response:** 204 No Content

---

### Tickets Endpoints

#### Create Ticket
- **Endpoint:** `POST /tickets`
- **Description:** Create a support/escalation ticket
- **Authentication:** Required
- **Request Body:**
  ```json
  {
    "conversation_id": 1,
    "title": "Urgent Issue",
    "description": "Detailed description of the issue",
    "priority": "high",
    "category": "technical"
  }
  ```
- **Response:** 201 Created
  ```json
  {
    "id": 1,
    "conversation_id": 1,
    "title": "Urgent Issue",
    "priority": "HIGH",
    "status": "OPEN",
    "created_at": "2024-01-15T10:30:00Z"
  }
  ```

#### List Tickets
- **Endpoint:** `GET /tickets?status_filter=open&priority_filter=high&skip=0&limit=50`
- **Description:** Retrieve all tickets for current user
- **Authentication:** Required
- **Query Parameters:**
  - `status_filter`: Filter by status (open, in_progress, resolved, closed)
  - `priority_filter`: Filter by priority (low, medium, high, critical)
  - `skip`: Number of records to skip
  - `limit`: Maximum records to return
- **Response:** 200 OK (List of tickets)

#### Get Ticket Details
- **Endpoint:** `GET /tickets/{ticket_id}`
- **Description:** Retrieve ticket details
- **Authentication:** Required
- **Response:** 200 OK

#### Update Ticket
- **Endpoint:** `PUT /tickets/{ticket_id}`
- **Description:** Update ticket details
- **Authentication:** Required
- **Request Body:**
  ```json
  {
    "title": "Updated Title",
    "status": "in_progress",
    "priority": "critical",
    "assigned_to_id": 5
  }
  ```
- **Response:** 200 OK

#### Delete Ticket
- **Endpoint:** `DELETE /tickets/{ticket_id}`
- **Description:** Delete a ticket
- **Authentication:** Required
- **Response:** 204 No Content

#### Escalate Ticket
- **Endpoint:** `POST /tickets/{ticket_id}/escalate`
- **Description:** Escalate a ticket to higher support level
- **Authentication:** Required
- **Request Body:**
  ```json
  {
    "reason": "Issue requires technical expert"
  }
  ```
- **Response:** 200 OK
  ```json
  {
    "message": "Ticket escalated successfully",
    "ticket_id": 1,
    "new_status": "ESCALATED"
  }
  ```

#### Get Ticket Statistics
- **Endpoint:** `GET /tickets/stats/summary`
- **Description:** Get ticket statistics for current user
- **Authentication:** Required
- **Response:** 200 OK
  ```json
  {
    "total_tickets": 15,
    "open": 5,
    "in_progress": 3,
    "resolved": 5,
    "closed": 2,
    "critical_priority": 1,
    "high_priority": 4
  }
  ```

---

## Error Handling

### Error Response Format

All errors follow this standard format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes

| Status Code | Meaning |
|---|---|
| 200 | OK - Request succeeded |
| 201 | Created - Resource created successfully |
| 204 | No Content - Request succeeded (no response body) |
| 400 | Bad Request - Invalid input parameters |
| 401 | Unauthorized - Missing or invalid authentication |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error - Server error |

### Example Error Response

```bash
HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "detail": "Conversation not found"
}
```

---

## Common Patterns

### Authentication Header

```bash
curl -H "Authorization: Bearer {access_token}" \
  http://localhost:8000/api/chat/conversations
```

### Pagination

All list endpoints support pagination:

```bash
GET /api/chat/conversations?skip=0&limit=50
```

**Parameters:**
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum records to return (default varies by endpoint)

### Filtering

Many list endpoints support filtering:

```bash
GET /api/tickets?status_filter=open&priority_filter=high
```

### Creating Resources

When creating resources, use POST with JSON body:

```bash
curl -X POST http://localhost:8000/api/chat/conversations \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"title": "My Conversation"}'
```

### Updating Resources

When updating resources, use PUT with JSON body:

```bash
curl -X PUT http://localhost:8000/api/users/{user_id} \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"full_name": "New Name"}'
```

### Deleting Resources

When deleting resources, use DELETE:

```bash
curl -X DELETE http://localhost:8000/api/chat/conversations/{conversation_id} \
  -H "Authorization: Bearer {token}"
```

---

## Rate Limiting

Currently, there is no rate limiting configured. For production deployments, implement rate limiting to prevent abuse.

---

## CORS

The API accepts requests from all origins. For production, configure CORS to only allow trusted domains in `app/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Best Practices

1. **Always include authentication tokens** for protected endpoints
2. **Use pagination** for large datasets to avoid performance issues
3. **Check response status codes** to handle errors appropriately
4. **Log all API interactions** for debugging and auditing
5. **Validate input** before sending to API
6. **Keep access tokens secure** - never expose them in logs or client-side code
7. **Use HTTPS** in production to encrypt data in transit

---

## Examples

### Complete Chat Flow

```bash
# 1. Login to get token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'

# Response includes: access_token

# 2. Create conversation
curl -X POST http://localhost:8000/api/chat/conversations \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{"title": "Support Request"}'

# Response includes: conversation_id

# 3. Send message
curl -X POST http://localhost:8000/api/chat/conversations/{conversation_id}/messages \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{"content": "I need help with..."}'

# Response includes: user_message, bot_response, sentiment_score
```

---

## Support

For issues or questions about the API:
- Check the logs in `app/logs/`
- Review the Swagger documentation at `/api/docs`
- Contact the development team

---

**Last Updated:** February 2024
**Version:** 1.0.0
