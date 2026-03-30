# Framework Training Data

This directory contains training data for various web frameworks and languages.

## Available Frameworks

| Framework | Language | Examples | Topics |
|-----------|----------|----------|--------|
| **Symfony** | PHP | 6 | Controllers, Entities, Services, Forms, Events, API Platform |
| **Django** | Python | 5 | Models, Views, Serializers, Management Commands, Middleware |
| **NestJS** | TypeScript | 5 | Controllers, Services, DTOs, Auth, WebSockets |
| **FeatherJS** | JavaScript | 4 | Services, Hooks, Real-time, Models, External APIs |

## Symfony Examples

### 1. CRUD Controller with Dependency Injection
- Full REST API controller
- Route parameters and validation
- JSON responses
- Best practices for controller structure

### 2. Doctrine Entity with Validation
- ORM mappings
- Validation constraints
- Lifecycle callbacks
- Relationships

### 3. Service with Caching
- Dependency injection
- Redis caching
- Repository pattern
- Event dispatching

### 4. Form with CSRF Protection
- Form types
- Validation
- Security
- Custom options

### 5. Event Subscriber
- Request/response logging
- Security headers
- Performance monitoring

### 6. API Platform Resource
- Auto-generated API
- Custom operations
- Serialization groups
- Validation

## Django Examples

### 1. Model with Relationships
- Foreign keys
- Many-to-many
- Custom managers
- Query optimization

### 2. DRF APIView
- CRUD operations
- Authentication
- Permissions
- Pagination

### 3. Serializers with Validation
- Nested serializers
- Custom validation
- Read-only fields
- Create/update logic

### 4. Management Commands
- Import from CSV/JSON
- Batch processing
- Error handling
- Progress reporting

### 5. Middleware
- Request logging
- CORS handling
- Rate limiting
- Performance tracking

## NestJS Examples

### 1. CRUD Controller with Swagger
- OpenAPI documentation
- Validation pipes
- Route decorators
- Pagination

### 2. Service with TypeORM
- Repository pattern
- Caching with Redis
- Event emitting
- Soft deletes

### 3. DTOs with class-validator
- Input validation
- Swagger decorators
- Transformation
- Nested DTOs

### 4. Authentication & Guards
- JWT strategy
- Local strategy
- Role-based access
- Custom decorators

### 5. WebSocket Gateway
- Real-time communication
- Room management
- Authentication
- Broadcasting

## FeatherJS Examples

### 1. Service with Hooks
- Authentication
- Authorization
- Data validation
- Before/after hooks

### 2. Application Setup
- Express integration
- Socket.io
- Middleware
- Channels

### 3. Custom Service (Stripe)
- External API integration
- Webhook handling
- Error management
- Database sync

### 4. Sequelize Models
- Model definitions
- Relationships
- Validation
- Indexes

## Usage in Training

### Adding More Examples

1. Create a new JSONL file for your framework:
```bash
touch colab_training/training_data/code/myframework.jsonl
```

2. Add examples in Alpaca format:
```json
{"instruction": "Create a controller in MyFramework", "input": "", "output": "...code..."}
```

3. Combine with existing data:
```bash
cat colab_training/training_data/code/*.jsonl > training_data.jsonl
```

### Training a Framework-Specific Agent

```bash
# Create training data with framework focus
cat colab_training/training_data/code/symfony.jsonl > training_data.jsonl

# Generate notebook
lab train start --agent code --base-model qwen2.5-coder-7b-instruct

# Upload to Colab and train
```

### Multi-Framework Training

Train on multiple frameworks simultaneously:
```bash
# Combine all frameworks
cat colab_training/training_data/code/*.jsonl > training_data.jsonl

# Train
lab train start --agent code --steps 150
```

## Best Practices Covered

### PHP/Symfony
- ✅ Dependency injection
- ✅ Doctrine ORM best practices
- ✅ Form validation
- ✅ Security (CSRF, XSS prevention)
- ✅ Event-driven architecture
- ✅ API Platform standards

### Python/Django
- ✅ Model relationships
- ✅ DRF serialization
- ✅ Custom management commands
- ✅ Middleware patterns
- ✅ Database optimization

### TypeScript/NestJS
- ✅ Decorator patterns
- ✅ Dependency injection
- ✅ DTO validation
- ✅ Authentication strategies
- ✅ Real-time with WebSockets

### JavaScript/FeatherJS
- ✅ Hook-based architecture
- ✅ Real-time services
- ✅ External API integration
- ✅ Sequelize ORM
- ✅ Socket.io channels

## Framework Comparison

| Feature | Symfony | Django | NestJS | FeatherJS |
|---------|---------|--------|--------|-----------|
| **Language** | PHP | Python | TypeScript | JavaScript |
| **Architecture** | MVC | MTV | Modular | Service-oriented |
| **ORM** | Doctrine | Django ORM | TypeORM | Sequelize |
| **API** | API Platform | DRF | Built-in | REST + Real-time |
| **DI** | Container | Limited | Full | Service locator |
| **Learning Curve** | Steep | Moderate | Moderate | Easy |

## Contributing

To add examples for a new framework:

1. Follow the Alpaca format
2. Include comprehensive comments
3. Show best practices
4. Add real-world scenarios
5. Validate JSON syntax

Example structure:
```json
{
  "instruction": "Clear task description",
  "input": "Optional context",
  "output": "Complete, working code with comments"
}
```
