"""
Schema Manager for MongoDB Collections

Handles schema discovery, metadata operations, and data profiling
for enhanced database analysis capabilities.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from collections import defaultdict, Counter
from datetime import datetime

logger = logging.getLogger(__name__)

class SchemaManager:
    """
    Manages MongoDB collection schema discovery and metadata operations
    
    Provides intelligent schema inference, data profiling, and optimization
    suggestions for better query performance and analysis.
    """
    
    def __init__(self, db_client):
        """
        Initialize schema manager
        
        Args:
            db_client: DatabaseQueryProcessor instance
        """
        self.db_client = db_client
        self._schema_cache = {}
        self._stats_cache = {}
    
    async def discover_collection_schema(self, 
                                       collection: str,
                                       database: Optional[str] = None,
                                       sample_size: int = 100) -> Dict[str, Any]:
        """
        Discover and analyze collection schema
        
        Args:
            collection: Collection name
            database: Database name
            sample_size: Number of documents to sample for schema analysis
            
        Returns:
            Comprehensive schema information
        """
        cache_key = f"{database or self.db_client.database_name}.{collection}"
        
        # Check cache first
        if cache_key in self._schema_cache:
            logger.debug(f"Returning cached schema for {cache_key}")
            return self._schema_cache[cache_key]
        
        try:
            # Get sample documents
            sample_data = await self.db_client.get_collection_sample(
                collection=collection,
                database=database,
                sample_size=sample_size
            )
            
            documents = json.loads(sample_data).get("documents", [])
            
            if not documents:
                return {"error": "No documents found in collection", "collection": collection}
            
            # Analyze schema
            schema_info = {
                "collection": collection,
                "database": database or self.db_client.database_name,
                "sample_size": len(documents),
                "fields": self._analyze_fields(documents),
                "document_structure": self._analyze_document_structure(documents),
                "data_types": self._analyze_data_types(documents),
                "field_statistics": self._analyze_field_statistics(documents),
                "indexes_suggested": self._suggest_indexes(documents),
                "analysis_recommendations": self._generate_analysis_recommendations(documents),
                "discovered_at": datetime.now().isoformat()
            }
            
            # Cache the result
            self._schema_cache[cache_key] = schema_info
            
            logger.info(f"Schema discovered for {cache_key}: {len(schema_info['fields'])} fields")
            return schema_info
            
        except Exception as e:
            logger.error(f"Failed to discover schema for {collection}: {e}")
            return {"error": str(e), "collection": collection}
    
    def _analyze_fields(self, documents: List[Dict]) -> Dict[str, Dict]:
        """Analyze field presence and characteristics"""
        field_info = defaultdict(lambda: {
            "count": 0,
            "presence_ratio": 0.0,
            "types": set(),
            "sample_values": [],
            "is_nested": False,
            "is_array": False,
            "null_count": 0
        })
        
        total_docs = len(documents)
        
        for doc in documents:
            self._traverse_document(doc, field_info, "", total_docs)
        
        # Convert sets to lists and calculate ratios
        for field_name, info in field_info.items():
            info["types"] = list(info["types"])
            info["presence_ratio"] = info["count"] / total_docs
            info["null_ratio"] = info["null_count"] / total_docs
            
            # Keep only a few sample values
            if len(info["sample_values"]) > 5:
                info["sample_values"] = info["sample_values"][:5]
        
        return dict(field_info)
    
    def _traverse_document(self, obj: Any, field_info: Dict, prefix: str, total_docs: int):
        """Recursively traverse document structure"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                field_path = f"{prefix}.{key}" if prefix else key
                
                # Update field info
                field_info[field_path]["count"] += 1
                
                if value is None:
                    field_info[field_path]["null_count"] += 1
                    field_info[field_path]["types"].add("null")
                else:
                    value_type = type(value).__name__
                    field_info[field_path]["types"].add(value_type)
                    
                    # Store sample values
                    if len(field_info[field_path]["sample_values"]) < 10:
                        if isinstance(value, (str, int, float, bool)):
                            field_info[field_path]["sample_values"].append(value)
                    
                    # Check for nested structures
                    if isinstance(value, dict):
                        field_info[field_path]["is_nested"] = True
                        self._traverse_document(value, field_info, field_path, total_docs)
                    elif isinstance(value, list):
                        field_info[field_path]["is_array"] = True
                        if value and isinstance(value[0], (dict, list)):
                            field_info[field_path]["is_nested"] = True
                            for item in value[:3]:  # Analyze first few items
                                self._traverse_document(item, field_info, field_path, total_docs)
        
        elif isinstance(obj, list):
            for item in obj[:5]:  # Limit analysis to first few items
                self._traverse_document(item, field_info, prefix, total_docs)
    
    def _analyze_document_structure(self, documents: List[Dict]) -> Dict[str, Any]:
        """Analyze overall document structure patterns"""
        structures = {
            "average_fields": 0,
            "max_fields": 0,
            "min_fields": float('inf'),
            "nested_levels": [],
            "array_fields": [],
            "common_patterns": []
        }
        
        total_fields = 0
        
        for doc in documents:
            field_count = self._count_fields(doc)
            total_fields += field_count
            
            structures["max_fields"] = max(structures["max_fields"], field_count)
            structures["min_fields"] = min(structures["min_fields"], field_count)
            
            # Analyze nesting depth
            max_depth = self._get_max_depth(doc)
            structures["nested_levels"].append(max_depth)
        
        structures["average_fields"] = total_fields / len(documents)
        structures["average_nesting_depth"] = sum(structures["nested_levels"]) / len(structures["nested_levels"])
        
        if structures["min_fields"] == float('inf'):
            structures["min_fields"] = 0
        
        return structures
    
    def _count_fields(self, obj: Any, prefix: str = "") -> int:
        """Count total fields in a document including nested"""
        if isinstance(obj, dict):
            count = len(obj)
            for value in obj.values():
                if isinstance(value, (dict, list)):
                    count += self._count_fields(value, prefix)
            return count
        elif isinstance(obj, list) and obj:
            return self._count_fields(obj[0], prefix)
        return 0
    
    def _get_max_depth(self, obj: Any, current_depth: int = 0) -> int:
        """Get maximum nesting depth of a document"""
        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(self._get_max_depth(value, current_depth + 1) for value in obj.values())
        elif isinstance(obj, list) and obj:
            return max(self._get_max_depth(item, current_depth) for item in obj[:3])
        return current_depth
    
    def _analyze_data_types(self, documents: List[Dict]) -> Dict[str, Any]:
        """Analyze data type distribution and patterns"""
        type_analysis = {
            "primary_types": Counter(),
            "type_consistency": {},
            "date_fields": [],
            "numeric_fields": [],
            "text_fields": [],
            "boolean_fields": [],
            "id_fields": [],
            "enum_candidates": {}
        }
        
        # Collect all field paths and their types
        all_field_types = defaultdict(Counter)
        
        for doc in documents:
            self._collect_field_types(doc, all_field_types, "")
        
        # Analyze type consistency and categorize fields
        for field_path, type_counter in all_field_types.items():
            total_occurrences = sum(type_counter.values())
            most_common_type = type_counter.most_common(1)[0]
            
            # Type consistency (what percentage of values are the most common type)
            consistency = most_common_type[1] / total_occurrences
            type_analysis["type_consistency"][field_path] = {
                "primary_type": most_common_type[0],
                "consistency": consistency,
                "type_distribution": dict(type_counter)
            }
            
            # Categorize fields by type
            primary_type = most_common_type[0]
            type_analysis["primary_types"][primary_type] += 1
            
            if primary_type in ["int", "float"]:
                type_analysis["numeric_fields"].append(field_path)
            elif primary_type == "str":
                type_analysis["text_fields"].append(field_path)
                
                # Check if it could be an enum (limited unique values)
                sample_values = [doc.get(field_path.split('.')[0]) for doc in documents[:20]]
                unique_values = set(v for v in sample_values if v is not None)
                if len(unique_values) <= 10 and len(unique_values) > 1:
                    type_analysis["enum_candidates"][field_path] = list(unique_values)
                    
            elif primary_type == "bool":
                type_analysis["boolean_fields"].append(field_path)
            
            # Check for ID fields
            if "_id" in field_path.lower() or field_path.lower().endswith("id"):
                type_analysis["id_fields"].append(field_path)
            
            # Check for date fields (basic heuristic)
            if any(date_keyword in field_path.lower() for date_keyword in ["date", "time", "created", "updated", "timestamp"]):
                type_analysis["date_fields"].append(field_path)
        
        return type_analysis
    
    def _collect_field_types(self, obj: Any, type_counter: Dict, prefix: str):
        """Collect field types recursively"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                field_path = f"{prefix}.{key}" if prefix else key
                
                if value is not None:
                    type_counter[field_path][type(value).__name__] += 1
                    
                    if isinstance(value, dict):
                        self._collect_field_types(value, type_counter, field_path)
                    elif isinstance(value, list) and value:
                        # Analyze first item in array
                        self._collect_field_types(value[0], type_counter, field_path)
    
    def _analyze_field_statistics(self, documents: List[Dict]) -> Dict[str, Any]:
        """Generate statistical analysis of fields"""
        stats = {
            "field_coverage": {},
            "cardinality_estimates": {},
            "value_distributions": {},
            "outlier_candidates": []
        }
        
        # Analyze each field's coverage and cardinality
        field_values = defaultdict(list)
        
        for doc in documents:
            self._collect_field_values(doc, field_values, "")
        
        for field_path, values in field_values.items():
            # Remove None values for analysis
            clean_values = [v for v in values if v is not None]
            
            if not clean_values:
                continue
            
            stats["field_coverage"][field_path] = len(clean_values) / len(documents)
            stats["cardinality_estimates"][field_path] = len(set(clean_values))
            
            # Basic value distribution analysis
            if isinstance(clean_values[0], (int, float)):
                stats["value_distributions"][field_path] = {
                    "min": min(clean_values),
                    "max": max(clean_values),
                    "avg": sum(clean_values) / len(clean_values),
                    "type": "numeric"
                }
            elif isinstance(clean_values[0], str):
                value_counter = Counter(clean_values)
                stats["value_distributions"][field_path] = {
                    "unique_count": len(value_counter),
                    "most_common": value_counter.most_common(3),
                    "avg_length": sum(len(str(v)) for v in clean_values) / len(clean_values),
                    "type": "text"
                }
        
        return stats
    
    def _collect_field_values(self, obj: Any, field_values: Dict, prefix: str):
        """Collect field values for statistical analysis"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                field_path = f"{prefix}.{key}" if prefix else key
                
                if isinstance(value, (str, int, float, bool)):
                    field_values[field_path].append(value)
                elif isinstance(value, dict):
                    self._collect_field_values(value, field_values, field_path)
                elif isinstance(value, list) and value:
                    # For arrays, collect the first item or array length
                    if isinstance(value[0], (str, int, float, bool)):
                        field_values[f"{field_path}.array_items"].extend(value[:10])
                    field_values[f"{field_path}.array_length"].append(len(value))
    
    def _suggest_indexes(self, documents: List[Dict]) -> List[Dict[str, Any]]:
        """Suggest database indexes based on schema analysis"""
        suggestions = []
        
        # Analyze field usage patterns to suggest indexes
        field_info = self._analyze_fields(documents)
        
        for field_path, info in field_info.items():
            # Skip deeply nested fields for index suggestions
            if field_path.count('.') > 2:
                continue
            
            suggestion = {
                "field": field_path,
                "reason": [],
                "priority": "low",
                "index_type": "single"
            }
            
            # High cardinality fields are good index candidates
            if len(info["sample_values"]) > 0:
                unique_ratio = len(set(info["sample_values"])) / len(info["sample_values"])
                if unique_ratio > 0.8:
                    suggestion["reason"].append("High cardinality field")
                    suggestion["priority"] = "medium"
            
            # ID fields should definitely have indexes
            if "_id" in field_path.lower() or field_path.lower().endswith("id"):
                suggestion["reason"].append("ID field")
                suggestion["priority"] = "high"
            
            # Date fields are often queried
            if any(date_keyword in field_path.lower() for date_keyword in ["date", "time", "created", "updated"]):
                suggestion["reason"].append("Date/time field - often used in range queries")
                suggestion["priority"] = "medium"
            
            # Fields with good presence ratio
            if info["presence_ratio"] > 0.8:
                suggestion["reason"].append("High presence ratio")
                if suggestion["priority"] == "low":
                    suggestion["priority"] = "medium"
            
            # Only suggest if we have reasons
            if suggestion["reason"]:
                suggestions.append(suggestion)
        
        # Sort by priority
        priority_order = {"high": 3, "medium": 2, "low": 1}
        suggestions.sort(key=lambda x: priority_order[x["priority"]], reverse=True)
        
        return suggestions[:10]  # Limit to top 10 suggestions
    
    def _generate_analysis_recommendations(self, documents: List[Dict]) -> List[str]:
        """Generate recommendations for data analysis"""
        recommendations = []
        
        field_info = self._analyze_fields(documents)
        type_analysis = self._analyze_data_types(documents)
        
        # Recommend based on field types
        if type_analysis["numeric_fields"]:
            recommendations.append(f"Consider statistical analysis on numeric fields: {', '.join(type_analysis['numeric_fields'][:3])}")
        
        if type_analysis["date_fields"]:
            recommendations.append(f"Time series analysis possible with date fields: {', '.join(type_analysis['date_fields'][:3])}")
        
        if type_analysis["enum_candidates"]:
            enum_fields = list(type_analysis["enum_candidates"].keys())[:2]
            recommendations.append(f"Categorical analysis recommended for: {', '.join(enum_fields)}")
        
        # Recommend based on field patterns
        high_cardinality_fields = [
            field for field, info in field_info.items() 
            if len(set(info["sample_values"])) / max(len(info["sample_values"]), 1) > 0.8
        ]
        
        if high_cardinality_fields:
            recommendations.append(f"Unique value analysis for high-cardinality fields: {', '.join(high_cardinality_fields[:2])}")
        
        # Missing data analysis
        sparse_fields = [
            field for field, info in field_info.items()
            if info["presence_ratio"] < 0.7
        ]
        
        if sparse_fields:
            recommendations.append(f"Missing data analysis recommended for sparse fields: {', '.join(sparse_fields[:2])}")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    async def get_collection_stats(self, 
                                 collection: str,
                                 database: Optional[str] = None) -> Dict[str, Any]:
        """
        Get collection statistics and metadata
        
        Args:
            collection: Collection name
            database: Database name
            
        Returns:
            Collection statistics
        """
        cache_key = f"{database or self.db_client.database_name}.{collection}.stats"
        
        # Check cache
        if cache_key in self._stats_cache:
            return self._stats_cache[cache_key]
        
        try:
            # Get document count
            doc_count = await self.db_client.count_documents(collection, database=database)
            
            # Get schema info
            schema_info = await self.discover_collection_schema(collection, database)
            
            stats = {
                "collection": collection,
                "database": database or self.db_client.database_name,
                "document_count": doc_count,
                "field_count": len(schema_info.get("fields", {})),
                "schema_discovered": bool(schema_info.get("fields")),
                "has_nested_fields": any(
                    info.get("is_nested", False) 
                    for info in schema_info.get("fields", {}).values()
                ),
                "has_arrays": any(
                    info.get("is_array", False) 
                    for info in schema_info.get("fields", {}).values()
                ),
                "analysis_recommendations": schema_info.get("analysis_recommendations", []),
                "updated_at": datetime.now().isoformat()
            }
            
            # Cache stats
            self._stats_cache[cache_key] = stats
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get stats for {collection}: {e}")
            return {"error": str(e), "collection": collection}
    
    def clear_cache(self):
        """Clear schema and stats cache"""
        self._schema_cache.clear()
        self._stats_cache.clear()
        logger.info("Schema and stats cache cleared")
    
    def get_cached_schemas(self) -> List[str]:
        """Get list of cached schema keys"""
        return list(self._schema_cache.keys())
