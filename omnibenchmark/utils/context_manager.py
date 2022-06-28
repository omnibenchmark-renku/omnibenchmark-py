"""General context manager used in omnibenchmark"""

from renku.ui.api.models.project import Project
from renku.command.command_builder.database_dispatcher import DatabaseDispatcher
from renku.infrastructure.gateway.activity_gateway import ActivityGateway
from renku.infrastructure.gateway.plan_gateway import PlanGateway


def get_database_dispatcher() -> DatabaseDispatcher:
    """Configure database from project

    Returns:
        DatabaseDispatcher: A renku database dispatcher to find project metadata.
    """
    # Get project context
    project = Project()
    client = project.client
    database_dispatcher = DatabaseDispatcher()
    database_dispatcher.push_database_to_stack(client.database_path)
    return database_dispatcher


def configure_activity_gateway() -> ActivityGateway:
    """Configure activity gateway from project

    Returns:
        ActivityGateway: A renku ActivityGateway with the currents project as underlying database.
    """
    # Get project context
    database_dispatcher = get_database_dispatcher()
    activity_gateway = ActivityGateway()
    activity_gateway.database_dispatcher = database_dispatcher
    return activity_gateway


def configure_plan_gateway() -> PlanGateway:
    """Configure plan gateway from project

    Returns:
        PlanGateway: A renku PlanGateway with the currents project as underlying database.
    """
    # Get project context
    database_dispatcher = get_database_dispatcher()
    plan_gateway = PlanGateway()
    plan_gateway.database_dispatcher = database_dispatcher
    return plan_gateway
