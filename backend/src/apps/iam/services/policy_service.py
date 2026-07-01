# app/services/policy_service.py

from typing import List, Dict
from src.core.enums import RBACRole, ProjectRole
from ..casbin import enforcer
from src.apps.iam.models import User


class PolicyService:

    # -------------------------------------------------------------------------
    # Authorization Check (Unified Request Evaluation)
    # -------------------------------------------------------------------------

    @staticmethod
    def has_permission(
        user: User,
        org_slug: str,
        module: str,
        action: str,
        project_id: str | None = None,
    ) -> bool:
        """
        Evaluates permissions across the unified track: (user, org, project, module, action).
        If no project_id is provided, a placeholder token "none" is passed.
        """
        if user.is_superuser:
            return True
        
        project_domain = f"proj_{project_id}" if project_id else "none"
        
        return enforcer.enforce(
            str(user.id),
            org_slug,
            project_domain,
            module,
            action,
        )

    # -------------------------------------------------------------------------
    # Permission Policies (Org vs Project Layers)
    # -------------------------------------------------------------------------

    @staticmethod
    def add_org_permission(role: str, org_slug: str, module: str, action: str) -> bool:
        return enforcer.add_policy(role, org_slug, module, action)

    @staticmethod
    def remove_org_permission(role: str, org_slug: str, module: str, action: str) -> bool:
        return enforcer.remove_policy(role, org_slug, module, action)

    @staticmethod
    def add_project_permission(role: str, project_id: str, module: str, action: str) -> bool:
        return enforcer.add_policy(role, f"proj_{project_id}", module, action)

    @staticmethod
    def remove_project_permission(role: str, project_id: str, module: str, action: str) -> bool:
        return enforcer.remove_policy(role, f"proj_{project_id}", module, action)

    @staticmethod
    def get_direct_permissions(role: str, domain: str) -> List[List[str]]:
        """Gets direct permissions for a role inside a domain (org_slug or proj_{project_id})."""
        return enforcer.get_filtered_policy(0, role, domain)

    # -------------------------------------------------------------------------
    # User <-> Organization Role Mapping
    # -------------------------------------------------------------------------

    @staticmethod
    def assign_org_role(user_id: int, role: RBACRole, org_slug: str) -> bool:
        return enforcer.add_grouping_policy(str(user_id), role.value, org_slug)

    @staticmethod
    def revoke_org_role(user_id: int, role: RBACRole, org_slug: str) -> bool:
        return enforcer.remove_grouping_policy(str(user_id), role.value, org_slug)

    @staticmethod
    def get_user_org_roles(user_id: int, org_slug: str) -> List[RBACRole]:
        """
        Efficiently fetches strongly-typed ORG roles for a single user.
        O(1) lookup against Casbin indexes.
        """
        roles = enforcer.get_roles_for_user_in_domain(str(user_id), org_slug)
        typed_roles: List[RBACRole] = []
        
        for role in roles:
            try:
                typed_roles.append(RBACRole(role))
            except ValueError:
                continue
                
        return typed_roles
    
    @staticmethod
    def remove_user_from_org(user_id: int, org_slug: str) -> bool:
        roles = enforcer.get_roles_for_user_in_domain(str(user_id), org_slug)
        result = enforcer.delete_roles_for_user_in_domain(str(user_id), roles, org_slug)
        return bool(result) 
    # -------------------------------------------------------------------------
    # User <-> Project Role Mapping (New Resource Layer)
    # -------------------------------------------------------------------------

    @staticmethod
    def assign_project_role(user_id: int, role: ProjectRole, project_id: str) -> bool:
        """Binds a user to a specific project-level security role contextualized by project domain."""
        return enforcer.add_grouping_policy(str(user_id), role.value, f"proj_{project_id}")

    @staticmethod
    def revoke_project_role(user_id: int, role: ProjectRole, project_id: str) -> bool:
        """Revokes a user's project-level security role inside a project domain."""
        return enforcer.remove_grouping_policy(str(user_id), role.value, f"proj_{project_id}")

    @staticmethod
    def get_user_project_roles(user_id: int, project_id: str) -> List[ProjectRole]:
        """
        Efficiently fetches strongly-typed PROJECT roles for a single user.
        O(1) lookup against Casbin indexes.
        """
        roles = enforcer.get_roles_for_user_in_domain(str(user_id), f"proj_{project_id}")
        typed_roles: List[ProjectRole] = []
        
        for role in roles:
            try:
                typed_roles.append(ProjectRole(role))
            except ValueError:
                continue
                
        return typed_roles
    
    @staticmethod
    def remove_user_from_project(user_id: int, project_id: str) -> bool:
        """Completely purges a user's roles from a specific project domain."""
        roles = enforcer.get_roles_for_user_in_domain(str(user_id), f"proj_{project_id}")
        result = enforcer.delete_roles_for_user_in_domain(str(user_id), roles, f"proj_{project_id}")
        return bool(result) 
    # -------------------------------------------------------------------------
    # Implicit Permission Resolution
    # -------------------------------------------------------------------------

    @staticmethod
    def get_user_implicit_permissions(user_id: int, domain: str) -> List[List[str]]:
        """
        Retrieves all resolved/inherited permissions for a user within a target domain floor.
        Provide either `org_slug` or `proj_{project_id}` as the domain parameter.
        """
        return enforcer.get_implicit_permissions_for_user(str(user_id), domain)

    # -------------------------------------------------------------------------
    # Role Inheritance
    # -------------------------------------------------------------------------

    @staticmethod
    def inherit_role(role: str, parent_role: str, domain: str) -> bool:
        return enforcer.add_grouping_policy(role, parent_role, domain)
    
    @staticmethod
    def remove_role_inheritance(role: str, parent_role: str, domain: str) -> bool:
        return enforcer.remove_grouping_policy(role, parent_role, domain)

    # -------------------------------------------------------------------------
    # Management & Validation Utilities
    # -------------------------------------------------------------------------

    @staticmethod
    def get_org_members_map(org_slug: str) -> Dict[int, List[RBACRole]]:
        """
        Returns a mapped ledger of users and their strongly-typed ORG roles.
        """
        policies = enforcer.get_filtered_grouping_policy(2, org_slug)
        role_map: Dict[int, List[RBACRole]] = {}
        
        for user_id, role, _org in policies:
            try:
                role_enum = RBACRole(role)
                role_map.setdefault(int(user_id), []).append(role_enum)
            except ValueError:
                # Log or skip if a role string exists in Casbin but isn't in our application enum
                continue
                
        return role_map
    
    @staticmethod
    def get_project_members_map(project_id: str) -> Dict[int, List[ProjectRole]]:
        """
        Returns a mapped ledger of users and their strongly-typed PROJECT roles.
        """
        policies = enforcer.get_filtered_grouping_policy(2, f"proj_{project_id}")
        role_map: Dict[int, List[ProjectRole]] = {}
        
        for user_id, role, _domain in policies:
            try:
                role_enum = ProjectRole(role)
                role_map.setdefault(int(user_id), []).append(role_enum)
            except ValueError:
                # Log or skip if an invalid/old role string is found
                continue
                
        return role_map
    
    @staticmethod
    def is_org_member(user: User, org_slug: str) -> bool:
        if user.is_superuser:
            return True
        user_roles = enforcer.get_roles_for_user_in_domain(str(user.id), org_slug)
        return len(user_roles) > 0

    @staticmethod
    def is_project_member(user: User, project_id: str) -> bool:
        """Verifies if a user holds an explicit membership role on the target project footprint."""
        if user.is_superuser:
            return True
        project_roles = enforcer.get_roles_for_user_in_domain(str(user.id), f"proj_{project_id}")
        return len(project_roles) > 0
    
    @staticmethod
    def can_access_org_role(user: User, org_slug: str, required_role: RBACRole) -> bool:
        if user.is_superuser:
            return True
        user_roles = enforcer.get_roles_for_user_in_domain(str(user.id), org_slug)
        return required_role.value in user_roles

    @staticmethod
    def can_access_project_role(user: User, project_id: str, required_role: ProjectRole) -> bool:
        """Verifies if a user explicitly matches a target project permission role."""
        if user.is_superuser:
            return True
        project_roles = enforcer.get_roles_for_user_in_domain(str(user.id), f"proj_{project_id}")
        return required_role.value in project_roles