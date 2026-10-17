from campus_grid.core.container import Container


def test_container_dependency_wiring(container: Container):
    assert container.db is not None
    assert container.user_repository is not None
    assert container.resource_repository is not None
    assert container.booking_repository is not None
    assert container.audit_log_repository is not None
    assert container.auth_service is not None
    assert container.user_service is not None
    assert container.resource_service is not None
    assert container.booking_service is not None
    assert container.audit_log_service is not None
