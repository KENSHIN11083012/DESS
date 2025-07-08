"""
Tests para la funcionalidad de perfil de usuario
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from core.entities.user import User, UserRole
from core.use_cases.profile_use_cases import (
    GetUserProfileUseCase,
    UpdateUserProfileUseCase,
    ChangePasswordUseCase,
    GetUserActivityUseCase,
    ValidateUserDataUseCase
)
from application.services.profile_service import ProfileService


class TestGetUserProfileUseCase:
    """Tests para el caso de uso GetUserProfile"""
    
    def test_execute_success(self):
        """Test obtener perfil exitosamente"""
        # Arrange
        user_repo = Mock()
        user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.USER,
            password="password123",
            is_active=True,
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 2)
        )
        user_repo.find_by_id.return_value = user
        
        use_case = GetUserProfileUseCase(user_repo)
        
        # Act
        result = use_case.execute(1)
        
        # Assert
        assert result['id'] == 1
        assert result['username'] == "testuser"
        assert result['email'] == "test@example.com"
        assert result['full_name'] == "Test User"
        assert result['role'] == "user"
        assert result['is_active'] is True
        assert result['profile_completion'] == 100
        assert 'permissions' in result
        user_repo.find_by_id.assert_called_once_with(1)
    
    def test_execute_user_not_found(self):
        """Test usuario no encontrado"""
        # Arrange
        user_repo = Mock()
        user_repo.find_by_id.return_value = None
        use_case = GetUserProfileUseCase(user_repo)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Usuario con ID 1 no encontrado"):
            use_case.execute(1)
    
    def test_calculate_profile_completion(self):
        """Test cálculo de completitud del perfil"""
        # Arrange
        user_repo = Mock()
        user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.USER,
            password="password123",
            is_active=True
        )
        user_repo.find_by_id.return_value = user
        
        use_case = GetUserProfileUseCase(user_repo)
        
        # Act
        completion = use_case._calculate_profile_completion(user)
        
        # Assert
        assert completion == 100
    
    def test_get_user_permissions_regular_user(self):
        """Test permisos de usuario regular"""
        # Arrange
        user_repo = Mock()
        user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.USER,
            password="password123",
            is_active=True
        )
        
        use_case = GetUserProfileUseCase(user_repo)
        
        # Act
        permissions = use_case._get_user_permissions(user)
        
        # Assert
        assert permissions['can_manage_users'] is False
        assert permissions['can_manage_solutions'] is False
        assert permissions['can_view_dashboard'] is True
        assert permissions['can_edit_profile'] is True
        assert permissions['can_change_password'] is True
    
    def test_get_user_permissions_super_admin(self):
        """Test permisos de super admin"""
        # Arrange
        user_repo = Mock()
        user = User(
            id=1,
            username="admin",
            email="admin@example.com",
            full_name="Super Admin",
            role=UserRole.SUPER_ADMIN,
            password="password123",
            is_active=True
        )
        
        use_case = GetUserProfileUseCase(user_repo)
        
        # Act
        permissions = use_case._get_user_permissions(user)
        
        # Assert
        assert permissions['can_manage_users'] is True
        assert permissions['can_manage_solutions'] is True
        assert permissions['can_view_dashboard'] is True
        assert permissions['can_edit_profile'] is True
        assert permissions['can_change_password'] is True


class TestUpdateUserProfileUseCase:
    """Tests para el caso de uso UpdateUserProfile"""
    
    def test_execute_success(self):
        """Test actualizar perfil exitosamente"""
        # Arrange
        user_repo = Mock()
        user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.USER,
            password="password123",
            is_active=True
        )
        user_repo.find_by_id.return_value = user
        user_repo.exists_by_email.return_value = False
        user_repo.save.return_value = user
        
        use_case = UpdateUserProfileUseCase(user_repo)
        
        # Act
        updates = {'email': 'newemail@example.com', 'full_name': 'New Name'}
        result = use_case.execute(1, updates)
        
        # Assert
        assert result.email == 'newemail@example.com'
        assert result.full_name == 'New Name'
        user_repo.save.assert_called_once()
    
    def test_execute_user_not_found(self):
        """Test usuario no encontrado"""
        # Arrange
        user_repo = Mock()
        user_repo.find_by_id.return_value = None
        use_case = UpdateUserProfileUseCase(user_repo)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Usuario con ID 1 no encontrado"):
            use_case.execute(1, {'email': 'test@example.com'})
    
    def test_execute_email_already_exists(self):
        """Test email ya existe"""
        # Arrange
        user_repo = Mock()
        user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.USER,
            password="password123"
        )
        user_repo.find_by_id.return_value = user
        user_repo.exists_by_email.return_value = True
        
        use_case = UpdateUserProfileUseCase(user_repo)
        
        # Act & Assert
        with pytest.raises(ValueError, match="El email 'newemail@example.com' ya está en uso"):
            use_case.execute(1, {'email': 'newemail@example.com'})


class TestChangePasswordUseCase:
    """Tests para el caso de uso ChangePassword"""
    
    def test_execute_success(self):
        """Test cambiar contraseña exitosamente"""
        # Arrange
        user_repo = Mock()
        user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.USER,
            password="oldpassword"
        )
        user_repo.find_by_id.return_value = user
        user_repo.save.return_value = user
        
        use_case = ChangePasswordUseCase(user_repo)
        
        # Act
        result = use_case.execute(1, "oldpassword", "newpassword123")
        
        # Assert
        assert result is True
        user_repo.save.assert_called_once()
    
    def test_execute_user_not_found(self):
        """Test usuario no encontrado"""
        # Arrange
        user_repo = Mock()
        user_repo.find_by_id.return_value = None
        use_case = ChangePasswordUseCase(user_repo)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Usuario con ID 1 no encontrado"):
            use_case.execute(1, "old", "new")
    
    def test_execute_wrong_current_password(self):
        """Test contraseña actual incorrecta"""
        # Arrange
        user_repo = Mock()
        user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.USER,
            password="correctpassword"
        )
        user_repo.find_by_id.return_value = user
        
        use_case = ChangePasswordUseCase(user_repo)
        
        # Act & Assert
        with pytest.raises(ValueError, match="La contraseña actual es incorrecta"):
            use_case.execute(1, "wrongpassword", "newpassword123")
    
    def test_execute_same_password(self):
        """Test nueva contraseña igual a la actual"""
        # Arrange
        user_repo = Mock()
        user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.USER,
            password="samepassword"
        )
        user_repo.find_by_id.return_value = user
        
        use_case = ChangePasswordUseCase(user_repo)
        
        # Act & Assert
        with pytest.raises(ValueError, match="La nueva contraseña debe ser diferente a la actual"):
            use_case.execute(1, "samepassword", "samepassword")


class TestValidateUserDataUseCase:
    """Tests para el caso de uso ValidateUserData"""
    
    def test_validate_username_success(self):
        """Test validar username exitosamente"""
        # Arrange
        user_repo = Mock()
        user_repo.find_by_username.return_value = None
        use_case = ValidateUserDataUseCase(user_repo)
        
        # Act
        result = use_case.execute_username("validuser")
        
        # Assert
        assert result['valid'] is True
        assert result['message'] == "Nombre de usuario disponible"
    
    def test_validate_username_too_short(self):
        """Test username muy corto"""
        # Arrange
        user_repo = Mock()
        use_case = ValidateUserDataUseCase(user_repo)
        
        # Act
        result = use_case.execute_username("ab")
        
        # Assert
        assert result['valid'] is False
        assert "al menos 3 caracteres" in result['message']
    
    def test_validate_username_already_exists(self):
        """Test username ya existe"""
        # Arrange
        user_repo = Mock()
        existing_user = User(
            id=2,
            username="existinguser",
            email="existing@example.com",
            full_name="Existing User",
            role=UserRole.USER,
            password="password123"
        )
        user_repo.find_by_username.return_value = existing_user
        use_case = ValidateUserDataUseCase(user_repo)
        
        # Act
        result = use_case.execute_username("existinguser")
        
        # Assert
        assert result['valid'] is False
        assert "ya está en uso" in result['message']
    
    def test_validate_email_success(self):
        """Test validar email exitosamente"""
        # Arrange
        user_repo = Mock()
        user_repo.find_by_email.return_value = None
        use_case = ValidateUserDataUseCase(user_repo)
        
        # Act
        result = use_case.execute_email("valid@example.com")
        
        # Assert
        assert result['valid'] is True
        assert result['message'] == "Email válido"
    
    def test_validate_email_invalid_format(self):
        """Test formato de email inválido"""
        # Arrange
        user_repo = Mock()
        use_case = ValidateUserDataUseCase(user_repo)
        
        # Act
        result = use_case.execute_email("invalid-email")
        
        # Assert
        assert result['valid'] is False
        assert "Formato de email inválido" in result['message']


class TestProfileService:
    """Tests para el servicio de perfil"""
    
    def test_get_user_profile_success(self):
        """Test obtener perfil exitosamente"""
        # Arrange
        get_profile_mock = Mock()
        update_profile_mock = Mock()
        change_password_mock = Mock()
        get_activity_mock = Mock()
        validate_data_mock = Mock()
        
        profile_data = {'id': 1, 'username': 'test'}
        get_profile_mock.execute.return_value = profile_data
        
        service = ProfileService(
            get_profile_mock,
            update_profile_mock,
            change_password_mock,
            get_activity_mock,
            validate_data_mock
        )
        
        # Act
        result = service.get_user_profile(1)
        
        # Assert
        assert result == profile_data
        get_profile_mock.execute.assert_called_once_with(1)
    
    def test_update_profile_with_validation_success(self):
        """Test actualizar perfil con validación exitosa"""
        # Arrange
        get_profile_mock = Mock()
        update_profile_mock = Mock()
        change_password_mock = Mock()
        get_activity_mock = Mock()
        validate_data_mock = Mock()
        
        user = User(
            id=1,
            username="testuser",
            email="new@example.com",
            full_name="New Name",
            role=UserRole.USER,
            password="password123"
        )
        
        validate_data_mock.execute_email.return_value = {'valid': True, 'message': 'Valid'}
        update_profile_mock.execute.return_value = user
        
        service = ProfileService(
            get_profile_mock,
            update_profile_mock,
            change_password_mock,
            get_activity_mock,
            validate_data_mock
        )
        
        # Act
        updates = {'email': 'new@example.com', 'full_name': 'New Name'}
        result = service.update_profile(1, updates)
        
        # Assert
        assert result == user
        validate_data_mock.execute_email.assert_called_once_with('new@example.com', 1)
        update_profile_mock.execute.assert_called_once_with(1, updates)
    
    def test_update_profile_validation_fails(self):
        """Test actualizar perfil con validación fallida"""
        # Arrange
        get_profile_mock = Mock()
        update_profile_mock = Mock()
        change_password_mock = Mock()
        get_activity_mock = Mock()
        validate_data_mock = Mock()
        
        validate_data_mock.execute_email.return_value = {'valid': False, 'message': 'Email already exists'}
        
        service = ProfileService(
            get_profile_mock,
            update_profile_mock,
            change_password_mock,
            get_activity_mock,
            validate_data_mock
        )
        
        # Act & Assert
        with pytest.raises(Exception, match="Error al actualizar perfil"):
            service.update_profile(1, {'email': 'existing@example.com'})
    
    def test_get_profile_summary_success(self):
        """Test obtener resumen de perfil exitosamente"""
        # Arrange
        get_profile_mock = Mock()
        update_profile_mock = Mock()
        change_password_mock = Mock()
        get_activity_mock = Mock()
        validate_data_mock = Mock()
        
        profile_data = {
            'username': 'testuser',
            'full_name': 'Test User',
            'email': 'test@example.com',
            'role': 'user',
            'is_active': True,
            'profile_completion': 85,
            'permissions': {'can_edit_profile': True}
        }
        
        activity_data = {
            'last_login': datetime(2024, 1, 1),
            'account_age_days': 30
        }
        
        get_profile_mock.execute.return_value = profile_data
        get_activity_mock.execute.return_value = activity_data
        
        service = ProfileService(
            get_profile_mock,
            update_profile_mock,
            change_password_mock,
            get_activity_mock,
            validate_data_mock
        )
        
        # Act
        result = service.get_profile_summary(1)
        
        # Assert
        assert 'basic_info' in result
        assert 'status' in result
        assert 'permissions' in result
        assert result['basic_info']['username'] == 'testuser'
        assert result['status']['profile_completion'] == 85
