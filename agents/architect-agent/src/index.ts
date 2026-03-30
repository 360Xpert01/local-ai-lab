import Fastify from 'fastify';
import cors from '@fastify/cors';

const fastify = Fastify({
  logger: true
});

// Register CORS
await fastify.register(cors, {
  origin: '*'
});

// Types
interface TaskRequest {
  task_id: string;
  description: string;
  files: string[];
  context?: Record<string, any>;
}

interface TaskResponse {
  task_id: string;
  status: string;
  result?: string;
  error?: string;
  artifacts?: {
    diagrams?: string[];
    documentation?: string;
    api_spec?: string;
  };
}

interface DesignRequest {
  system_name: string;
  requirements: string[];
  constraints?: string[];
  tech_stack?: string[];
}

// Health check
fastify.get('/health', async () => {
  return {
    status: 'healthy',
    agent: 'architect',
    capabilities: [
      'system_design',
      'api_design',
      'database_schema',
      'architecture_patterns',
      'diagram_generation'
    ]
  };
});

// Execute task
fastify.post<{ Body: TaskRequest }>('/execute', async (request, reply) => {
  const { task_id, description, files, context } = request.body;
  
  fastify.log.info(`Processing task: ${task_id}`);
  
  const desc = description.toLowerCase();
  
  if (desc.includes('api') || desc.includes('endpoint')) {
    return generateApiDesign(task_id, description);
  }
  
  if (desc.includes('database') || desc.includes('schema')) {
    return generateDatabaseSchema(task_id, description);
  }
  
  if (desc.includes('design') || desc.includes('architecture')) {
    return generateSystemDesign(task_id, description, context);
  }
  
  // Default response
  const response: TaskResponse = {
    task_id,
    status: 'completed',
    result: `Architect Agent received task: ${description}\n\n` +
            'I specialize in:\n' +
            '- System architecture design\n' +
            '- API design (REST, GraphQL, gRPC)\n' +
            '- Database schema design\n' +
            '- Architecture patterns\n' +
            '- Mermaid diagram generation'
  };
  
  return response;
});

// Generate API design
fastify.post<{ Body: DesignRequest }>('/design/api', async (request) => {
  return generateApiSpec(request.body);
});

// Generate system design
fastify.post<{ Body: DesignRequest }>('/design/system', async (request) => {
  return generateSystemArchitecture(request.body);
});

// Generate database schema
fastify.post<{ Body: DesignRequest }>('/design/database', async (request) => {
  return generateDatabaseDesign(request.body);
});

function generateApiDesign(taskId: string, description: string): TaskResponse {
  const apiSpec = `# API Design

## Overview
RESTful API designed for scalability and maintainability.

## Endpoints

### GET /api/v1/resources
Retrieve a list of resources.

**Response:**
\`\`\`json
{
  "data": [],
  "meta": {
    "total": 0,
    "page": 1,
    "per_page": 20
  }
}
\`\`\`

### POST /api/v1/resources
Create a new resource.

**Request Body:**
\`\`\`json
{
  "name": "string",
  "description": "string"
}
\`\`\`

### GET /api/v1/resources/:id
Retrieve a specific resource.

### PUT /api/v1/resources/:id
Update a resource.

### DELETE /api/v1/resources/:id
Delete a resource.

## Authentication
JWT-based authentication required for all endpoints.

## Rate Limiting
100 requests per minute per API key.`;

  return {
    task_id: taskId,
    status: 'completed',
    result: `API design generated for: ${description}`,
    artifacts: {
      api_spec: apiSpec,
      diagrams: [
        generateMermaidDiagram()
      ]
    }
  };
}

function generateDatabaseSchema(taskId: string, description: string): TaskResponse {
  const schema = `-- Database Schema (PostgreSQL)

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Resources table
CREATE TABLE resources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_resources_user_id ON resources(user_id);
CREATE INDEX idx_resources_status ON resources(status);

-- Triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$\nBEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_resources_updated_at BEFORE UPDATE ON resources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();`;

  return {
    task_id: taskId,
    status: 'completed',
    result: `Database schema generated for: ${description}`,
    artifacts: {
      documentation: schema,
      diagrams: [generateERDiagram()]
    }
  };
}

