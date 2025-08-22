# Chat API 🚀

A modern, real-time chat application built with FastAPI, WebSockets, and a beautiful frontend. Features include user authentication, real-time messaging, chat rooms, and a responsive design.

## ✨ Features

- **Real-time Chat**: WebSocket-based instant messaging
- **User Authentication**: JWT-based secure authentication
- **Chat Rooms**: Create and join multiple chat rooms
- **Modern UI**: Beautiful, responsive frontend design
- **Message Persistence**: Store chat history in database
- **RESTful API**: Clean, documented API endpoints
- **Docker Support**: Easy deployment with containers

## 🏗️ Architecture

- **Backend**: FastAPI (Python)
- **Database**: SQLAlchemy ORM with PostgreSQL/SQLite support
- **Authentication**: JWT tokens with bcrypt password hashing
- **Real-time**: WebSocket connections for live chat
- **Frontend**: Vanilla JavaScript with modern CSS
- **Deployment**: Docker and Docker Compose

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Docker and Docker Compose (optional)
- PostgreSQL (optional, SQLite is default)

### Option 1: Local Development

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd chat-api
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Environment setup**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run the application**:
   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Open frontend**:
   - Navigate to `frontend/index.html` in your browser
   - Or serve with a simple HTTP server: `python -m http.server 8080`

### Option 2: Docker Deployment

1. **Start all services**:
   ```bash
   docker-compose up -d
   ```

2. **Access the application**:
   - API: http://localhost:8000
   - Frontend: Open `frontend/index.html` in your browser

## 📚 API Documentation

Once running, visit http://localhost:8000/docs for interactive API documentation.

### Key Endpoints

- `POST /register` - User registration
- `POST /login` - User authentication
- `GET /users/me` - Get current user info
- `POST /chat-rooms` - Create chat room
- `GET /chat-rooms/{room_id}/messages` - Get room messages
- `WS /ws/{room_id}` - WebSocket connection for real-time chat

### Authentication

All protected endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

## 🎨 Frontend Features

- **Responsive Design**: Works on desktop and mobile
- **Real-time Updates**: Instant message delivery
- **User Management**: Login, register, and logout
- **Room Management**: Create and join chat rooms
- **Modern UI**: Clean, intuitive interface
- **Toast Notifications**: User feedback and alerts

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./chat.db` |
| `SECRET_KEY` | JWT secret key | `your-secret-key-change-in-production` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration time | `30` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |

### Database Options

- **SQLite** (default): `DATABASE_URL=sqlite:///./chat.db`
- **PostgreSQL**: `DATABASE_URL=postgresql://user:password@localhost/chatdb`

## 🐳 Docker Commands

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f chat-api

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build

# Clean up volumes
docker-compose down -v
```

## 🧪 Testing

### Manual Testing

1. Start the backend server
2. Open the frontend in multiple browser tabs
3. Register different users
4. Create chat rooms and test messaging

### API Testing

Use the interactive docs at http://localhost:8000/docs or tools like:
- Postman
- Insomnia
- curl commands

## 🔒 Security Features

- **Password Hashing**: bcrypt with salt
- **JWT Tokens**: Secure authentication
- **CORS Protection**: Configurable origins
- **Input Validation**: Pydantic schemas
- **SQL Injection Protection**: SQLAlchemy ORM

## 📱 Browser Support

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## 🚀 Production Deployment

### Environment Setup

1. Set strong `SECRET_KEY`
2. Use PostgreSQL for production database
3. Configure proper CORS origins
4. Set up SSL/TLS certificates
5. Use reverse proxy (nginx)

### Scaling Considerations

- Redis for session management
- Database connection pooling
- Load balancing for multiple instances
- WebSocket scaling with Redis pub/sub

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Issues**: Create a GitHub issue
- **Documentation**: Check the API docs at `/docs`
- **Community**: Join our discussions

---

**Happy Chatting! 💬**
