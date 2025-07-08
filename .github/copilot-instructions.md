# DESS Copilot Instructions

<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

## Project Context
This is DESS (Desarrollador de Ecosistemas de Soluciones Empresariales) - an enterprise platform for centralizing access and management of business solutions with automated deployment capabilities.

## Architecture Guidelines
- Follow Clean Architecture principles
- Separate core domain logic from infrastructure concerns
- Use dependency injection for repositories and services
- Implement proper error handling and logging

## Code Style
- Use Python type hints consistently
- Follow Django best practices
- Implement proper serializers for API endpoints
- Use pytest for testing with >80% coverage
- Follow PEP 8 style guidelines

## Technology Stack
- Backend: Python 3.11 + Django 4.2 + Django REST Framework
- Database: Oracledb
- Authentication: JWT tokens
- API Documentation: OpenAPI/Swagger with drf-spectacular
- Testing: pytest + pytest-django

## Domain Context
- Users have roles (super_admin, user) with different permissions
- Solutions are business applications that can be deployed automatically
- Super admins manage users and assign solutions
- Regular users see only their assigned solutions
- The platform detects application types and deploys them automatically

## Common Patterns
- Entities in core/entities/ represent business domain objects
- Use cases in core/use_cases/ contain business logic
- Repositories in core/interfaces/ define data access contracts
- Django models in infrastructure/database/ implement persistence
- API views in infrastructure/web/ handle HTTP requests
- Services in application/services/ orchestrate use cases
