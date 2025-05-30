"""
Database-related exceptions for the Data Analyzer Agent

Custom exceptions for database operations and connection management.
"""


class DatabaseError(Exception):
    """Base exception for database operations"""
    pass


class DatabaseConnectionError(DatabaseError):
    """Exception raised when database connection fails"""
    pass


class DatabaseQueryError(DatabaseError):
    """Exception raised when database query execution fails"""
    pass


class DatabaseConfigurationError(DatabaseError):
    """Exception raised when database configuration is invalid"""
    pass


class DatabaseTimeoutError(DatabaseError):
    """Exception raised when database operation times out"""
    pass 