function generateSystemDesign(
  taskId: string, 
  description: string, 
  context?: Record<string, any>
): TaskResponse {
  const architecture = `# System Architecture

## Components

### 1. API Gateway
- Rate limiting
- Authentication
- Request routing
- Load balancing

### 2. Application Services
- Stateless design
- Horizontal scaling
- Containerized deployment

### 3. Data Layer
- Primary database: PostgreSQL
- Cache: Redis
- Search: Elasticsearch (optional)

### 4. Message Queue
- Async processing
- Event-driven architecture
- RabbitMQ or Kafka

## Scalability Strategy

1. **Horizontal Scaling**: Deploy multiple service instances
2. **Database Sharding**: Partition data by tenant/region
3. **Caching**: Multi-layer caching strategy
4. **CDN**: Static assets served via CDN

## Security

- TLS 1.3 for all communications
- API authentication via JWT
- Database encryption at rest
- Network isolation with VPC`;

  return {
    task_id: taskId,
    status: 'completed',
    result: `System architecture designed for: ${description}`,
    artifacts: {
      documentation: architecture,
      diagrams: [
        generateArchitectureDiagram(),
        generateMermaidDiagram()
      ]
    }
  };
}

function generateApiSpec(design: DesignRequest): any {
  return {
    openapi: '3.0.0',
    info: {
      title: `${design.system_name} API`,
      version: '1.0.0'
    },
    paths: {
      '/api/v1/items': {
        get: {
          summary: 'List items',
          responses: {
            '200': {
              description: 'Success'
            }
          }
        }
      }
    }
  };
}

function generateSystemArchitecture(design: DesignRequest): any {
  return {
    architecture: 'microservices',
    components: ['api-gateway', 'auth-service', 'core-service', 'worker'],
    database: 'postgresql',
    cache: 'redis',
    message_queue: 'rabbitmq'
  };
}

function generateDatabaseDesign(design: DesignRequest): any {
  return {
    tables: ['users', 'resources', 'audit_logs'],
    relationships: [
      { from: 'resources', to: 'users', type: 'many-to-one' }
    ]
  };
}

function generateMermaidDiagram(): string {
  return `\`\`\`mermaid
graph TB
    Client[Client Application]
    Gateway[API Gateway]
    Auth[Auth Service]
    API[Core API]
    DB[(Database)]
    Cache[(Redis Cache)]
    
    Client -->|HTTPS| Gateway
    Gateway -->|Validate| Auth
    Gateway -->|Route| API
    API -->|Read/Write| DB
    API -->|Cache| Cache
\`\`\``;
}

function generateERDiagram(): string {
  return `\`\`\`mermaid
erDiagram
    USER ||--o{ RESOURCE : owns
    USER {
        uuid id PK
        string email
        string username
        datetime created_at
    }
    RESOURCE {
        uuid id PK
        uuid user_id FK
        string name
        string status
    }
\`\`\``;
}

function generateArchitectureDiagram(): string {
  return `\`\`\`mermaid
graph LR
    subgraph "Client Layer"
        Web[Web App]
        Mobile[Mobile App]
    end
    
    subgraph "API Layer"
        LB[Load Balancer]
        Gateway[API Gateway]
    end
    
    subgraph "Service Layer"
        S1[Service 1]
        S2[Service 2]
        S3[Service 3]
    end
    
    subgraph "Data Layer"
        DB1[(Primary DB)]
        DB2[(Read Replica)]
        Cache[(Cache)]
    end
    
    Web --> LB
    Mobile --> LB
    LB --> Gateway
    Gateway --> S1
    Gateway --> S2
    Gateway --> S3
    S1 --> DB1
    S2 --> DB2
    S3 --> Cache
\`\`\``;
}

// Start server
try {
  await fastify.listen({ port: 8083, host: '0.0.0.0' });
  console.log('Architect Agent running on http://localhost:8083');
} catch (err) {
  fastify.log.error(err);
  process.exit(1);
}
