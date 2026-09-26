import logging
from typing import List, Optional, Dict, Any
from core.base_service import BaseService
from models.employee import Employee
from repositories.employee_repository import EmployeeRepository
from core.base_model import generate_uuid

logger = logging.getLogger(__name__)

class EmployeeService(BaseService):
    """Service for managing employees in the travel agency."""

    def __init__(self):
        super().__init__()

    def search_employees(
        self,
        query: str = "",
        fields: list[str] | None = None,
        skip: int = 0,
        limit: int = 50
    ):
        """
        Search employees with pagination, sorting, and field filtering.
        """
        with self._get_session() as session:
            repo = EmployeeRepository(session)
            return repo.search_employees(
                query=query,
                fields=fields,
                skip=skip,
                limit=limit
            )

    def create_employee(self, employee_data: Dict[str, Any], created_by: Optional[str] = None) -> Employee:
        """
        Creates a new employee.
        """
        self.validate_required(employee_data, ['first_name', 'phone', 'date_joined'])
        
        login_data = employee_data.pop('login_data', None)
        
        with self._get_session() as session:
            repo = EmployeeRepository(session)
            
            # Auto-generate employee code if not provided
            if 'employee_code' not in employee_data or not employee_data['employee_code']:
                count = repo.get_count()
                employee_data['employee_code'] = f"EMP-{count + 1:04d}"
                
            # Check unique fields
            if 'cnic' in employee_data and employee_data['cnic']:
                self.validate_unique(session, Employee, 'cnic', employee_data['cnic'])
            if 'email' in employee_data and employee_data['email']:
                self.validate_unique(session, Employee, 'email', employee_data['email'])
                
            # Create instance
            employee = Employee(id=generate_uuid(), created_by=created_by)
            for key, value in employee_data.items():
                if hasattr(employee, key):
                    setattr(employee, key, value)
                    
            if login_data:
                from models.user import User
                from utils.encryption import hash_password
                
                if not login_data.get('password'):
                    raise ValueError("Password is required to create a new login account.")
                
                # Verify username doesn't already exist
                existing = session.query(User).filter_by(username=login_data['username'].lower()).first()
                if existing:
                    raise ValueError(f"Username {login_data['username']} is already taken.")
                
                new_user = User(
                    id=generate_uuid(),
                    username=login_data['username'].lower(),
                    password_hash=hash_password(login_data['password']),
                    full_name=f"{employee.first_name} {employee.last_name}".strip(),
                    role='Employee',
                    permissions=login_data.get('permissions', {}),
                    created_by=created_by
                )
                session.add(new_user)
                session.flush() # get user ID
                employee.user_id = new_user.id
                    
            repo.add(employee)
            session.commit()
            session.refresh(employee)
            logger.info(f"Created employee: {employee.full_name} ({employee.employee_code})")
            return employee

    def get_employee_by_id(self, employee_id: str) -> Optional[Employee]:
        """
        Retrieves an employee by ID.
        """
        with self._get_session() as session:
            repo = EmployeeRepository(session)
            return repo.get_by_id(employee_id)

    def update_employee(self, employee_id: str, employee_data: Dict[str, Any], updated_by: Optional[str] = None) -> Employee:
        """
        Updates an existing employee.
        """
        login_data = employee_data.pop('login_data', None)
        
        with self._get_session() as session:
            repo = EmployeeRepository(session)
            employee = repo.get_by_id(employee_id)
            if not employee:
                raise ValueError(f"Employee with ID {employee_id} not found.")
                
            # Check unique fields
            if 'cnic' in employee_data and employee_data['cnic']:
                self.validate_unique(session, Employee, 'cnic', employee_data['cnic'], exclude_id=employee_id)
            if 'email' in employee_data and employee_data['email']:
                self.validate_unique(session, Employee, 'email', employee_data['email'], exclude_id=employee_id)
                
            for key, value in employee_data.items():
                if hasattr(employee, key) and key not in ('id', 'created_at', 'created_by', 'employee_code', 'user_id'):
                    setattr(employee, key, value)
                    
            if login_data:
                from models.user import User
                from utils.encryption import hash_password
                
                if employee.user_id:
                    user = session.query(User).filter_by(id=employee.user_id).first()
                    if user:
                        # Update existing user
                        if login_data.get('password'):
                            user.password_hash = hash_password(login_data['password'])
                        if login_data.get('permissions'):
                            user.permissions = login_data['permissions']
                else:
                    if not login_data.get('password'):
                        raise ValueError("Password is required to create a new login account.")
                        
                    # Verify username doesn't already exist
                    existing = session.query(User).filter_by(username=login_data['username'].lower()).first()
                    if existing:
                        raise ValueError(f"Username {login_data['username']} is already taken.")
                    
                    new_user = User(
                        id=generate_uuid(),
                        username=login_data['username'].lower(),
                        password_hash=hash_password(login_data['password']),
                        full_name=f"{employee.first_name} {employee.last_name}".strip(),
                        role='Employee',
                        permissions=login_data.get('permissions', {}),
                        created_by=updated_by
                    )
                    session.add(new_user)
                    session.flush()
                    employee.user_id = new_user.id
                    
            employee.updated_by = updated_by
            repo.update(employee)
            session.commit()
            session.refresh(employee)
            logger.info(f"Updated employee ID {employee_id}")
            return employee

    def delete_employee(self, employee_id: str, deleted_by: Optional[str] = None) -> bool:
        """
        Soft deletes an employee.
        """
        with self._get_session() as session:
            repo = EmployeeRepository(session)
            employee = repo.get_by_id(employee_id)
            if not employee:
                raise ValueError(f"Employee with ID {employee_id} not found.")
            
            repo.soft_delete(employee, deleted_by=deleted_by)
            session.commit()
            logger.info(f"Deleted employee ID {employee_id}")
            return True
