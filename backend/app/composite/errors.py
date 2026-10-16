"""Hierarchy errors raised by the Composite domain. Each carries the HTTP status the API should return."""


class HierarchyError(Exception):
    status_code = 400


class InvalidHierarchyOperation(HierarchyError):
    status_code = 400


class CircularHierarchyError(HierarchyError):
    status_code = 409


class DuplicateChildError(HierarchyError):
    status_code = 409
