"""
Query Parser for Database Operations

Detects database references in user queries and extracts relevant
information for MongoDB operations via MCP.
"""

import re
import logging
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DatabaseReference:
    """Represents a detected database reference in a user query"""
    database: Optional[str] = None
    collection: str = ""
    operation_type: str = "query"  # query, aggregate, count, distinct
    filters: Dict = None
    projection: Dict = None
    limit: int = 1000
    sort: Dict = None
    confidence: float = 0.0

class QueryParser:
    """Parse user queries to detect database operations and extract parameters"""
    
    # Query patterns for different types of database operations
    COLLECTION_PATTERNS = [
        # Direct collection references
        r"analyze\s+(\w+)\s+collection",
        r"query\s+(\w+)\s+(?:collection|table|data)",
        r"get\s+data\s+from\s+(\w+)",
        r"(\w+)\s+collection\s+analysis",
        r"explore\s+(\w+)\s+(?:collection|data)",
        r"examine\s+(\w+)\s+(?:collection|records)",
        r"investigate\s+(\w+)\s+(?:collection|dataset)",
        r"look\s+at\s+(\w+)\s+(?:collection|data)",
        r"review\s+(\w+)\s+(?:collection|records)",
        r"study\s+(\w+)\s+(?:collection|dataset)",
    ]
    
    FILTERED_QUERY_PATTERNS = [
        # Queries with conditions
        r"(\w+)\s+where\s+(\w+)\s*=\s*['\"]?([^'\"]+)['\"]?",
        r"filter\s+(\w+)\s+by\s+(\w+)\s*=\s*['\"]?([^'\"]+)['\"]?",
        r"(\w+)\s+with\s+(\w+)\s+equals?\s+['\"]?([^'\"]+)['\"]?",
        r"(\w+)\s+having\s+(\w+)\s*=\s*['\"]?([^'\"]+)['\"]?",
        r"select\s+.*from\s+(\w+)\s+where\s+(\w+)\s*=\s*['\"]?([^'\"]+)['\"]?",
    ]
    
    AGGREGATION_PATTERNS = [
        # Aggregation operations
        r"aggregate\s+(\w+)\s+by\s+(\w+)",
        r"group\s+(\w+)\s+by\s+(\w+)",
        r"summarize\s+(\w+)\s+by\s+(\w+)",
        r"count\s+(\w+)\s+by\s+(\w+)",
        r"sum\s+(\w+)\s+by\s+(\w+)",
        r"average\s+(\w+)\s+by\s+(\w+)",
        r"total\s+(\w+)\s+by\s+(\w+)",
    ]
    
    TIME_RANGE_PATTERNS = [
        r"(?:in\s+)?last\s+(\d+)\s+(day|week|month|year)s?",
        r"(?:in\s+)?past\s+(\d+)\s+(day|week|month|year)s?",
        r"since\s+(\d{4}-\d{2}-\d{2})",
        r"after\s+(\d{4}-\d{2}-\d{2})",
        r"before\s+(\d{4}-\d{2}-\d{2})",
        r"between\s+(\d{4}-\d{2}-\d{2})\s+and\s+(\d{4}-\d{2}-\d{2})",
    ]
    
    def __init__(self):
        """Initialize the query parser"""
        self.compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict:
        """Compile regex patterns for better performance"""
        return {
            'collection': [re.compile(pattern, re.IGNORECASE) for pattern in self.COLLECTION_PATTERNS],
            'filtered': [re.compile(pattern, re.IGNORECASE) for pattern in self.FILTERED_QUERY_PATTERNS],
            'aggregation': [re.compile(pattern, re.IGNORECASE) for pattern in self.AGGREGATION_PATTERNS],
            'time_range': [re.compile(pattern, re.IGNORECASE) for pattern in self.TIME_RANGE_PATTERNS],
        }
    
    def needs_database_query(self, query: str) -> bool:
        """
        Determine if query requires database access
        
        Args:
            query: User query string
            
        Returns:
            bool: True if query appears to reference database operations
        """
        query_lower = query.lower()
        
        # Check for explicit database keywords
        database_keywords = [
            'collection', 'database', 'table', 'query', 'aggregate',
            'filter', 'where', 'group by', 'count', 'sum', 'average',
            'find', 'search', 'retrieve', 'get data', 'analyze data'
        ]
        
        keyword_matches = sum(1 for keyword in database_keywords if keyword in query_lower)
        
        # Check for collection name patterns
        collection_matches = any(
            pattern.search(query) for pattern in self.compiled_patterns['collection']
        )
        
        # Higher confidence if multiple indicators present
        confidence = (keyword_matches / len(database_keywords)) + (1.0 if collection_matches else 0.0)
        
        logger.debug(f"Database query detection - Keywords: {keyword_matches}, Collections: {collection_matches}, Confidence: {confidence}")
        
        return confidence > 0.3  # Threshold for database query detection
    
    def extract_database_references(self, query: str) -> Optional[DatabaseReference]:
        """
        Extract database references from query
        
        Args:
            query: User query string
            
        Returns:
            DatabaseReference object if found, None otherwise
        """
        if not self.needs_database_query(query):
            return None
        
        db_ref = DatabaseReference()
        db_ref.filters = {}
        
        # Extract collection name
        collection_name, collection_confidence = self._extract_collection_name(query)
        if collection_name:
            db_ref.collection = collection_name
            db_ref.confidence += collection_confidence
        
        # Extract operation type
        operation_type = self._extract_operation_type(query)
        db_ref.operation_type = operation_type
        
        # Extract filters
        filters = self._extract_filters(query)
        if filters:
            db_ref.filters.update(filters)
            db_ref.confidence += 0.2
        
        # Extract aggregation fields
        aggregation_field = self._extract_aggregation_field(query)
        if aggregation_field and operation_type == "aggregate":
            db_ref.filters['group_by'] = aggregation_field
            db_ref.confidence += 0.2
        
        # Extract time ranges
        time_filters = self._extract_time_range(query)
        if time_filters:
            db_ref.filters.update(time_filters)
            db_ref.confidence += 0.1
        
        # Extract limit
        limit = self._extract_limit(query)
        if limit:
            db_ref.limit = limit
        
        # Only return if we have reasonable confidence
        if db_ref.confidence > 0.5 and db_ref.collection:
            logger.info(f"Extracted database reference: {db_ref}")
            return db_ref
        
        return None
    
    def _extract_collection_name(self, query: str) -> Tuple[Optional[str], float]:
        """Extract collection name from query"""
        confidence = 0.0
        
        # Try collection patterns
        for pattern in self.compiled_patterns['collection']:
            match = pattern.search(query)
            if match:
                collection_name = match.group(1)
                confidence = 0.8
                logger.debug(f"Found collection name via pattern: {collection_name}")
                return collection_name, confidence
        
        # Try filtered query patterns
        for pattern in self.compiled_patterns['filtered']:
            match = pattern.search(query)
            if match:
                collection_name = match.group(1)
                confidence = 0.7
                logger.debug(f"Found collection name via filtered pattern: {collection_name}")
                return collection_name, confidence
        
        # Try aggregation patterns
        for pattern in self.compiled_patterns['aggregation']:
            match = pattern.search(query)
            if match:
                collection_name = match.group(1)
                confidence = 0.7
                logger.debug(f"Found collection name via aggregation pattern: {collection_name}")
                return collection_name, confidence
        
        return None, confidence
    
    def _extract_operation_type(self, query: str) -> str:
        """Determine the type of database operation"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['aggregate', 'group', 'summarize', 'count', 'sum', 'average']):
            return "aggregate"
        elif any(word in query_lower for word in ['count', 'total number']):
            return "count"
        elif any(word in query_lower for word in ['distinct', 'unique']):
            return "distinct"
        else:
            return "query"
    
    def _extract_filters(self, query: str) -> Dict:
        """Extract filter conditions from query"""
        filters = {}
        
        for pattern in self.compiled_patterns['filtered']:
            match = pattern.search(query)
            if match and len(match.groups()) >= 3:
                field = match.group(2)
                value = match.group(3)
                
                # Try to convert to appropriate type
                try:
                    # Try integer
                    if value.isdigit():
                        filters[field] = int(value)
                    # Try float
                    elif '.' in value and value.replace('.', '').isdigit():
                        filters[field] = float(value)
                    # Try boolean
                    elif value.lower() in ['true', 'false']:
                        filters[field] = value.lower() == 'true'
                    else:
                        # Keep as string
                        filters[field] = value
                        
                    logger.debug(f"Extracted filter: {field} = {filters[field]}")
                except ValueError:
                    filters[field] = value
        
        return filters
    
    def _extract_aggregation_field(self, query: str) -> Optional[str]:
        """Extract field for aggregation operations"""
        for pattern in self.compiled_patterns['aggregation']:
            match = pattern.search(query)
            if match and len(match.groups()) >= 2:
                group_field = match.group(2)
                logger.debug(f"Extracted aggregation field: {group_field}")
                return group_field
        return None
    
    def _extract_time_range(self, query: str) -> Dict:
        """Extract time range filters from query"""
        time_filters = {}
        
        for pattern in self.compiled_patterns['time_range']:
            match = pattern.search(query)
            if match:
                groups = match.groups()
                
                if len(groups) == 2:  # last/past N days/weeks/months/years
                    amount = int(groups[0])
                    unit = groups[1]
                    
                    # Convert to MongoDB date filter
                    from datetime import datetime, timedelta
                    
                    if unit.startswith('day'):
                        delta = timedelta(days=amount)
                    elif unit.startswith('week'):
                        delta = timedelta(weeks=amount)
                    elif unit.startswith('month'):
                        delta = timedelta(days=amount * 30)  # Approximate
                    elif unit.startswith('year'):
                        delta = timedelta(days=amount * 365)  # Approximate
                    else:
                        continue
                    
                    start_date = datetime.now() - delta
                    time_filters['created_at'] = {'$gte': start_date}
                    logger.debug(f"Extracted time range: last {amount} {unit}s")
                
                elif len(groups) == 1:  # specific date
                    date_str = groups[0]
                    try:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                        if 'since' in query.lower() or 'after' in query.lower():
                            time_filters['created_at'] = {'$gte': date_obj}
                        elif 'before' in query.lower():
                            time_filters['created_at'] = {'$lt': date_obj}
                        logger.debug(f"Extracted date filter: {date_str}")
                    except ValueError:
                        continue
                
                elif len(groups) == 2 and 'between' in query.lower():  # date range
                    try:
                        start_date = datetime.strptime(groups[0], '%Y-%m-%d')
                        end_date = datetime.strptime(groups[1], '%Y-%m-%d')
                        time_filters['created_at'] = {'$gte': start_date, '$lte': end_date}
                        logger.debug(f"Extracted date range: {groups[0]} to {groups[1]}")
                    except ValueError:
                        continue
        
        return time_filters
    
    def _extract_limit(self, query: str) -> int:
        """Extract result limit from query"""
        limit_patterns = [
            r"limit\s+(\d+)",
            r"top\s+(\d+)",
            r"first\s+(\d+)",
            r"(\d+)\s+records?",
            r"(\d+)\s+results?",
        ]
        
        for pattern in limit_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                limit = int(match.group(1))
                logger.debug(f"Extracted limit: {limit}")
                return min(limit, 10000)  # Cap at 10k for safety
        
        return 1000  # Default limit
    
    def get_suggested_collections(self, query: str) -> List[str]:
        """
        Suggest collection names based on query context
        
        Args:
            query: User query string
            
        Returns:
            List of suggested collection names
        """
        suggestions = []
        query_lower = query.lower()
        
        # Common collection name patterns based on query content
        collection_hints = {
            'user': ['users', 'user_profiles', 'accounts', 'customers'],
            'order': ['orders', 'purchases', 'transactions', 'sales'],
            'product': ['products', 'items', 'inventory', 'catalog'],
            'log': ['logs', 'events', 'activities', 'audit_log'],
            'message': ['messages', 'emails', 'notifications', 'communications'],
            'payment': ['payments', 'billing', 'invoices', 'financial'],
            'review': ['reviews', 'ratings', 'feedback', 'comments'],
            'session': ['sessions', 'visits', 'analytics', 'tracking'],
        }
        
        for keyword, collections in collection_hints.items():
            if keyword in query_lower:
                suggestions.extend(collections)
        
        return list(set(suggestions))  # Remove duplicates
