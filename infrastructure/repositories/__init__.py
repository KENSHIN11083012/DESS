"""
Implementaciones concretas de repositorios usando Django ORM
"""
from .django_user_repository import DjangoUserRepository
from .django_solution_repository import DjangoSolutionRepository
from .django_solution_assignment_repository import DjangoSolutionAssignmentRepository

__all__ = [
    'DjangoUserRepository',
    'DjangoSolutionRepository', 
    'DjangoSolutionAssignmentRepository',
]